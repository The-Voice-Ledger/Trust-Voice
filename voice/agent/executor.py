"""
TrustVoice Agent — Executor

The AI Agent loop that uses OpenAI function-calling to orchestrate
voice commands across every TrustVoice capability.

Architecture:
    1. Load conversation history from Redis
    2. Build messages = system_prompt + history + user_message
    3. Call GPT with tools (max N turns)
    4. On tool_calls  → execute via _execute_tool → append result → loop
    5. On text        → return as agent response
    6. Save updated history to Redis

Design decisions:
    • READ tools (search, details, history) → direct DB queries for speed
    • WRITE tools (donate, create, withdraw) → delegate to existing handlers
      to reuse all business logic, payment integration, and validation
    • Conversation history stored separately from session_manager to avoid
      conflicts with the old pipeline
    • Graceful fallback: if the agent errors, callers can fall back to
      the NLU → command_router pipeline
"""

import os
import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from database.models import (
    Campaign, Donation, Donor, User,
    NGOOrganization, PendingNGORegistration,
)
from voice.agent.tools import AGENT_TOOLS

logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────
AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-4o-mini")
AGENT_MAX_TURNS = int(os.getenv("AGENT_MAX_TURNS", "6"))
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.2"))
AGENT_HISTORY_TTL = int(os.getenv("AGENT_HISTORY_TTL", "1800"))  # 30 min
AGENT_MAX_HISTORY = 30  # max messages to keep per conversation

# Redis key prefix — separate from session_manager's "session:" keys
AGENT_KEY_PREFIX = "agent_conv"


# ── Redis helpers (graceful when Redis is unavailable) ──────────
def _redis():
    """Lazy import redis_client so the module loads even if Redis is down."""
    try:
        from voice.session_manager import redis_client
        return redis_client
    except Exception:
        return None


def _get_history(user_id: str, conversation_id: str) -> List[Dict]:
    """Load conversation history from Redis."""
    r = _redis()
    if not r:
        return []
    try:
        key = f"{AGENT_KEY_PREFIX}:{user_id}:{conversation_id}"
        raw = r.get(key)
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning(f"Failed to load agent history: {e}")
    return []


def _save_history(
    user_id: str, conversation_id: str, messages: List[Dict]
):
    """Persist conversation history to Redis (trimmed)."""
    r = _redis()
    if not r:
        return
    try:
        key = f"{AGENT_KEY_PREFIX}:{user_id}:{conversation_id}"
        # Keep only the most recent messages to bound context size
        trimmed = messages[-AGENT_MAX_HISTORY:]
        r.setex(key, AGENT_HISTORY_TTL, json.dumps(trimmed, default=str))
    except Exception as e:
        logger.warning(f"Failed to save agent history: {e}")


# ── User lookup helper ──────────────────────────────────────────
def _get_user(user_id: str, db: Session) -> Optional[User]:
    """Resolve a user from UUID string or telegram_user_id."""
    try:
        uid = uuid.UUID(user_id)
        return db.query(User).filter(User.id == uid).first()
    except (ValueError, AttributeError):
        return db.query(User).filter(
            User.telegram_user_id == str(user_id)
        ).first()


# ── System prompt builder ───────────────────────────────────────
def _build_system_prompt(
    user_id: str,
    db: Session,
    language: str = "en",
    context: Optional[Dict] = None,
) -> str:
    user = _get_user(user_id, db)
    user_role = (user.role if user else "guest") or "DONOR"
    user_name = (user.full_name if user else "") or "Anonymous"

    lang_map = {"en": "English", "am": "Amharic (አማርኛ)"}
    lang_name = lang_map.get(language, "English")

    if language == "am":
        lang_instruction = (
            "The user speaks Amharic. Respond in Amharic (አማርኛ). "
            "Use English for tool parameter values."
        )
    else:
        lang_instruction = "Respond in English."

    ctx_note = ""
    if context:
        if context.get("page"):
            ctx_note += f"\nUser is on the '{context['page']}' page."
        if context.get("selected_campaign"):
            sc = context["selected_campaign"]
            ctx_note += (
                f"\nViewing campaign: '{sc.get('title', '?')}' "
                f"(ID: {sc.get('id')})."
            )

    return (
        "You are TrustVoice Assistant — a helpful AI for a voice-first "
        "donation platform connecting donors with verified NGO campaigns "
        "across Africa.\n\n"
        f"USER: {user_name}  |  ROLE: {user_role}  |  LANG: {lang_name}\n"
        f"{lang_instruction}\n"
        "\nRULES:\n"
        "1. Be concise — responses are read aloud via TTS. "
        "Aim for 1-3 short sentences.\n"
        "2. Use tools for ALL data and actions — never fabricate numbers.\n"
        "3. For compound requests (\"find campaigns and donate\"), "
        "handle them step-by-step with multiple tool calls.\n"
        "4. ALWAYS confirm before write actions "
        "(donations, campaign creation, withdrawals).\n"
        "5. When listing campaigns, always include the campaign ID.\n"
        "6. If information is missing, ask — don't guess.\n"
        f"{ctx_note}"
    )


# ── Agent Executor ──────────────────────────────────────────────
class AgentExecutor:
    """
    Runs the TrustVoice AI Agent loop.

    Usage:
        agent = AgentExecutor()
        result = await agent.run("find education campaigns", user_id, db)
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = AGENT_MODEL
        self.max_turns = AGENT_MAX_TURNS
        self.temperature = AGENT_TEMPERATURE

    # ── Public API ──────────────────────────────────────────────
    async def run(
        self,
        user_message: str,
        user_id: str,
        db: Session,
        language: str = "en",
        conversation_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Run the agent on a user message (text already transcribed).

        Returns:
            {
                "conversation_id": str,
                "response_text": str,
                "data": dict,       # structured data from tools
                "tools_used": [str],
            }
        """
        conv_id = conversation_id or str(uuid.uuid4())
        history = _get_history(user_id, conv_id)

        system_prompt = _build_system_prompt(user_id, db, language, context)
        messages: List[Dict] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        collected_data: Dict[str, Any] = {}
        tools_used: List[str] = []
        final_text = ""

        try:
            for _turn in range(self.max_turns):
                resp = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=AGENT_TOOLS,
                    tool_choice="auto",
                    temperature=self.temperature,
                )

                choice = resp.choices[0]
                msg = choice.message

                # Serialize assistant message for the conversation
                assistant_dict: Dict[str, Any] = {
                    "role": "assistant",
                    "content": msg.content,
                }
                if msg.tool_calls:
                    assistant_dict["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                messages.append(assistant_dict)

                # No tool calls → agent is done
                if not msg.tool_calls:
                    final_text = msg.content or ""
                    break

                # Execute each tool call
                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    logger.info(f"🤖 Agent tool: {tool_name}({tool_args})")
                    tools_used.append(tool_name)

                    try:
                        result = await self._execute_tool(
                            tool_name, tool_args, user_id, db
                        )
                    except Exception as exc:
                        logger.error(f"Tool {tool_name} error: {exc}")
                        result = {"error": str(exc)}

                    # Collect structured data for frontend
                    if isinstance(result, dict):
                        for key in (
                            "campaigns", "campaign", "donation",
                            "donations", "stats", "success",
                        ):
                            if key in result:
                                collected_data[key] = result[key]

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, default=str),
                    })
            else:
                # Exhausted all turns
                if not final_text:
                    final_text = (
                        "I've completed the actions. "
                        "Is there anything else you need?"
                    )

        except Exception as exc:
            logger.error(f"Agent execution error: {exc}", exc_info=True)
            raise  # Let callers handle fallback

        # Save history (everything except system prompt)
        _save_history(user_id, conv_id, messages[1:])

        return {
            "conversation_id": conv_id,
            "response_text": final_text,
            "data": collected_data,
            "tools_used": tools_used,
        }

    # ── Tool Dispatch ───────────────────────────────────────────
    async def _execute_tool(
        self, name: str, args: Dict, user_id: str, db: Session
    ) -> Dict:
        dispatch = {
            "search_campaigns": self._tool_search_campaigns,
            "get_campaign_details": self._tool_get_campaign_details,
            "make_donation": self._tool_make_donation,
            "check_donation_status": self._tool_check_donation_status,
            "view_donation_history": self._tool_view_donation_history,
            "create_campaign": self._tool_create_campaign,
            "register_ngo": self._tool_register_ngo,
            "view_my_campaigns": self._tool_view_my_campaigns,
            "submit_field_report": self._tool_submit_field_report,
            "withdraw_funds": self._tool_withdraw_funds,
            "get_platform_stats": self._tool_get_platform_stats,
            "change_language": self._tool_change_language,
            "get_help": self._tool_get_help,
        }
        handler = dispatch.get(name)
        if not handler:
            return {"error": f"Unknown tool: {name}"}
        return await handler(args, user_id, db)

    # ────────────────────────────────────────────────────────────
    #  READ tools — direct DB queries for speed
    # ────────────────────────────────────────────────────────────

    async def _tool_search_campaigns(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """Search active campaigns with optional filters."""
        query = db.query(Campaign).filter(Campaign.status == "active")

        if args.get("category"):
            query = query.filter(
                Campaign.category.ilike(f"%{args['category']}%")
            )
        if args.get("location"):
            loc = args["location"]
            query = query.filter(
                or_(
                    Campaign.location_region.ilike(f"%{loc}%"),
                    Campaign.location_country.ilike(f"%{loc}%"),
                    Campaign.description.ilike(f"%{loc}%"),
                )
            )
        if args.get("keyword"):
            kw = f"%{args['keyword']}%"
            query = query.filter(
                or_(Campaign.title.ilike(kw), Campaign.description.ilike(kw))
            )

        campaigns = query.order_by(Campaign.created_at.desc()).limit(10).all()

        return {
            "total_found": len(campaigns),
            "campaigns": [
                {
                    "id": c.id,
                    "title": c.title,
                    "category": c.category,
                    "goal_usd": float(c.goal_amount_usd or 0),
                    "raised_usd": float(c.raised_amount_usd or 0),
                    "progress_pct": int(
                        (float(c.raised_amount_usd or 0)
                         / max(float(c.goal_amount_usd or 1), 1))
                        * 100
                    ),
                    "location": (
                        c.location_region
                        or c.location_country
                        or "N/A"
                    ),
                    "description_preview": (c.description or "")[:120],
                }
                for c in campaigns
            ],
        }

    async def _tool_get_campaign_details(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """Get full details of a specific campaign."""
        campaign = (
            db.query(Campaign)
            .filter(Campaign.id == args["campaign_id"])
            .first()
        )
        if not campaign:
            return {"error": f"Campaign {args['campaign_id']} not found."}

        raised = float(campaign.raised_amount_usd or 0)
        goal = max(float(campaign.goal_amount_usd or 1), 1)

        return {
            "campaign": {
                "id": campaign.id,
                "title": campaign.title,
                "description": campaign.description,
                "category": campaign.category,
                "goal_usd": goal,
                "raised_usd": raised,
                "progress_pct": int((raised / goal) * 100),
                "status": campaign.status,
                "location": (
                    campaign.location_region
                    or campaign.location_country
                    or "N/A"
                ),
                "created_at": str(campaign.created_at),
            }
        }

    async def _tool_view_donation_history(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """View the user's past donations."""
        limit = min(args.get("limit", 5), 20)
        user = _get_user(user_id, db)
        if not user:
            return {"error": "User not found. Please register first."}

        donor = (
            db.query(Donor)
            .filter(Donor.telegram_user_id == user.telegram_user_id)
            .first()
        )
        if not donor:
            return {"donations": [], "message": "No donation history yet."}

        donations = (
            db.query(Donation)
            .filter(Donation.donor_id == donor.id)
            .order_by(Donation.created_at.desc())
            .limit(limit)
            .all()
        )

        items = []
        for d in donations:
            camp = (
                db.query(Campaign)
                .filter(Campaign.id == d.campaign_id)
                .first()
            )
            items.append({
                "id": str(d.id),
                "amount": float(d.amount),
                "currency": d.currency,
                "status": d.status,
                "campaign_title": camp.title if camp else "Unknown",
                "date": str(d.created_at),
            })

        return {"donations": items, "total_count": len(items)}

    async def _tool_view_my_campaigns(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """View campaigns owned by the current user."""
        user = _get_user(user_id, db)
        if not user:
            return {"error": "User not found."}

        ngo = (
            db.query(NGOOrganization)
            .filter(NGOOrganization.admin_user_id == user.id)
            .first()
        )
        if not ngo:
            return {
                "campaigns": [],
                "message": "No NGO linked to your account.",
            }

        campaigns = (
            db.query(Campaign).filter(Campaign.ngo_id == ngo.id).all()
        )
        return {
            "campaigns": [
                {
                    "id": c.id,
                    "title": c.title,
                    "status": c.status,
                    "goal_usd": float(c.goal_amount_usd or 0),
                    "raised_usd": float(c.raised_amount_usd or 0),
                    "progress_pct": int(
                        (float(c.raised_amount_usd or 0)
                         / max(float(c.goal_amount_usd or 1), 1))
                        * 100
                    ),
                }
                for c in campaigns
            ],
            "total_count": len(campaigns),
        }

    async def _tool_get_platform_stats(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """Platform-wide statistics."""
        active_campaigns = (
            db.query(func.count(Campaign.id))
            .filter(Campaign.status == "active")
            .scalar()
        ) or 0
        total_donations = db.query(func.count(Donation.id)).scalar() or 0
        total_raised = (
            db.query(func.sum(Donation.amount))
            .filter(Donation.status == "completed")
            .scalar()
        ) or 0
        total_donors = db.query(func.count(Donor.id)).scalar() or 0

        return {
            "stats": {
                "active_campaigns": active_campaigns,
                "total_donations": total_donations,
                "total_raised_usd": float(total_raised),
                "total_donors": total_donors,
            }
        }

    async def _tool_get_help(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """Return help info (the agent will rephrase for the user)."""
        user = _get_user(user_id, db)
        role = (user.role if user else "guest") or "guest"
        capabilities = [
            "Search campaigns by category, location, or keyword",
            "View campaign details",
            "Make a donation (M-Pesa or card)",
            "Check donation status",
            "View your donation history",
        ]
        if role in ("CAMPAIGN_CREATOR", "SYSTEM_ADMIN", "ngo_admin", "super_admin"):
            capabilities += [
                "Create a new campaign",
                "View your campaigns",
                "Withdraw funds",
            ]
        if role in ("FIELD_AGENT", "SYSTEM_ADMIN", "super_admin"):
            capabilities.append("Submit field impact report")
        capabilities += [
            "Get platform statistics",
            "Change language (English / Amharic)",
        ]
        return {"role": role, "capabilities": capabilities}

    # ────────────────────────────────────────────────────────────
    #  WRITE tools — delegate to existing handlers
    # ────────────────────────────────────────────────────────────

    async def _tool_make_donation(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """Initiate a donation (delegates to Lab 5 payment handler)."""
        from voice.handlers.donation_handler import initiate_voice_donation

        campaign = (
            db.query(Campaign)
            .filter(Campaign.id == args["campaign_id"])
            .first()
        )
        if not campaign:
            return {"error": f"Campaign {args['campaign_id']} not found."}
        if campaign.status != "active":
            return {
                "error": (
                    f"Campaign is not active (status: {campaign.status})."
                )
            }

        result = await initiate_voice_donation(
            db=db,
            telegram_user_id=user_id,
            campaign_id=campaign.id,
            amount=float(args["amount"]),
            currency=args.get("currency", "USD"),
            payment_method=args.get("payment_method"),
        )

        if result.get("success"):
            return {
                "success": True,
                "donation_id": str(result.get("donation_id", "")),
                "payment_method": result.get("payment_method"),
                "instructions": result.get("instructions", ""),
                "amount": args["amount"],
                "currency": args.get("currency", "USD"),
                "campaign_title": campaign.title,
            }
        return {"error": result.get("error", "Donation failed.")}

    async def _tool_check_donation_status(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """Check status of a donation."""
        from voice.handlers.donation_handler import get_donation_status

        donation_id = None
        if args.get("donation_id"):
            try:
                donation_id = uuid.UUID(args["donation_id"])
            except ValueError:
                return {"error": "Invalid donation ID format."}

        return await get_donation_status(db, user_id, donation_id)

    async def _tool_create_campaign(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """Create a campaign (delegates to existing handler)."""
        from voice.handlers.ngo_handlers import handle_create_campaign

        entities = {
            "title": args["title"],
            "description": args["description"],
            "goal_amount": args["goal_amount"],
            "category": args["category"],
            "location": args.get("location", ""),
        }
        return await handle_create_campaign(
            entities=entities, user_id=user_id, db=db, context={}
        )

    async def _tool_register_ngo(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """Register a new NGO (delegates to existing handler)."""
        from voice.handlers.ngo_handlers import handle_register_ngo

        entities = {
            "organization_name": args["name"],
            "description": args.get("description", ""),
            "website": args.get("website", ""),
            "country": args.get("country", ""),
        }
        return await handle_register_ngo(
            entities=entities, user_id=user_id, db=db, context={}
        )

    async def _tool_submit_field_report(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """Submit impact report (delegates to existing handler)."""
        from voice.handlers.ngo_handlers import handle_field_report

        entities = {
            "campaign_id": args["campaign_id"],
            "description": args["description"],
            "verification_status": args.get("verification_status", "verified"),
        }
        return await handle_field_report(
            entities=entities, user_id=user_id, db=db, context={}
        )

    async def _tool_withdraw_funds(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """Withdraw funds (delegates to existing handler)."""
        from voice.handlers.ngo_handlers import handle_withdraw_funds

        entities = {
            "campaign_id": args["campaign_id"],
        }
        if args.get("amount") is not None:
            entities["amount"] = args["amount"]
        return await handle_withdraw_funds(
            entities=entities, user_id=user_id, db=db, context={}
        )

    async def _tool_change_language(
        self, args: Dict, user_id: str, db: Session
    ) -> Dict:
        """Change language preference."""
        from voice.handlers.general_handlers import handle_change_language

        return await handle_change_language(
            entities={"language": args["language"]},
            user_id=user_id,
            db=db,
            context={},
        )

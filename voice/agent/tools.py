"""
TrustVoice Agent — Tool Definitions

OpenAI function-calling tool schemas for the TrustVoice AI Agent.
Each tool maps to an existing backend capability (handler or DB query).

Tool categories:
  Discovery   → search_campaigns, get_campaign_details
  Donation    → make_donation, check_donation_status, view_donation_history
  NGO/Campaign→ create_campaign, register_ngo, view_my_campaigns
  Field       → submit_field_report, withdraw_funds
  Platform    → get_platform_stats, change_language, get_help
"""

AGENT_TOOLS = [
    # ─── Discovery ──────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "search_campaigns",
            "description": (
                "Search for active fundraising campaigns. Use when the user "
                "wants to find, browse, list, or discover campaigns. "
                "Returns matching campaigns with title, progress, and location."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Campaign category to filter by",
                        "enum": [
                            "education", "health", "water", "environment",
                            "food", "shelter", "economic", "community",
                        ],
                    },
                    "location": {
                        "type": "string",
                        "description": (
                            "Location or region to filter by "
                            "(e.g. 'Kenya', 'Nairobi', 'Ethiopia')"
                        ),
                    },
                    "keyword": {
                        "type": "string",
                        "description": (
                            "Free-text keyword to search in campaign "
                            "titles and descriptions"
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_campaign_details",
            "description": (
                "Get full details of a specific campaign including goal, "
                "amount raised, description, location, and category."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "campaign_id": {
                        "type": "integer",
                        "description": "The campaign ID number",
                    },
                },
                "required": ["campaign_id"],
            },
        },
    },

    # ─── Donation ───────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "make_donation",
            "description": (
                "Initiate a donation to a specific campaign. "
                "ALWAYS confirm the amount and campaign with the user "
                "before calling this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "campaign_id": {
                        "type": "integer",
                        "description": "Campaign ID to donate to",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Donation amount",
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code",
                        "enum": ["USD", "KES", "ETB", "UGX", "TZS", "GBP", "EUR"],
                    },
                    "payment_method": {
                        "type": "string",
                        "description": "Payment method preference",
                        "enum": ["mpesa", "stripe"],
                    },
                },
                "required": ["campaign_id", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_donation_status",
            "description": (
                "Check the status of the user's most recent donation, "
                "or a specific donation by ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "donation_id": {
                        "type": "string",
                        "description": (
                            "Specific donation UUID to check. "
                            "If omitted, returns the most recent donation."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_donation_history",
            "description": (
                "View the user's past donations with amounts, "
                "campaign names, and dates."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of donations to return (default 5)",
                    },
                },
                "required": [],
            },
        },
    },

    # ─── NGO / Campaign Management ─────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_campaign",
            "description": (
                "Create a new fundraising campaign. "
                "Only available to NGO administrators and campaign creators."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Campaign title",
                    },
                    "description": {
                        "type": "string",
                        "description": "Campaign description explaining the cause",
                    },
                    "goal_amount": {
                        "type": "number",
                        "description": "Fundraising goal amount in USD",
                    },
                    "category": {
                        "type": "string",
                        "description": "Campaign category",
                        "enum": [
                            "education", "health", "water", "environment",
                            "food", "shelter", "economic", "community",
                        ],
                    },
                    "location": {
                        "type": "string",
                        "description": "Campaign location or region",
                    },
                },
                "required": ["title", "description", "goal_amount", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "register_ngo",
            "description": (
                "Register a new NGO organization on the platform. "
                "The registration will be reviewed by an admin."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "NGO organization name",
                    },
                    "description": {
                        "type": "string",
                        "description": "NGO description and mission statement",
                    },
                    "website": {
                        "type": "string",
                        "description": "NGO website URL (optional)",
                    },
                    "country": {
                        "type": "string",
                        "description": "Country where the NGO operates",
                    },
                },
                "required": ["name", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_my_campaigns",
            "description": (
                "View campaigns managed by the current user. "
                "For NGO admins and campaign creators only."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },

    # ─── Field Agent / Withdrawals ──────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "submit_field_report",
            "description": (
                "Submit an impact verification report for a campaign. "
                "Only available to field agents."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "campaign_id": {
                        "type": "integer",
                        "description": "Campaign ID to report on",
                    },
                    "description": {
                        "type": "string",
                        "description": "Field report describing observed impact",
                    },
                    "verification_status": {
                        "type": "string",
                        "description": "Verification result",
                        "enum": ["verified", "partial", "unverified"],
                    },
                },
                "required": ["campaign_id", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "withdraw_funds",
            "description": (
                "Request withdrawal of funds from a campaign. "
                "Only the campaign owner can withdraw."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "campaign_id": {
                        "type": "integer",
                        "description": "Campaign ID to withdraw from",
                    },
                    "amount": {
                        "type": "number",
                        "description": (
                            "Amount to withdraw in USD. "
                            "If omitted, withdraws the full available balance."
                        ),
                    },
                },
                "required": ["campaign_id"],
            },
        },
    },

    # ─── Platform / Utility ─────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_platform_stats",
            "description": (
                "Get platform-wide statistics: total donations, "
                "active campaigns, registered donors, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "change_language",
            "description": (
                "Change the user's preferred language for voice interactions. "
                "Supports English and Amharic."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Language to switch to",
                        "enum": ["en", "am"],
                    },
                },
                "required": ["language"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_help",
            "description": (
                "Get help information about available commands "
                "and platform features. Use when user says 'help', "
                "'what can you do', etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

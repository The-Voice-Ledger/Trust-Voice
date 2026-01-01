"""
Analytics API Router

Provides endpoints for conversation analytics dashboard:
- GET /api/analytics/conversation-metrics: Summary, trends, and funnel data
- GET /api/analytics/events: Recent conversation events

Used by: frontend-miniapps/conversation-analytics.html
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.db import get_db
from voice.conversation.analytics import ConversationAnalytics
from typing import Optional

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/conversation-metrics")
async def get_conversation_metrics(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze"),
    conversation_type: Optional[str] = Query(default=None, description="Filter by conversation type"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive conversation analytics
    
    Returns:
        - summary: Overall metrics (started, completed, abandoned, completion_rate)
        - daily_metrics: Day-by-day breakdown
        - donation_funnel: Step-by-step conversion rates
        - recent_events: Last 10 conversation events
    
    Query Parameters:
        - days: Number of days to analyze (1-365, default 7)
        - conversation_type: Filter by type (optional, e.g., "donating")
    
    Example Response:
    ```json
    {
        "summary": {
            "started": 150,
            "completed": 68,
            "abandoned": 82,
            "completion_rate": 45.3,
            "previous_period": {
                "started": 120,
                "completed": 50,
                "abandoned": 70,
                "completion_rate": 41.7
            }
        },
        "daily_metrics": [
            {
                "date": "2025-12-25",
                "type": "donating",
                "started": 25,
                "completed": 12,
                "abandoned": 13,
                "completion_rate": 48.0
            }
        ],
        "donation_funnel": {
            "campaign_selection": {"count": 150, "percentage": 100.0},
            "amount_entry": {"count": 120, "percentage": 80.0},
            "payment_method": {"count": 95, "percentage": 63.3},
            "confirmation": {"count": 75, "percentage": 50.0},
            "completed": {"count": 68, "percentage": 45.3}
        },
        "recent_events": [
            {
                "event_type": "conversation_started",
                "conversation_state": "donating",
                "current_step": null,
                "event_data": {},
                "created_at": "2025-12-31T10:15:30"
            }
        ]
    }
    ```
    """
    
    # Get summary metrics
    summary = ConversationAnalytics.get_summary_metrics(days, db)
    
    # Get daily breakdown
    daily_metrics = ConversationAnalytics.get_daily_metrics(days, db)
    
    # Get donation funnel (default to "donating" if not specified)
    funnel_type = conversation_type or "donating"
    donation_funnel = ConversationAnalytics.get_funnel_metrics(funnel_type, days, db)
    
    # Get recent events
    recent_events = ConversationAnalytics.get_recent_events(limit=10, db=db)
    
    return {
        "summary": summary,
        "daily_metrics": daily_metrics,
        "donation_funnel": donation_funnel,
        "recent_events": recent_events,
        "period": {
            "days": days,
            "conversation_type": funnel_type
        }
    }


@router.get("/events")
async def get_recent_events(
    limit: int = Query(default=20, ge=1, le=100, description="Number of events to return"),
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    db: Session = Depends(get_db)
):
    """
    Get recent conversation events
    
    Query Parameters:
        - limit: Number of events to return (1-100, default 20)
        - event_type: Filter by specific event type (optional)
    
    Returns:
        List of recent conversation events with details
    
    Example Response:
    ```json
    {
        "events": [
            {
                "event_type": "step_completed",
                "conversation_state": "donating",
                "current_step": "enter_amount",
                "event_data": {"amount": 500},
                "created_at": "2025-12-31T10:30:45"
            }
        ],
        "total": 1
    }
    ```
    """
    
    events = ConversationAnalytics.get_recent_events(limit, db)
    
    # Filter by event type if specified
    if event_type:
        events = [e for e in events if e["event_type"] == event_type]
    
    return {
        "events": events,
        "total": len(events),
        "limit": limit,
        "filter": {"event_type": event_type} if event_type else None
    }


@router.get("/funnel")
async def get_funnel_analysis(
    conversation_type: str = Query(default="donating", description="Type of conversation to analyze"),
    days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get detailed funnel analysis for specific conversation type
    
    Query Parameters:
        - conversation_type: Type of conversation (default "donating")
        - days: Number of days to analyze (1-365, default 7)
    
    Returns:
        Detailed funnel metrics with drop-off analysis
    
    Example Response:
    ```json
    {
        "conversation_type": "donating",
        "period_days": 7,
        "funnel": {
            "campaign_selection": {
                "count": 150,
                "percentage": 100.0,
                "drop_off": 0.0
            },
            "amount_entry": {
                "count": 120,
                "percentage": 80.0,
                "drop_off": 20.0
            }
        },
        "total_started": 150,
        "total_completed": 68,
        "overall_conversion": 45.3
    }
    ```
    """
    
    funnel = ConversationAnalytics.get_funnel_metrics(conversation_type, days, db)
    
    # Calculate drop-offs
    steps = list(funnel.items())
    for i in range(1, len(steps)):
        prev_percentage = steps[i-1][1]["percentage"]
        curr_percentage = steps[i][1]["percentage"]
        steps[i][1]["drop_off"] = round(prev_percentage - curr_percentage, 1)
    
    # Set first step drop-off to 0
    if steps:
        steps[0][1]["drop_off"] = 0.0
    
    # Rebuild funnel dict
    enriched_funnel = {step: data for step, data in steps}
    
    # Calculate totals
    total_started = steps[0][1]["count"] if steps else 0
    total_completed = steps[-1][1]["count"] if steps else 0
    overall_conversion = (total_completed / total_started * 100) if total_started > 0 else 0
    
    return {
        "conversation_type": conversation_type,
        "period_days": days,
        "funnel": enriched_funnel,
        "total_started": total_started,
        "total_completed": total_completed,
        "overall_conversion": round(overall_conversion, 1)
    }


@router.get("/summary")
async def get_summary(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get quick summary metrics
    
    Query Parameters:
        - days: Number of days to analyze (1-365, default 7)
    
    Returns:
        High-level summary statistics
    
    Example Response:
    ```json
    {
        "started": 150,
        "completed": 68,
        "abandoned": 82,
        "completion_rate": 45.3,
        "previous_period": {
            "started": 120,
            "completion_rate": 41.7
        }
    }
    ```
    """
    
    return ConversationAnalytics.get_summary_metrics(days, db)

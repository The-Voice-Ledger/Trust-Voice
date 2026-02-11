"""
Conversation Analytics Tracking

Track conversation events, calculate metrics, and provide funnel analysis
for conversation performance optimization.

Event Types:
    - conversation_started: User begins a conversation flow
    - step_completed: User completes a step in multi-turn flow
    - clarification_requested: Bot asks for clarification
    - context_switched: User switches conversation context
    - conversation_completed: Conversation successfully finished
    - conversation_abandoned: User abandons conversation
    - error_occurred: Error during conversation

Usage:
    # Track event
    ConversationAnalytics.track_event(
        user_id="123",
        session_id="abc-def",
        event_type="conversation_started",
        conversation_state="donating",
        db=db
    )
    
    # Get funnel metrics
    funnel = ConversationAnalytics.get_funnel_metrics("donating", days=7, db=db)
"""

from datetime import datetime, date, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from database.models import ConversationEvent, ConversationMetrics, User
import uuid


class ConversationAnalytics:
    """Track and analyze conversation performance"""
    
    # Valid event types
    EVENT_TYPES = [
        "conversation_started",
        "step_completed",
        "clarification_requested",
        "context_switched",
        "conversation_completed",
        "conversation_abandoned",
        "error_occurred"
    ]
    
    @staticmethod
    def track_event(
        user_id: str,
        session_id: str,
        event_type: str,
        conversation_state: Optional[str] = None,
        current_step: Optional[str] = None,
        event_data: Optional[dict] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Track a conversation event
        
        Args:
            user_id: Telegram user ID
            session_id: Unique session identifier
            event_type: Type of event (see EVENT_TYPES)
            conversation_state: Current conversation state (e.g., "donating", "searching")
            current_step: Current step in multi-turn flow
            event_data: Additional event metadata
            db: Database session
            
        Returns:
            True if event tracked successfully
        """
        if not db:
            return False
        
        if event_type not in ConversationAnalytics.EVENT_TYPES:
            print(f"⚠️  Unknown event type: {event_type}")
            return False
        
        try:
            # Get user from database
            user = db.query(User).filter(User.telegram_user_id == user_id).first()
            
            # Create event
            event = ConversationEvent(
                user_id=user.id if user else None,
                session_id=session_id,
                event_type=event_type,
                conversation_state=conversation_state,
                current_step=current_step,
                event_data=event_data or {}
            )
            
            db.add(event)
            db.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ Error tracking event: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def update_daily_metrics(
        conversation_type: str,
        metric_type: str,
        db: Session
    ) -> bool:
        """
        Update daily conversation metrics
        
        Args:
            conversation_type: Type of conversation (e.g., "donating", "searching")
            metric_type: Type of metric update ("started", "completed", "abandoned")
            db: Database session
            
        Returns:
            True if metrics updated successfully
        """
        if metric_type not in ["started", "completed", "abandoned"]:
            return False
        
        try:
            today = date.today()
            
            # Get or create metrics record
            metrics = db.query(ConversationMetrics).filter(
                ConversationMetrics.date == today,
                ConversationMetrics.conversation_type == conversation_type
            ).first()
            
            if not metrics:
                metrics = ConversationMetrics(
                    date=today,
                    conversation_type=conversation_type
                )
                db.add(metrics)
            
            # Increment counter
            if metric_type == "started":
                metrics.started_count += 1
            elif metric_type == "completed":
                metrics.completed_count += 1
            elif metric_type == "abandoned":
                metrics.abandoned_count += 1
            
            metrics.updated_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error updating metrics: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_funnel_metrics(
        conversation_type: str,
        days: int,
        db: Session
    ) -> Dict[str, Dict]:
        """
        Get conversation funnel metrics with drop-off analysis
        
        Args:
            conversation_type: Type of conversation (e.g., "donating")
            days: Number of days to analyze
            db: Database session
            
        Returns:
            Dictionary with step counts and percentages
            {
                "campaign_selection": {"count": 100, "percentage": 100.0},
                "amount_entry": {"count": 80, "percentage": 80.0},
                ...
            }
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get step completion counts
            step_counts = db.query(
                ConversationEvent.current_step,
                func.count(ConversationEvent.id).label('count')
            ).filter(
                and_(
                    ConversationEvent.conversation_state == conversation_type,
                    ConversationEvent.event_type == "step_completed",
                    ConversationEvent.created_at >= start_date
                )
            ).group_by(ConversationEvent.current_step).all()
            
            if not step_counts:
                return {}
            
            # Calculate percentages relative to first step
            step_dict = {step: count for step, count in step_counts if step}
            
            if not step_dict:
                return {}
            
            # Get total started (first step or started event)
            total_started = db.query(func.count(ConversationEvent.id)).filter(
                and_(
                    ConversationEvent.conversation_state == conversation_type,
                    ConversationEvent.event_type == "conversation_started",
                    ConversationEvent.created_at >= start_date
                )
            ).scalar() or 0
            
            # If no started events, use max step count as baseline
            if total_started == 0:
                total_started = max(step_dict.values()) if step_dict else 1
            
            # Build funnel with percentages
            funnel = {}
            for step, count in step_dict.items():
                percentage = (count / total_started * 100) if total_started > 0 else 0
                funnel[step] = {
                    "count": count,
                    "percentage": round(percentage, 1)
                }
            
            return funnel
            
        except Exception as e:
            print(f"❌ Error getting funnel metrics: {e}")
            return {}
    
    @staticmethod
    def get_summary_metrics(
        days: int,
        db: Session
    ) -> Dict:
        """
        Get summary metrics for all conversations
        
        Args:
            days: Number of days to analyze
            db: Database session
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            start_date = date.today() - timedelta(days=days)
            
            # Get metrics for period
            metrics = db.query(ConversationMetrics).filter(
                ConversationMetrics.date >= start_date
            ).all()
            
            if not metrics:
                return {
                    "started": 0,
                    "completed": 0,
                    "abandoned": 0,
                    "completion_rate": 0.0
                }
            
            # Calculate totals
            total_started = sum(m.started_count for m in metrics)
            total_completed = sum(m.completed_count for m in metrics)
            total_abandoned = sum(m.abandoned_count for m in metrics)
            
            completion_rate = (total_completed / total_started * 100) if total_started > 0 else 0
            
            # Get previous period for comparison
            prev_start_date = start_date - timedelta(days=days)
            prev_metrics = db.query(ConversationMetrics).filter(
                and_(
                    ConversationMetrics.date >= prev_start_date,
                    ConversationMetrics.date < start_date
                )
            ).all()
            
            previous_period = None
            if prev_metrics:
                prev_started = sum(m.started_count for m in prev_metrics)
                prev_completed = sum(m.completed_count for m in prev_metrics)
                prev_abandoned = sum(m.abandoned_count for m in prev_metrics)
                prev_rate = (prev_completed / prev_started * 100) if prev_started > 0 else 0
                
                previous_period = {
                    "started": prev_started,
                    "completed": prev_completed,
                    "abandoned": prev_abandoned,
                    "completion_rate": round(prev_rate, 1)
                }
            
            return {
                "started": total_started,
                "completed": total_completed,
                "abandoned": total_abandoned,
                "completion_rate": round(completion_rate, 1),
                "previous_period": previous_period
            }
            
        except Exception as e:
            print(f"❌ Error getting summary metrics: {e}")
            return {
                "started": 0,
                "completed": 0,
                "abandoned": 0,
                "completion_rate": 0.0
            }
    
    @staticmethod
    def get_daily_metrics(
        days: int,
        db: Session
    ) -> List[Dict]:
        """
        Get daily metrics breakdown
        
        Args:
            days: Number of days to retrieve
            db: Database session
            
        Returns:
            List of daily metrics dictionaries
        """
        try:
            start_date = date.today() - timedelta(days=days)
            
            # Get metrics ordered by date
            metrics = db.query(ConversationMetrics).filter(
                ConversationMetrics.date >= start_date
            ).order_by(ConversationMetrics.date).all()
            
            return [
                {
                    "date": m.date.isoformat(),
                    "type": m.conversation_type,
                    "started": m.started_count,
                    "completed": m.completed_count,
                    "abandoned": m.abandoned_count,
                    "completion_rate": round(
                        (m.completed_count / m.started_count * 100) if m.started_count > 0 else 0,
                        1
                    )
                }
                for m in metrics
            ]
            
        except Exception as e:
            print(f"❌ Error getting daily metrics: {e}")
            return []
    
    @staticmethod
    def get_recent_events(
        limit: int,
        db: Session
    ) -> List[Dict]:
        """
        Get recent conversation events
        
        Args:
            limit: Maximum number of events to return
            db: Database session
            
        Returns:
            List of recent event dictionaries
        """
        try:
            events = db.query(ConversationEvent).order_by(
                desc(ConversationEvent.created_at)
            ).limit(limit).all()
            
            return [
                {
                    "event_type": e.event_type,
                    "conversation_state": e.conversation_state,
                    "current_step": e.current_step,
                    "event_data": e.event_data or {},
                    "created_at": e.created_at.isoformat()
                }
                for e in events
            ]
            
        except Exception as e:
            print(f"❌ Error getting recent events: {e}")
            return []

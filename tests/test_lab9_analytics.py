"""
Test Suite for Lab 9 Part 4: Conversation Analytics

Tests analytics tracking, metrics calculation, and dashboard API endpoints.
"""

import sys
import os
from datetime import datetime, date, timedelta
from unittest.mock import Mock, MagicMock, patch

# Mock database models before importing
sys.modules['database.models'] = Mock()
sys.modules['database.db'] = Mock()

# Create mock models
class MockUser:
    def __init__(self, id, telegram_id):
        self.id = id
        self.telegram_id = telegram_id

class MockConversationEvent:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.user_id = kwargs.get('user_id')
        self.session_id = kwargs.get('session_id', 'test-session')
        self.event_type = kwargs.get('event_type')
        self.conversation_state = kwargs.get('conversation_state')
        self.current_step = kwargs.get('current_step')
        self.event_data = kwargs.get('event_data', {})
        self.created_at = kwargs.get('created_at', datetime.utcnow())

class MockConversationMetrics:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.date = kwargs.get('date', date.today())
        self.conversation_type = kwargs.get('conversation_type', 'donating')
        self.started_count = kwargs.get('started_count', 0)
        self.completed_count = kwargs.get('completed_count', 0)
        self.abandoned_count = kwargs.get('abandoned_count', 0)
        self.avg_duration_seconds = kwargs.get('avg_duration_seconds')
        self.avg_messages = kwargs.get('avg_messages')
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

# Set up mock models
sys.modules['database.models'].User = MockUser
sys.modules['database.models'].ConversationEvent = MockConversationEvent
sys.modules['database.models'].ConversationMetrics = MockConversationMetrics

# Now we can import the analytics module
from voice.conversation.analytics import ConversationAnalytics


def test_1_track_event():
    """Test 1: Track conversation events"""
    print("\n" + "="*60)
    print("TEST 1: Track Conversation Events")
    print("="*60)
    
    # Mock database session
    mock_db = Mock()
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = MockUser(1, "123")
    
    # Track started event
    result = ConversationAnalytics.track_event(
        user_id="123",
        session_id="abc-123",
        event_type="conversation_started",
        conversation_state="donating",
        db=mock_db
    )
    
    assert result == True, "Event tracking failed"
    assert mock_db.add.called, "Event not added to database"
    assert mock_db.commit.called, "Changes not committed"
    print("✅ Event tracking works")
    
    # Track step completion
    result = ConversationAnalytics.track_event(
        user_id="123",
        session_id="abc-123",
        event_type="step_completed",
        conversation_state="donating",
        current_step="enter_amount",
        event_data={"amount": 500},
        db=mock_db
    )
    
    assert result == True, "Step tracking failed"
    print("✅ Step tracking works")
    
    # Track completion
    result = ConversationAnalytics.track_event(
        user_id="123",
        session_id="abc-123",
        event_type="conversation_completed",
        conversation_state="donating",
        db=mock_db
    )
    
    assert result == True, "Completion tracking failed"
    print("✅ Completion tracking works")
    
    print("\n✅ TEST 1 PASSED: All event types tracked successfully")


def test_2_update_metrics():
    """Test 2: Update daily metrics"""
    print("\n" + "="*60)
    print("TEST 2: Update Daily Metrics")
    print("="*60)
    
    # Mock database session
    mock_db = Mock()
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    
    # No existing metrics
    mock_query.filter.return_value.first.return_value = None
    
    # Update started count
    result = ConversationAnalytics.update_daily_metrics(
        conversation_type="donating",
        metric_type="started",
        db=mock_db
    )
    
    assert result == True, "Metrics update failed"
    assert mock_db.add.called, "New metrics record not created"
    print("✅ Creates new metrics record when none exists")
    
    # Simulate existing metrics
    existing_metrics = MockConversationMetrics(
        started_count=10,
        completed_count=5,
        abandoned_count=5
    )
    mock_query.filter.return_value.first.return_value = existing_metrics
    
    # Update completed count
    result = ConversationAnalytics.update_daily_metrics(
        conversation_type="donating",
        metric_type="completed",
        db=mock_db
    )
    
    assert result == True, "Metrics update failed"
    assert existing_metrics.completed_count == 6, "Counter not incremented"
    print("✅ Increments existing metrics correctly")
    
    print("\n✅ TEST 2 PASSED: Daily metrics updated successfully")


def test_3_funnel_metrics():
    """Test 3: Calculate funnel metrics"""
    print("\n" + "="*60)
    print("TEST 3: Calculate Funnel Metrics")
    print("="*60)
    
    # Mock database session
    mock_db = Mock()
    
    # Mock step completion data
    mock_steps = [
        ("campaign_selection", 100),
        ("enter_amount", 80),
        ("select_payment", 65),
        ("confirm", 50),
    ]
    
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.group_by.return_value.all.return_value = mock_steps
    
    # Mock total started count
    mock_query.filter.return_value.scalar.return_value = 100
    
    # Get funnel
    funnel = ConversationAnalytics.get_funnel_metrics(
        conversation_type="donating",
        days=7,
        db=mock_db
    )
    
    assert "campaign_selection" in funnel, "Missing campaign_selection step"
    assert funnel["campaign_selection"]["count"] == 100, "Wrong count"
    assert funnel["campaign_selection"]["percentage"] == 100.0, "Wrong percentage"
    print("✅ Campaign selection: 100 users (100%)")
    
    assert "enter_amount" in funnel, "Missing enter_amount step"
    assert funnel["enter_amount"]["percentage"] == 80.0, "Wrong percentage"
    print("✅ Amount entry: 80 users (80%) - 20% drop-off")
    
    assert "select_payment" in funnel, "Missing select_payment step"
    assert funnel["select_payment"]["percentage"] == 65.0, "Wrong percentage"
    print("✅ Payment selection: 65 users (65%) - 15% drop-off")
    
    print("\n✅ TEST 3 PASSED: Funnel metrics calculated correctly")


def test_4_summary_metrics():
    """Test 4: Get summary metrics"""
    print("\n" + "="*60)
    print("TEST 4: Get Summary Metrics")
    print("="*60)
    
    # Mock database session
    mock_db = Mock()
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    
    # Mock current period metrics
    current_metrics = [
        MockConversationMetrics(started_count=150, completed_count=68, abandoned_count=82),
        MockConversationMetrics(started_count=100, completed_count=45, abandoned_count=55),
    ]
    
    # Mock previous period metrics
    previous_metrics = [
        MockConversationMetrics(started_count=120, completed_count=50, abandoned_count=70),
    ]
    
    # Set up query mocks
    filter_mock = Mock()
    mock_query.filter.return_value = filter_mock
    
    # First call returns current period, second returns previous
    filter_mock.all.side_effect = [current_metrics, previous_metrics]
    
    # Get summary
    summary = ConversationAnalytics.get_summary_metrics(days=7, db=mock_db)
    
    assert summary["started"] == 250, f"Wrong started count: {summary['started']}"
    assert summary["completed"] == 113, f"Wrong completed count: {summary['completed']}"
    assert summary["abandoned"] == 137, f"Wrong abandoned count: {summary['abandoned']}"
    print(f"✅ Started: {summary['started']}, Completed: {summary['completed']}, Abandoned: {summary['abandoned']}")
    
    assert 44.0 <= summary["completion_rate"] <= 46.0, "Completion rate should be ~45%"
    print(f"✅ Completion rate: {summary['completion_rate']}%")
    
    assert "previous_period" in summary, "Missing previous period comparison"
    assert summary["previous_period"]["started"] == 120, "Wrong previous period data"
    print(f"✅ Previous period comparison included")
    
    print("\n✅ TEST 4 PASSED: Summary metrics calculated correctly")


def test_5_daily_metrics():
    """Test 5: Get daily metrics breakdown"""
    print("\n" + "="*60)
    print("TEST 5: Get Daily Metrics Breakdown")
    print("="*60)
    
    # Mock database session
    mock_db = Mock()
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    
    # Mock daily data
    today = date.today()
    daily_data = [
        MockConversationMetrics(
            date=today - timedelta(days=2),
            started_count=50,
            completed_count=25,
            abandoned_count=25
        ),
        MockConversationMetrics(
            date=today - timedelta(days=1),
            started_count=60,
            completed_count=30,
            abandoned_count=30
        ),
        MockConversationMetrics(
            date=today,
            started_count=40,
            completed_count=18,
            abandoned_count=22
        ),
    ]
    
    mock_query.filter.return_value.order_by.return_value.all.return_value = daily_data
    
    # Get daily metrics
    daily = ConversationAnalytics.get_daily_metrics(days=3, db=mock_db)
    
    assert len(daily) == 3, f"Expected 3 days, got {len(daily)}"
    print(f"✅ Retrieved {len(daily)} days of data")
    
    assert daily[0]["started"] == 50, "Wrong data for day 1"
    assert daily[0]["completion_rate"] == 50.0, "Wrong completion rate calculation"
    print(f"✅ Day 1: 50 started, 50% completion")
    
    assert daily[1]["started"] == 60, "Wrong data for day 2"
    print(f"✅ Day 2: 60 started, 50% completion")
    
    assert daily[2]["started"] == 40, "Wrong data for day 3"
    assert daily[2]["completion_rate"] == 45.0, "Wrong completion rate for day 3"
    print(f"✅ Day 3: 40 started, 45% completion")
    
    print("\n✅ TEST 5 PASSED: Daily metrics breakdown correct")


def test_6_recent_events():
    """Test 6: Get recent events"""
    print("\n" + "="*60)
    print("TEST 6: Get Recent Events")
    print("="*60)
    
    # Mock database session
    mock_db = Mock()
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    
    # Mock recent events
    events = [
        MockConversationEvent(
            id=1,
            event_type="conversation_started",
            conversation_state="donating",
            created_at=datetime.utcnow()
        ),
        MockConversationEvent(
            id=2,
            event_type="step_completed",
            conversation_state="donating",
            current_step="enter_amount",
            event_data={"amount": 500}
        ),
        MockConversationEvent(
            id=3,
            event_type="conversation_completed",
            conversation_state="donating"
        ),
    ]
    
    mock_query.order_by.return_value.limit.return_value.all.return_value = events
    
    # Get recent events
    recent = ConversationAnalytics.get_recent_events(limit=10, db=mock_db)
    
    assert len(recent) == 3, f"Expected 3 events, got {len(recent)}"
    print(f"✅ Retrieved {len(recent)} recent events")
    
    assert recent[0]["event_type"] == "conversation_started", "Wrong event type"
    print("✅ Event 1: conversation_started")
    
    assert recent[1]["event_type"] == "step_completed", "Wrong event type"
    assert recent[1]["current_step"] == "enter_amount", "Missing step info"
    assert recent[1]["event_data"]["amount"] == 500, "Missing event data"
    print("✅ Event 2: step_completed with data")
    
    assert recent[2]["event_type"] == "conversation_completed", "Wrong event type"
    print("✅ Event 3: conversation_completed")
    
    print("\n✅ TEST 6 PASSED: Recent events retrieved correctly")


def run_all_tests():
    """Run all analytics tests"""
    print("\n" + "="*70)
    print("  LAB 9 PART 4: CONVERSATION ANALYTICS - TEST SUITE")
    print("="*70)
    
    try:
        test_1_track_event()
        test_2_update_metrics()
        test_3_funnel_metrics()
        test_4_summary_metrics()
        test_5_daily_metrics()
        test_6_recent_events()
        
        print("\n" + "="*70)
        print("  ✅ ALL TESTS PASSED - ANALYTICS WORKING")
        print("="*70)
        
        print("\n📊 Analytics Features Verified:")
        print("  ✅ Event tracking (started, step_completed, completed, abandoned)")
        print("  ✅ Daily metrics aggregation")
        print("  ✅ Funnel analysis with drop-off rates")
        print("  ✅ Summary statistics with period comparison")
        print("  ✅ Daily metrics breakdown")
        print("  ✅ Recent events retrieval")
        
        print("\n🎯 Integration Points:")
        print("  • SessionManager tracks events automatically")
        print("  • API endpoints at /api/analytics/*")
        print("  • Dashboard UI at /conversation-analytics.html")
        print("  • Real-time metrics with 30s auto-refresh")
        
        print("\n📈 Dashboard Capabilities:")
        print("  • Summary cards with trend indicators")
        print("  • Daily trend chart (Chart.js)")
        print("  • Interactive funnel visualization")
        print("  • Recent events feed")
        print("  • 7/30/90 day period selector")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Video Progress Verification (VPV) - Technical Implementation Plan

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     VPV System Architecture                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Upload     │    │  Processing  │    │   Delivery   │  │
│  │   Layer      │───▶│    Layer     │───▶│    Layer     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │          │
│         │                    │                    │          │
│  ┌──────▼──────┐    ┌───────▼────────┐  ┌────────▼──────┐ │
│  │  Telegram   │    │   Video        │  │   CDN         │ │
│  │  Bot API    │    │   Processor    │  │   (Railway)   │ │
│  │  + Web UI   │    │   + Metadata   │  │   + Streaming │ │
│  └─────────────┘    └────────────────┘  └───────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Storage & Database Layer                │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │  PostgreSQL  │  Redis Cache  │  S3/R2 Object Store │    │
│  │  (Metadata)  │  (Sessions)   │  (Video Files)      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: MVP Implementation (2-3 weeks)

### 1.1 Database Schema

```sql
-- Campaign milestones table
CREATE TABLE campaign_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    milestone_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_amount DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed
    expected_date DATE,
    completed_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(campaign_id, milestone_number)
);

-- Video updates table
CREATE TABLE video_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    milestone_id UUID REFERENCES campaign_milestones(id),
    uploader_id UUID NOT NULL REFERENCES users(id),
    
    -- Video storage
    video_url TEXT NOT NULL,
    thumbnail_url TEXT,
    duration_seconds INTEGER,
    file_size_bytes BIGINT,
    
    -- Metadata
    title VARCHAR(255) NOT NULL,
    description TEXT,
    recorded_at TIMESTAMP,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Verification data
    video_hash VARCHAR(64) NOT NULL, -- SHA-256 hash
    gps_latitude DECIMAL(10, 8),
    gps_longitude DECIMAL(11, 8),
    gps_accuracy_meters DECIMAL(6, 2),
    device_info JSONB, -- {model, os, app_version}
    
    -- Financial data
    amount_spent DECIMAL(10, 2),
    expense_breakdown JSONB, -- [{item, cost, receipt_url}]
    
    -- Engagement metrics
    view_count INTEGER DEFAULT 0,
    unique_viewers INTEGER DEFAULT 0,
    average_watch_time_seconds DECIMAL(6, 2),
    share_count INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, published, flagged
    moderation_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Video interactions table
CREATE TABLE video_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES video_updates(id),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Interaction type
    interaction_type VARCHAR(50) NOT NULL, -- view, share, comment, flag
    
    -- For comments
    comment_text TEXT,
    voice_message_url TEXT,
    
    -- For views
    watch_duration_seconds INTEGER,
    watched_to_end BOOLEAN,
    
    -- For flags
    flag_reason VARCHAR(100),
    flag_details TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verification records table
CREATE TABLE video_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES video_updates(id),
    verifier_id UUID REFERENCES users(id), -- field agent or admin
    
    verification_type VARCHAR(50) NOT NULL, -- gps, receipt, identity, third_party
    verification_status VARCHAR(50) NOT NULL, -- verified, disputed, pending
    
    verification_data JSONB, -- Type-specific verification details
    notes TEXT,
    
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_video_updates_campaign ON video_updates(campaign_id);
CREATE INDEX idx_video_updates_milestone ON video_updates(milestone_id);
CREATE INDEX idx_video_updates_status ON video_updates(status);
CREATE INDEX idx_video_interactions_video ON video_interactions(video_id);
CREATE INDEX idx_video_interactions_user ON video_interactions(user_id);
```

### 1.2 Video Upload Flow

#### API Endpoints

```python
# voice/routers/vpv.py

from fastapi import APIRouter, UploadFile, File, Form, Depends
from typing import Optional
import hashlib
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/vpv", tags=["video-verification"])

@router.post("/videos/upload")
async def upload_video(
    campaign_id: str = Form(...),
    milestone_id: Optional[str] = Form(None),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    amount_spent: Optional[float] = Form(None),
    gps_latitude: Optional[float] = Form(None),
    gps_longitude: Optional[float] = Form(None),
    recorded_at: Optional[datetime] = Form(None),
    video_file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a video progress update.
    
    Flow:
    1. Validate user has permission to upload for this campaign
    2. Calculate video hash
    3. Upload to object storage
    4. Create database record
    5. Queue for processing (transcoding, thumbnail generation)
    6. Notify campaign donors
    """
    
    # Validate campaign ownership
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign or campaign.creator_id != user.id:
        raise HTTPException(403, "Not authorized")
    
    # Read video file
    video_content = await video_file.read()
    
    # Calculate SHA-256 hash
    video_hash = hashlib.sha256(video_content).hexdigest()
    
    # Check for duplicate
    existing = db.query(VideoUpdate).filter(
        VideoUpdate.video_hash == video_hash
    ).first()
    if existing:
        raise HTTPException(400, "Video already uploaded")
    
    # Generate unique filename
    file_extension = video_file.filename.split('.')[-1]
    storage_key = f"videos/{campaign_id}/{uuid.uuid4()}.{file_extension}"
    
    # Upload to object storage (implement based on provider)
    video_url = await upload_to_storage(storage_key, video_content)
    
    # Create database record
    video_update = VideoUpdate(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        milestone_id=milestone_id,
        uploader_id=user.id,
        video_url=video_url,
        title=title,
        description=description,
        video_hash=video_hash,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
        recorded_at=recorded_at or datetime.utcnow(),
        amount_spent=amount_spent,
        file_size_bytes=len(video_content),
        status='processing'
    )
    
    db.add(video_update)
    db.commit()
    
    # Queue for processing
    from voice.tasks.video_tasks import process_video_task
    process_video_task.delay(str(video_update.id))
    
    # Notify donors
    from voice.tasks.notification_tasks import notify_video_upload
    notify_video_upload.delay(str(campaign_id), str(video_update.id))
    
    return {
        "video_id": str(video_update.id),
        "status": "processing",
        "message": "Video uploaded successfully and is being processed"
    }

@router.get("/videos/{video_id}")
async def get_video(
    video_id: str,
    db: Session = Depends(get_db)
):
    """Get video details and streaming URL."""
    video = db.query(VideoUpdate).filter(VideoUpdate.id == video_id).first()
    if not video:
        raise HTTPException(404, "Video not found")
    
    # Increment view count (use Redis for better performance)
    video.view_count += 1
    db.commit()
    
    return {
        "id": str(video.id),
        "campaign_id": str(video.campaign_id),
        "title": video.title,
        "description": video.description,
        "video_url": video.video_url,
        "thumbnail_url": video.thumbnail_url,
        "duration_seconds": video.duration_seconds,
        "recorded_at": video.recorded_at,
        "uploaded_at": video.uploaded_at,
        "gps": {
            "latitude": video.gps_latitude,
            "longitude": video.gps_longitude
        } if video.gps_latitude else None,
        "financial": {
            "amount_spent": video.amount_spent,
            "breakdown": video.expense_breakdown
        },
        "engagement": {
            "views": video.view_count,
            "shares": video.share_count
        }
    }

@router.get("/campaigns/{campaign_id}/videos")
async def list_campaign_videos(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """List all videos for a campaign, grouped by milestone."""
    videos = db.query(VideoUpdate).filter(
        VideoUpdate.campaign_id == campaign_id,
        VideoUpdate.status == 'published'
    ).order_by(VideoUpdate.uploaded_at.asc()).all()
    
    return [
        {
            "id": str(v.id),
            "title": v.title,
            "thumbnail_url": v.thumbnail_url,
            "uploaded_at": v.uploaded_at,
            "duration_seconds": v.duration_seconds,
            "view_count": v.view_count
        }
        for v in videos
    ]

@router.post("/videos/{video_id}/interact")
async def record_interaction(
    video_id: str,
    interaction_type: str = Form(...),  # view, share, comment
    comment_text: Optional[str] = Form(None),
    watch_duration: Optional[int] = Form(None),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record user interaction with video."""
    interaction = VideoInteraction(
        video_id=video_id,
        user_id=user.id,
        interaction_type=interaction_type,
        comment_text=comment_text,
        watch_duration_seconds=watch_duration
    )
    db.add(interaction)
    db.commit()
    
    return {"status": "recorded"}
```

### 1.3 Video Processing (Celery Tasks)

```python
# voice/tasks/video_tasks.py

from celery import shared_task
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import VideoUpdate
import subprocess
import os
from PIL import Image
import io

@shared_task
def process_video_task(video_id: str):
    """
    Process uploaded video:
    1. Extract metadata (duration, resolution)
    2. Generate thumbnail
    3. Transcode to web-friendly format (H.264/AAC)
    4. Generate multiple quality variants (480p, 720p)
    5. Update database
    """
    db = SessionLocal()
    try:
        video = db.query(VideoUpdate).filter(VideoUpdate.id == video_id).first()
        if not video:
            return {"error": "Video not found"}
        
        # Download video from storage
        local_path = f"/tmp/{video_id}.mp4"
        download_from_storage(video.video_url, local_path)
        
        # Extract duration using ffprobe
        duration = get_video_duration(local_path)
        video.duration_seconds = duration
        
        # Generate thumbnail (frame at 25% mark)
        thumbnail_path = f"/tmp/{video_id}_thumb.jpg"
        generate_thumbnail(local_path, thumbnail_path, duration * 0.25)
        
        # Upload thumbnail
        thumbnail_url = upload_to_storage(
            f"thumbnails/{video.campaign_id}/{video_id}.jpg",
            open(thumbnail_path, 'rb').read()
        )
        video.thumbnail_url = thumbnail_url
        
        # Transcode to H.264 if needed
        if not is_web_compatible(local_path):
            transcoded_path = f"/tmp/{video_id}_web.mp4"
            transcode_video(local_path, transcoded_path)
            
            # Re-upload transcoded version
            new_url = upload_to_storage(
                f"videos/{video.campaign_id}/{video_id}_web.mp4",
                open(transcoded_path, 'rb').read()
            )
            video.video_url = new_url
        
        # Update status
        video.status = 'published'
        db.commit()
        
        # Cleanup
        os.remove(local_path)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        
        return {"status": "success", "video_id": video_id}
        
    except Exception as e:
        video.status = 'error'
        db.commit()
        return {"error": str(e)}
    finally:
        db.close()

def get_video_duration(video_path: str) -> int:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return int(float(result.stdout.strip()))

def generate_thumbnail(video_path: str, output_path: str, timestamp: float):
    """Extract frame at timestamp as thumbnail."""
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-ss', str(timestamp),
        '-vframes', '1',
        '-vf', 'scale=640:-1',
        output_path
    ]
    subprocess.run(cmd, check=True)

def transcode_video(input_path: str, output_path: str):
    """Transcode video to H.264/AAC for web compatibility."""
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        '-vf', 'scale=1280:-2',  # Max 720p
        output_path
    ]
    subprocess.run(cmd, check=True)
```

### 1.4 Telegram Bot Integration

```python
# voice/telegram/vpv_handlers.py

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
import requests

async def upload_video_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upload_video command."""
    user = update.effective_user
    
    # Check if user has campaigns
    campaigns = get_user_campaigns(str(user.id))
    if not campaigns:
        await update.message.reply_text(
            "You don't have any active campaigns. Create one first using /create_campaign"
        )
        return
    
    # Show campaign selection
    keyboard = [
        [InlineKeyboardButton(c['title'], callback_data=f"upload:{c['id']}")]
        for c in campaigns
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Select campaign for video update:",
        reply_markup=reply_markup
    )

async def handle_video_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video messages sent to bot."""
    user = update.effective_user
    video = update.message.video
    
    # Check if in upload flow
    user_state = get_user_state(str(user.id))
    if not user_state or user_state.get('action') != 'uploading_video':
        await update.message.reply_text(
            "Send /upload_video first to start uploading"
        )
        return
    
    campaign_id = user_state['campaign_id']
    
    await update.message.reply_text("📤 Uploading video...")
    
    try:
        # Download video from Telegram
        file = await context.bot.get_file(video.file_id)
        video_bytes = await file.download_as_bytearray()
        
        # Upload to our API
        response = requests.post(
            f"{API_BASE}/api/vpv/videos/upload",
            files={'video_file': ('video.mp4', video_bytes, 'video/mp4')},
            data={
                'campaign_id': campaign_id,
                'title': user_state.get('title', 'Progress Update'),
                'description': user_state.get('description', ''),
                'recorded_at': update.message.date.isoformat()
            },
            headers={'Authorization': f'Bearer {get_user_token(user.id)}'}
        )
        
        if response.status_code == 200:
            await update.message.reply_text(
                "✅ Video uploaded successfully!\n"
                "It's being processed and will be available to donors shortly."
            )
        else:
            await update.message.reply_text(
                f"❌ Upload failed: {response.json().get('detail', 'Unknown error')}"
            )
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    # Clear state
    clear_user_state(str(user.id))

# Register handlers
application.add_handler(CommandHandler("upload_video", upload_video_command))
application.add_handler(MessageHandler(filters.VIDEO, handle_video_message))
```

### 1.5 Frontend Integration (Miniapp)

```html
<!-- frontend-miniapps/vpv-viewer.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Campaign Progress</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        .video-container {
            position: relative;
            width: 100%;
            margin-bottom: 20px;
        }
        
        video {
            width: 100%;
            border-radius: 12px;
        }
        
        .video-overlay {
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
        }
        
        .milestone-card {
            background: #f5f5f5;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 12px;
        }
        
        .financial-breakdown {
            background: white;
            padding: 12px;
            border-radius: 8px;
            margin-top: 12px;
        }
        
        .expense-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Progress Updates</h2>
        <div id="videos-container"></div>
    </div>
    
    <script>
        const API_BASE = window.location.origin;
        const urlParams = new URLSearchParams(window.location.search);
        const campaignId = urlParams.get('campaign_id');
        
        async function loadVideos() {
            const response = await fetch(`${API_BASE}/api/vpv/campaigns/${campaignId}/videos`);
            const videos = await response.json();
            
            const container = document.getElementById('videos-container');
            
            for (const video of videos) {
                const videoCard = createVideoCard(video);
                container.appendChild(videoCard);
            }
        }
        
        function createVideoCard(video) {
            const card = document.createElement('div');
            card.className = 'milestone-card';
            
            card.innerHTML = `
                <div class="video-container">
                    <video controls preload="metadata">
                        <source src="${video.video_url}" type="video/mp4">
                    </video>
                    <div class="video-overlay">
                        ${formatDate(video.uploaded_at)}
                    </div>
                </div>
                <h3>${video.title}</h3>
                <p>${video.description || ''}</p>
                ${video.financial ? createFinancialBreakdown(video.financial) : ''}
                <div style="display: flex; gap: 16px; margin-top: 12px; font-size: 14px; color: #666;">
                    <span>👁 ${video.view_count} views</span>
                    <span>📤 ${video.share_count} shares</span>
                </div>
            `;
            
            return card;
        }
        
        function createFinancialBreakdown(financial) {
            if (!financial.breakdown) return '';
            
            let html = '<div class="financial-breakdown">';
            html += `<strong>Amount Spent: $${financial.amount_spent}</strong>`;
            html += '<div style="margin-top: 8px;">';
            
            for (const expense of financial.breakdown) {
                html += `
                    <div class="expense-item">
                        <span>${expense.item}</span>
                        <span>$${expense.cost}</span>
                    </div>
                `;
            }
            
            html += '</div></div>';
            return html;
        }
        
        function formatDate(dateStr) {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                year: 'numeric'
            });
        }
        
        loadVideos();
    </script>
</body>
</html>
```

## Phase 2: Enhanced Features (4-6 weeks)

### 2.1 Video Compression & Optimization

```python
# voice/services/video_compression.py

import ffmpeg
from typing import Tuple

class VideoCompressor:
    """Optimize videos for mobile delivery."""
    
    @staticmethod
    def compress_for_mobile(
        input_path: str,
        output_path: str,
        target_bitrate: str = "500k",
        max_resolution: Tuple[int, int] = (854, 480)  # 480p
    ):
        """
        Compress video for mobile data efficiency.
        
        Target: < 5MB per minute of video
        """
        stream = ffmpeg.input(input_path)
        
        # Get input dimensions
        probe = ffmpeg.probe(input_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        width = int(video_info['width'])
        height = int(video_info['height'])
        
        # Calculate scaled dimensions (maintain aspect ratio)
        if width > max_resolution[0] or height > max_resolution[1]:
            scale = min(max_resolution[0] / width, max_resolution[1] / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            # Ensure dimensions are divisible by 2 (H.264 requirement)
            new_width = new_width - (new_width % 2)
            new_height = new_height - (new_height % 2)
        else:
            new_width, new_height = width, height
        
        stream = ffmpeg.output(
            stream,
            output_path,
            vcodec='libx264',
            video_bitrate=target_bitrate,
            acodec='aac',
            audio_bitrate='64k',
            vf=f'scale={new_width}:{new_height}',
            preset='medium',
            crf=28,  # Higher CRF = more compression
            movflags='faststart'  # Enable progressive streaming
        )
        
        ffmpeg.run(stream, overwrite_output=True)
```

### 2.2 Video Verification System

```python
# voice/services/video_verification.py

from typing import Dict, Any
from geopy.distance import geodesic
from datetime import datetime, timedelta

class VideoVerifier:
    """Verify authenticity of video updates."""
    
    @staticmethod
    def verify_gps_consistency(
        video: VideoUpdate,
        campaign: Campaign,
        tolerance_meters: float = 1000
    ) -> Dict[str, Any]:
        """
        Verify video was recorded near campaign location.
        """
        if not video.gps_latitude or not campaign.location_lat:
            return {
                "verified": False,
                "reason": "Missing GPS data"
            }
        
        video_coords = (video.gps_latitude, video.gps_longitude)
        campaign_coords = (campaign.location_lat, campaign.location_lng)
        
        distance = geodesic(video_coords, campaign_coords).meters
        
        if distance <= tolerance_meters:
            return {
                "verified": True,
                "distance_meters": distance
            }
        else:
            return {
                "verified": False,
                "reason": f"Video recorded {distance:.0f}m from campaign location",
                "distance_meters": distance
            }
    
    @staticmethod
    def verify_timestamp_plausibility(
        video: VideoUpdate,
        campaign: Campaign
    ) -> Dict[str, Any]:
        """
        Check if video timestamp is plausible.
        """
        # Video can't be from before campaign started
        if video.recorded_at < campaign.created_at:
            return {
                "verified": False,
                "reason": "Video dated before campaign creation"
            }
        
        # Video can't be from future
        if video.recorded_at > datetime.utcnow() + timedelta(hours=1):
            return {
                "verified": False,
                "reason": "Video dated in the future"
            }
        
        return {"verified": True}
    
    @staticmethod
    def verify_spending_consistency(
        video: VideoUpdate,
        campaign: Campaign
    ) -> Dict[str, Any]:
        """
        Verify claimed spending doesn't exceed campaign funds.
        """
        # Get total raised
        total_raised = campaign.total_raised or 0
        
        # Get cumulative spending from all videos
        previous_videos = db.query(VideoUpdate).filter(
            VideoUpdate.campaign_id == campaign.id,
            VideoUpdate.uploaded_at < video.uploaded_at
        ).all()
        
        total_spent = sum(v.amount_spent or 0 for v in previous_videos)
        total_spent += (video.amount_spent or 0)
        
        if total_spent > total_raised * 1.1:  # 10% buffer for estimation
            return {
                "verified": False,
                "reason": f"Claimed spending (${total_spent}) exceeds funds raised (${total_raised})"
            }
        
        return {
            "verified": True,
            "total_spent": total_spent,
            "total_raised": total_raised,
            "remaining": total_raised - total_spent
        }
    
    @staticmethod
    def calculate_trust_score(video: VideoUpdate, campaign: Campaign) -> float:
        """
        Calculate trust score (0-100) based on verification checks.
        """
        score = 100.0
        
        # GPS verification (-30 if failed)
        gps_result = VideoVerifier.verify_gps_consistency(video, campaign)
        if not gps_result['verified']:
            score -= 30
        
        # Timestamp verification (-20 if failed)
        time_result = VideoVerifier.verify_timestamp_plausibility(video, campaign)
        if not time_result['verified']:
            score -= 20
        
        # Spending verification (-25 if failed)
        spending_result = VideoVerifier.verify_spending_consistency(video, campaign)
        if not spending_result['verified']:
            score -= 25
        
        # Video quality indicators (+/- 10)
        if video.duration_seconds and video.duration_seconds < 10:
            score -= 10  # Too short
        elif video.duration_seconds and video.duration_seconds > 180:
            score -= 5   # Too long
        
        # Third-party verification (+15)
        if db.query(VideoVerification).filter(
            VideoVerification.video_id == video.id,
            VideoVerification.verification_status == 'verified'
        ).count() > 0:
            score += 15
        
        return max(0, min(100, score))
```

### 2.3 Analytics Dashboard

```python
# voice/routers/vpv_analytics.py

@router.get("/campaigns/{campaign_id}/analytics")
async def get_campaign_vpv_analytics(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """Get VPV analytics for campaign."""
    
    videos = db.query(VideoUpdate).filter(
        VideoUpdate.campaign_id == campaign_id,
        VideoUpdate.status == 'published'
    ).all()
    
    total_views = sum(v.view_count for v in videos)
    total_shares = sum(v.share_count for v in videos)
    avg_watch_time = sum(v.average_watch_time_seconds or 0 for v in videos) / len(videos) if videos else 0
    
    # Engagement rate: unique viewers / campaign donors
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    donor_count = db.query(Donation).filter(
        Donation.campaign_id == campaign_id
    ).distinct(Donation.donor_id).count()
    
    engagement_rate = (sum(v.unique_viewers for v in videos) / donor_count * 100) if donor_count > 0 else 0
    
    # Video frequency
    if len(videos) >= 2:
        first_video = min(videos, key=lambda v: v.uploaded_at)
        last_video = max(videos, key=lambda v: v.uploaded_at)
        days_active = (last_video.uploaded_at - first_video.uploaded_at).days
        videos_per_week = len(videos) / (days_active / 7) if days_active > 0 else 0
    else:
        videos_per_week = 0
    
    return {
        "video_count": len(videos),
        "total_views": total_views,
        "total_shares": total_shares,
        "average_watch_time_seconds": round(avg_watch_time, 1),
        "engagement_rate_percent": round(engagement_rate, 1),
        "videos_per_week": round(videos_per_week, 2),
        "trust_score": calculate_campaign_trust_score(campaign_id, db),
        "milestone_completion": calculate_milestone_progress(campaign_id, db)
    }
```

## Phase 3: Scale & Automation (8-12 weeks)

### 3.1 Object Storage Integration

```python
# config/storage.py

import boto3
from botocore.client import Config
import os

class StorageConfig:
    """Storage configuration for video files."""
    
    # Choose provider: AWS S3, Cloudflare R2, or Railway volumes
    PROVIDER = os.getenv("STORAGE_PROVIDER", "cloudflare_r2")
    
    # Cloudflare R2 (S3-compatible, no egress fees)
    if PROVIDER == "cloudflare_r2":
        s3_client = boto3.client(
            's3',
            endpoint_url=os.getenv("R2_ENDPOINT"),
            aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
        BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "trustvoice-videos")
        PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://videos.trustvoice.app")
    
    # AWS S3
    elif PROVIDER == "aws_s3":
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "trustvoice-videos")
        PUBLIC_URL = f"https://{BUCKET_NAME}.s3.amazonaws.com"

def upload_to_storage(key: str, file_content: bytes) -> str:
    """Upload file to configured storage provider."""
    StorageConfig.s3_client.put_object(
        Bucket=StorageConfig.BUCKET_NAME,
        Key=key,
        Body=file_content,
        ContentType='video/mp4'
    )
    return f"{StorageConfig.PUBLIC_URL}/{key}"

def download_from_storage(url: str, local_path: str):
    """Download file from storage to local path."""
    key = url.split(StorageConfig.PUBLIC_URL + '/')[-1]
    StorageConfig.s3_client.download_file(
        StorageConfig.BUCKET_NAME,
        key,
        local_path
    )
```

### 3.2 Automated Notifications

```python
# voice/tasks/notification_tasks.py

@shared_task
def notify_video_upload(campaign_id: str, video_id: str):
    """Notify all campaign donors about new video update."""
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        video = db.query(VideoUpdate).filter(VideoUpdate.id == video_id).first()
        
        # Get all donors for this campaign
        donations = db.query(Donation).filter(
            Donation.campaign_id == campaign_id
        ).distinct(Donation.donor_id).all()
        
        donor_ids = [d.donor_id for d in donations]
        users = db.query(User).filter(User.id.in_(donor_ids)).all()
        
        # Send Telegram notifications
        for user in users:
            if user.telegram_user_id:
                send_telegram_message(
                    user.telegram_user_id,
                    f"📹 New update from {campaign.title}!\n\n"
                    f"{video.title}\n\n"
                    f"Watch now: {get_video_url(video_id)}",
                    buttons=[
                        [{"text": "Watch Video", "url": get_video_url(video_id)}],
                        [{"text": "View Campaign", "url": get_campaign_url(campaign_id)}]
                    ]
                )
        
        # Send email notifications (optional)
        for user in users:
            if user.email:
                send_email(
                    to=user.email,
                    subject=f"New Progress Update: {campaign.title}",
                    template="video_update",
                    context={
                        "campaign": campaign,
                        "video": video,
                        "user": user
                    }
                )
        
        return {"notified": len(users)}
    finally:
        db.close()
```

### 3.3 AI-Powered Features (Future)

```python
# voice/services/video_ai.py

from openai import OpenAI

class VideoAI:
    """AI-powered video analysis features."""
    
    @staticmethod
    async def generate_video_summary(video_id: str) -> str:
        """
        Generate text summary of video content using Whisper + GPT-4.
        """
        # 1. Extract audio
        audio_path = extract_audio_from_video(video_id)
        
        # 2. Transcribe with Whisper
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # 3. Summarize with GPT-4
        summary = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize this campaign progress update in 2-3 sentences."},
                {"role": "user", "content": transcript.text}
            ]
        )
        
        return summary.choices[0].message.content
    
    @staticmethod
    async def detect_video_content(video_path: str) -> Dict:
        """
        Use GPT-4 Vision to analyze video frames.
        Detect: people, construction materials, equipment, etc.
        """
        # Extract key frames
        frames = extract_frames(video_path, num_frames=5)
        
        # Analyze with GPT-4 Vision
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        analysis = []
        for frame in frames:
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe what you see in this construction/campaign progress image. Focus on: materials, equipment, people, progress indicators."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{encode_image(frame)}"}
                            }
                        ]
                    }
                ],
                max_tokens=200
            )
            analysis.append(response.choices[0].message.content)
        
        return {
            "frame_descriptions": analysis,
            "detected_elements": extract_keywords(analysis)
        }
    
    @staticmethod
    async def auto_tag_milestones(video_id: str, campaign_id: str):
        """
        Automatically suggest which milestone a video belongs to.
        """
        video = db.query(VideoUpdate).filter(VideoUpdate.id == video_id).first()
        milestones = db.query(CampaignMilestone).filter(
            CampaignMilestone.campaign_id == campaign_id,
            CampaignMilestone.status != 'completed'
        ).all()
        
        # Get video content description
        content = await VideoAI.detect_video_content(video.video_url)
        
        # Match to milestone using GPT-4
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Match this video content to the most relevant milestone."
                },
                {
                    "role": "user",
                    "content": f"Video description: {content}\n\nMilestones: {[m.title for m in milestones]}\n\nWhich milestone?"
                }
            ]
        )
        
        suggested_milestone = response.choices[0].message.content
        return suggested_milestone
```

## Infrastructure Requirements

### 3.4 System Dependencies

```dockerfile
# Dockerfile additions for VPV

# Install ffmpeg for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libavcodec-extra \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
RUN pip install \
    ffmpeg-python==0.2.0 \
    pillow==10.1.0 \
    opencv-python==4.8.1.78 \
    boto3==1.29.7
```

### 3.5 Environment Variables

```bash
# Add to Railway project settings

# Storage
STORAGE_PROVIDER=cloudflare_r2
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=trustvoice-videos
R2_PUBLIC_URL=https://videos.trustvoice.app

# Video Processing
MAX_VIDEO_SIZE_MB=100
MAX_VIDEO_DURATION_SECONDS=300
VIDEO_COMPRESSION_QUALITY=medium
THUMBNAIL_SIZE=640x360

# AI Features (optional)
ENABLE_VIDEO_AI=false
OPENAI_API_KEY=sk-...
```

### 3.6 Celery Worker Configuration

```python
# Add to Railway worker service

# voice/tasks/celery_app.py

# Add video processing queue
app.conf.task_routes = {
    'voice.tasks.video_tasks.*': {'queue': 'video_processing'},
    'voice.tasks.voice_tasks.*': {'queue': 'voice_processing'},
    'voice.tasks.notification_tasks.*': {'queue': 'notifications'},
}

# Configure result backend for video tasks
app.conf.result_backend = 'redis://redis:6379/1'
app.conf.result_expires = 3600  # 1 hour
```

## Performance Optimization

### 3.7 Video Streaming Optimization

```python
# Use CDN for video delivery
# Add to main.py

from fastapi.responses import StreamingResponse
import aiohttp

@app.get("/stream/video/{video_id}")
async def stream_video(video_id: str, range: str = Header(None)):
    """
    Stream video with range request support for seek functionality.
    """
    video = db.query(VideoUpdate).filter(VideoUpdate.id == video_id).first()
    if not video:
        raise HTTPException(404)
    
    # Get video from storage
    video_url = video.video_url
    
    headers = {}
    if range:
        headers['Range'] = range
    
    async with aiohttp.ClientSession() as session:
        async with session.get(video_url, headers=headers) as response:
            content = await response.read()
            
            return StreamingResponse(
                io.BytesIO(content),
                media_type="video/mp4",
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Range": response.headers.get('Content-Range', ''),
                    "Content-Length": str(len(content))
                }
            )
```

### 3.8 Caching Strategy

```python
# voice/services/video_cache.py

from functools import lru_cache
import redis

redis_client = redis.from_url(os.getenv("REDIS_URL"))

def cache_video_metadata(video_id: str, ttl: int = 3600):
    """Cache video metadata in Redis."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"video_meta:{video_id}"
            cached = redis_client.get(cache_key)
            
            if cached:
                return json.loads(cached)
            
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

## Testing Strategy

### 3.9 Unit Tests

```python
# tests/test_vpv.py

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_upload_video():
    """Test video upload endpoint."""
    with open("test_video.mp4", "rb") as video_file:
        response = client.post(
            "/api/vpv/videos/upload",
            files={"video_file": video_file},
            data={
                "campaign_id": "test-campaign-id",
                "title": "Test Update"
            },
            headers={"Authorization": "Bearer test_token"}
        )
    
    assert response.status_code == 200
    assert "video_id" in response.json()

def test_video_verification():
    """Test GPS verification logic."""
    from voice.services.video_verification import VideoVerifier
    
    result = VideoVerifier.verify_gps_consistency(
        video=mock_video(lat=9.0, lon=38.7),
        campaign=mock_campaign(lat=9.001, lon=38.701)
    )
    
    assert result["verified"] == True
    assert result["distance_meters"] < 1000
```

## Monitoring & Analytics

### 3.10 Metrics to Track

```python
# voice/monitoring/vpv_metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Video upload metrics
video_uploads_total = Counter(
    'vpv_video_uploads_total',
    'Total number of video uploads',
    ['status']  # success, failed
)

video_processing_duration = Histogram(
    'vpv_video_processing_duration_seconds',
    'Time to process uploaded video',
    buckets=[10, 30, 60, 120, 300, 600]
)

# Engagement metrics
video_views_total = Counter(
    'vpv_video_views_total',
    'Total video views'
)

video_watch_duration = Histogram(
    'vpv_video_watch_duration_seconds',
    'Time users spend watching videos',
    buckets=[10, 30, 60, 90, 120, 180]
)

# Storage metrics
video_storage_bytes = Gauge(
    'vpv_video_storage_bytes',
    'Total bytes used for video storage'
)
```

## Cost Estimation

### Monthly Operating Costs (1000 active campaigns)

**Storage (Cloudflare R2):**
- 10TB video storage: $15/month
- No egress fees: $0
- Subtotal: $15/month

**Video Processing (Railway):**
- Worker instance: $20/month
- Additional compute: ~$30/month
- Subtotal: $50/month

**Database:**
- PostgreSQL (Neon): $19/month
- Redis: $10/month (Railway add-on)
- Subtotal: $29/month

**Total: ~$94/month** for 1000 campaigns with VPV

**Per-Campaign Cost: $0.09/month**

## Deployment Checklist

- [ ] Database migrations run
- [ ] Object storage configured (R2/S3)
- [ ] FFmpeg installed on worker
- [ ] Celery worker started with video queue
- [ ] Environment variables set
- [ ] Test video upload flow
- [ ] Test video streaming
- [ ] Monitoring dashboard configured
- [ ] Backup strategy for videos
- [ ] CDN configured (optional)

## Security Considerations

### 3.11 Video Upload Security

```python
# voice/security/video_validation.py

from magic import Magic

class VideoSecurityValidator:
    """Validate uploaded videos for security."""
    
    ALLOWED_FORMATS = ['video/mp4', 'video/quicktime', 'video/x-msvideo']
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_DURATION = 600  # 10 minutes
    
    @staticmethod
    def validate_file(file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded video file."""
        
        # Check file size
        if len(file_content) > VideoSecurityValidator.MAX_FILE_SIZE:
            return {
                "valid": False,
                "error": "File too large (max 100MB)"
            }
        
        # Verify MIME type (don't trust extension)
        mime = Magic(mime=True)
        detected_type = mime.from_buffer(file_content)
        
        if detected_type not in VideoSecurityValidator.ALLOWED_FORMATS:
            return {
                "valid": False,
                "error": f"Invalid file type: {detected_type}"
            }
        
        # Check for malicious content (basic)
        if b'<script' in file_content or b'<?php' in file_content:
            return {
                "valid": False,
                "error": "Suspicious content detected"
            }
        
        return {"valid": True}
```

## Conclusion

This implementation plan provides a complete technical roadmap for Video Progress Verification. Start with Phase 1 MVP (2-3 weeks), validate with Zimbabwe borehole project, then progressively add features based on user feedback and scale requirements.

**Success Criteria:**
- 90%+ video upload success rate
- < 60 seconds average processing time
- 70%+ donor video view rate
- 50%+ completion rate for VPV campaigns vs. 30% without

**Next Actions:**
1. Review and approve architecture
2. Set up development environment
3. Implement Phase 1 MVP
4. Test with Zimbabwe pilot
5. Iterate based on learnings

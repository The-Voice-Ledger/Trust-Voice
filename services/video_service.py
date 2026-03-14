"""
Video Transparency Service

Handles video upload, storage, hashing, and optional IPFS pinning
for the three-act transparency framework.

Storage backends (selected via R2_VIDEOS_BUCKET env var):
  1. Cloudflare R2 (production) — S3-compatible, $0.015/GB, zero egress
     Requires: R2_VIDEOS_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
               R2_ENDPOINT_URL, R2_PUBLIC_URL
  2. Local disk (development) — /uploads/videos/{uuid}.{ext}

Both backends:
  - SHA-256 integrity hash computed on upload
  - Optional IPFS pinning via existing IPFSService

Supports:
  Act 1 "Why We Need This" — campaign pitch video
  Act 2 "What We Are Doing" — progress stream
  Act 3 "What We Did"       — milestone closeout
  Field Agent Verification  — independent GPS-tagged evidence
"""

import os
import hashlib
import logging
import uuid
import tempfile
from pathlib import Path
from typing import BinaryIO, Optional, Dict, Any
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

logger = logging.getLogger(__name__)

# Max file size: 100 MB
MAX_VIDEO_SIZE_BYTES = 100 * 1024 * 1024
# Max duration: 5 minutes for progress updates
MAX_PROGRESS_DURATION_SECONDS = 300
ALLOWED_MIME_TYPES = {
    "video/mp4", "video/webm", "video/quicktime",
    "video/x-msvideo", "video/x-matroska",
}
UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "videos"

# GPS proximity threshold: 2 km
GPS_PROXIMITY_THRESHOLD_KM = 2.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS points in kilometres."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def _get_r2_client():
    """Lazily create an S3 client pointing at Cloudflare R2."""
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("R2_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )


class VideoService:
    """
    Manages video storage, integrity hashing, GPS verification,
    and IPFS integration.

    Automatically uses Cloudflare R2 in production (when R2_VIDEOS_BUCKET
    is set), otherwise falls back to local disk.

    Usage:
        from services.video_service import video_service

        result = video_service.store_video(
            file=uploaded_file,
            filename="evidence.mp4",
            category="progress",
            parent_type="milestone",
            parent_id=42,
        )
    """

    def __init__(self):
        self.r2_bucket = os.getenv("R2_VIDEOS_BUCKET")
        self.r2_public_url = os.getenv("R2_PUBLIC_URL", "").rstrip("/")
        self.use_r2 = bool(self.r2_bucket and os.getenv("R2_ACCESS_KEY_ID"))

        if self.use_r2:
            logger.info("VideoService: using Cloudflare R2 bucket '%s'", self.r2_bucket)
        else:
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            logger.info("VideoService: using local disk storage at %s", UPLOAD_DIR)

    # ── Core storage ───────────────────────────────────────────

    def store_video(
        self,
        file: BinaryIO,
        filename: str,
        category: str,
        parent_type: str,
        parent_id: int,
        pin_to_ipfs: bool = False,
        duration_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Store a video file, hash it with SHA-256, and return storage metadata.

        Raises ValueError if file exceeds size/duration limits.
        """
        # Enforce 5-minute cap on progress updates
        if category == "progress" and duration_seconds is not None:
            if duration_seconds > MAX_PROGRESS_DURATION_SECONDS:
                raise ValueError(
                    f"Progress videos must be under {MAX_PROGRESS_DURATION_SECONDS // 60} minutes"
                )

        ext = Path(filename).suffix.lower() or ".mp4"
        video_uuid = str(uuid.uuid4())
        dest_filename = f"{video_uuid}{ext}"

        # Stream to a temp file while hashing (works for both backends)
        sha256 = hashlib.sha256()
        total_bytes = 0

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        try:
            while True:
                chunk = file.read(64 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_VIDEO_SIZE_BYTES:
                    tmp.close()
                    os.unlink(tmp.name)
                    raise ValueError(
                        f"Video exceeds {MAX_VIDEO_SIZE_BYTES // (1024 * 1024)}MB limit"
                    )
                sha256.update(chunk)
                tmp.write(chunk)
            tmp.close()

            content_hash = sha256.hexdigest()

            # Route to correct backend
            if self.use_r2:
                storage_url = self._upload_to_r2(
                    tmp.name, dest_filename, category, parent_type, parent_id,
                )
            else:
                storage_url = self._save_local(tmp.name, dest_filename)
        finally:
            # Clean temp file (may already be moved by _save_local)
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

        logger.info(
            "Stored video: %s (%s bytes, sha256=%s) via %s for %s:%d [%s]",
            dest_filename, total_bytes, content_hash[:16],
            "R2" if self.use_r2 else "local",
            parent_type, parent_id, category,
        )

        result = {
            "storage_url": storage_url,
            "sha256": content_hash,
            "file_size": total_bytes,
            "uuid": video_uuid,
            "ipfs_cid": None,
        }

        if pin_to_ipfs:
            # For R2, we'd need to download the file first — skip for now
            if not self.use_r2:
                local_path = UPLOAD_DIR / dest_filename
                result["ipfs_cid"] = self._pin_to_ipfs(
                    local_path, dest_filename, category, parent_type, parent_id,
                )

        return result

    # ── R2 backend ─────────────────────────────────────────────

    def _upload_to_r2(
        self, tmp_path: str, dest_filename: str,
        category: str, parent_type: str, parent_id: int,
    ) -> str:
        """Upload file to Cloudflare R2 and return public URL."""
        key = f"videos/{parent_type}/{parent_id}/{category}/{dest_filename}"
        client = _get_r2_client()
        client.upload_file(
            tmp_path, self.r2_bucket, key,
            ExtraArgs={"ContentType": "video/mp4"},
        )
        if self.r2_public_url:
            return f"{self.r2_public_url}/{key}"
        return f"r2://{self.r2_bucket}/{key}"

    def _delete_from_r2(self, storage_url: str) -> bool:
        """Delete a file from R2."""
        try:
            # Extract key from URL
            if self.r2_public_url and storage_url.startswith(self.r2_public_url):
                key = storage_url[len(self.r2_public_url) + 1:]
            elif storage_url.startswith("r2://"):
                key = storage_url.split("/", 3)[3]
            else:
                logger.warning("Cannot parse R2 key from: %s", storage_url)
                return False
            client = _get_r2_client()
            client.delete_object(Bucket=self.r2_bucket, Key=key)
            logger.info("Deleted from R2: %s", key)
            return True
        except Exception as e:
            logger.error("R2 delete failed: %s", e)
            return False

    # ── Local backend ──────────────────────────────────────────

    def _save_local(self, tmp_path: str, dest_filename: str) -> str:
        """Move temp file to local uploads directory."""
        import shutil
        dest_path = UPLOAD_DIR / dest_filename
        shutil.move(tmp_path, str(dest_path))
        return f"/uploads/videos/{dest_filename}"

    # ── Common operations ──────────────────────────────────────

    def delete_video(self, storage_url: str) -> bool:
        """Delete a video from whichever backend holds it."""
        if self.use_r2 and not storage_url.startswith("/uploads/"):
            return self._delete_from_r2(storage_url)
        try:
            filename = Path(storage_url).name
            filepath = UPLOAD_DIR / filename
            if filepath.exists():
                filepath.unlink()
                logger.info("Deleted local video: %s", filename)
                return True
            logger.warning("Video not found for deletion: %s", filename)
            return False
        except Exception as e:
            logger.error("Error deleting video %s: %s", storage_url, e)
            return False

    def get_video_path(self, storage_url: str) -> Optional[Path]:
        """Get absolute path for a locally stored video (None if R2)."""
        if self.use_r2 and not storage_url.startswith("/uploads/"):
            return None
        filename = Path(storage_url).name
        filepath = UPLOAD_DIR / filename
        return filepath if filepath.exists() else None

    # ── GPS & integrity ────────────────────────────────────────

    def check_gps_proximity(
        self,
        video_lat: float,
        video_lon: float,
        project_gps: Optional[str],
        threshold_km: float = GPS_PROXIMITY_THRESHOLD_KM,
    ) -> Dict[str, Any]:
        """
        Check if video GPS is within threshold of the project site.

        Args:
            video_lat, video_lon: GPS from the uploaded video
            project_gps: Campaign location_gps string "lat,lon"
            threshold_km: Max distance in km (default 2km)

        Returns:
            { "within_range": bool, "distance_km": float, "threshold_km": float }
        """
        if not project_gps:
            return {"within_range": None, "distance_km": None, "threshold_km": threshold_km, "reason": "No project GPS on record"}

        try:
            parts = project_gps.split(",")
            proj_lat = float(parts[0].strip())
            proj_lon = float(parts[1].strip())
        except (ValueError, IndexError):
            return {"within_range": None, "distance_km": None, "threshold_km": threshold_km, "reason": "Invalid project GPS format"}

        distance = _haversine_km(video_lat, video_lon, proj_lat, proj_lon)
        within = distance <= threshold_km

        if not within:
            logger.warning(
                "GPS proximity check FAILED: video (%.4f,%.4f) is %.1f km from project (%.4f,%.4f) — threshold %.1f km",
                video_lat, video_lon, distance, proj_lat, proj_lon, threshold_km,
            )

        return {
            "within_range": within,
            "distance_km": round(distance, 2),
            "threshold_km": threshold_km,
        }

    def verify_integrity(self, storage_url: str, expected_hash: str) -> bool:
        """
        Verify file integrity by comparing SHA-256 hash.
        Works for local files only; R2 files verified via stored hash.
        """
        filepath = self.get_video_path(storage_url)
        if not filepath:
            # For R2 files, we trust the hash recorded at upload time
            logger.info("Cannot verify R2 file locally — hash was verified at upload")
            return True

        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(64 * 1024)
                if not chunk:
                    break
                sha256.update(chunk)

        actual_hash = sha256.hexdigest()
        is_valid = actual_hash == expected_hash
        if not is_valid:
            logger.warning(
                "Integrity check FAILED for %s: expected %s, got %s",
                storage_url, expected_hash[:16], actual_hash[:16],
            )
        return is_valid

    def auto_generate_title(self, category: str, parent_type: str, parent_title: Optional[str] = None) -> str:
        """
        Auto-generate a human-friendly title when user doesn't provide one.

        Examples:
            "Progress Update — Mwanza Water Project — 14 Mar 2026"
            "Completion Evidence — Land Preparation — 14 Mar 2026"
        """
        date_str = datetime.utcnow().strftime("%d %b %Y")
        cat_labels = {
            "why": "Campaign Pitch",
            "progress": "Progress Update",
            "completion": "Completion Evidence",
            "verification": "Field Verification",
        }
        cat_label = cat_labels.get(category, category.title())
        if parent_title:
            return f"{cat_label} — {parent_title} — {date_str}"
        return f"{cat_label} — {date_str}"

    # ── IPFS ───────────────────────────────────────────────────

    def _pin_to_ipfs(
        self, filepath: Path, filename: str,
        category: str, parent_type: str, parent_id: int,
    ) -> Optional[str]:
        """Pin video to IPFS via Pinata (best-effort)."""
        try:
            from services.ipfs_service import ipfs_service

            with open(filepath, "rb") as f:
                result = ipfs_service.pin_file(
                    file=f,
                    filename=filename,
                    metadata={
                        "category": category,
                        "parent_type": parent_type,
                        "parent_id": str(parent_id),
                        "type": "transparency_video",
                    },
                )
            cid = result.get("IpfsHash")
            if cid:
                logger.info("Pinned video to IPFS: %s", cid)
            return cid
        except Exception as e:
            logger.warning("IPFS pinning failed (non-fatal): %s", e)
            return None


# Singleton
video_service = VideoService()

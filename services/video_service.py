"""
Video Transparency Service

Handles video upload, storage, hashing, and optional IPFS pinning
for the three-act transparency framework.

Storage Strategy (MVP):
  - Files saved to /uploads/videos/{uuid}.{ext}
  - SHA-256 integrity hash computed on upload
  - Optional IPFS pinning via existing IPFSService
  - Ready for R2/S3 migration (swap storage_backend)

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
from pathlib import Path
from typing import BinaryIO, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Max file size: 100 MB
MAX_VIDEO_SIZE_BYTES = 100 * 1024 * 1024
ALLOWED_MIME_TYPES = {
    "video/mp4", "video/webm", "video/quicktime",
    "video/x-msvideo", "video/x-matroska",
}
UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "videos"


class VideoService:
    """
    Manages video storage, integrity hashing, and IPFS integration.

    Usage:
        from services.video_service import video_service

        result = video_service.store_video(
            file=uploaded_file,
            filename="evidence.mp4",
            category="progress",
            parent_type="milestone",
            parent_id=42,
        )
        # result = { "storage_url": "/uploads/videos/...", "sha256": "abc...", "file_size": 12345678 }
    """

    def __init__(self):
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def store_video(
        self,
        file: BinaryIO,
        filename: str,
        category: str,
        parent_type: str,
        parent_id: int,
        pin_to_ipfs: bool = False,
    ) -> Dict[str, Any]:
        """
        Store a video file and compute its SHA-256 hash.

        Args:
            file: File-like object (SpooledTemporaryFile from FastAPI)
            filename: Original filename
            category: Video category (why, progress, completion, verification)
            parent_type: 'campaign' or 'milestone'
            parent_id: ID of the parent entity
            pin_to_ipfs: Whether to also pin to IPFS via Pinata

        Returns:
            dict with storage_url, sha256, file_size, ipfs_cid (optional)

        Raises:
            ValueError: If file exceeds size limit or has invalid type
        """
        # Generate unique filename preserving extension
        ext = Path(filename).suffix.lower() or ".mp4"
        video_uuid = str(uuid.uuid4())
        dest_filename = f"{video_uuid}{ext}"
        dest_path = UPLOAD_DIR / dest_filename

        # Stream file to disk while computing hash
        sha256 = hashlib.sha256()
        total_bytes = 0

        with open(dest_path, "wb") as out:
            while True:
                chunk = file.read(64 * 1024)  # 64KB chunks
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_VIDEO_SIZE_BYTES:
                    # Clean up and reject
                    out.close()
                    dest_path.unlink(missing_ok=True)
                    raise ValueError(
                        f"Video exceeds {MAX_VIDEO_SIZE_BYTES // (1024*1024)}MB limit"
                    )
                sha256.update(chunk)
                out.write(chunk)

        content_hash = sha256.hexdigest()
        storage_url = f"/uploads/videos/{dest_filename}"

        logger.info(
            "Stored video: %s (%s bytes, sha256=%s) for %s:%d [%s]",
            dest_filename, total_bytes, content_hash[:16],
            parent_type, parent_id, category,
        )

        result = {
            "storage_url": storage_url,
            "sha256": content_hash,
            "file_size": total_bytes,
            "uuid": video_uuid,
            "ipfs_cid": None,
        }

        # Optional IPFS pinning
        if pin_to_ipfs:
            result["ipfs_cid"] = self._pin_to_ipfs(dest_path, dest_filename, category, parent_type, parent_id)

        return result

    def delete_video(self, storage_url: str) -> bool:
        """Delete a video file from local storage."""
        try:
            filename = Path(storage_url).name
            filepath = UPLOAD_DIR / filename
            if filepath.exists():
                filepath.unlink()
                logger.info("Deleted video: %s", filename)
                return True
            logger.warning("Video not found for deletion: %s", filename)
            return False
        except Exception as e:
            logger.error("Error deleting video %s: %s", storage_url, e)
            return False

    def get_video_path(self, storage_url: str) -> Optional[Path]:
        """Get absolute path for a stored video."""
        filename = Path(storage_url).name
        filepath = UPLOAD_DIR / filename
        return filepath if filepath.exists() else None

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

    def verify_integrity(self, storage_url: str, expected_hash: str) -> bool:
        """
        Verify file integrity by comparing SHA-256 hash.
        Used by donors/auditors to confirm video hasn't been tampered with.
        """
        filepath = self.get_video_path(storage_url)
        if not filepath:
            return False

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


# Singleton
video_service = VideoService()

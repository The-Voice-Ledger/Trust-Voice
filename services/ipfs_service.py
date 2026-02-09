"""
IPFS Service using Pinata

Provides IPFS pinning and retrieval for:
- Campaign transparency videos
- Tax receipt NFT metadata
- Impact verification documents

Pinata API Documentation: https://docs.pinata.cloud/
Free tier: 1GB storage, unlimited gateway bandwidth
"""

import os
import requests
import logging
import json
from typing import BinaryIO, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class IPFSService:
    """
    IPFS service using Pinata for content pinning.
    
    Usage:
        from services.ipfs_service import ipfs_service
        
        # Pin video file
        result = ipfs_service.pin_file(file_object, "campaign_video.mp4")
        video_url = ipfs_service.get_gateway_url(result["IpfsHash"])
        
        # Pin JSON metadata (for NFTs)
        metadata = {"name": "Tax Receipt #123", ...}
        result = ipfs_service.pin_json(metadata, "receipt-123")
        metadata_uri = f"ipfs://{result['IpfsHash']}"
    """
    
    def __init__(self):
        """Initialize Pinata service with API credentials."""
        self.api_key = os.getenv("PINATA_API_KEY")
        self.api_secret = os.getenv("PINATA_API_SECRET")
        self.jwt = os.getenv("PINATA_JWT")  # Alternative to API key/secret
        
        # Pinata API endpoints
        self.pin_file_url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        self.pin_json_url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
        self.unpin_url = "https://api.pinata.cloud/pinning/unpin"
        
        # IPFS gateway URLs (public access)
        self.gateways = [
            "https://gateway.pinata.cloud/ipfs/",
            "https://ipfs.io/ipfs/",  # Fallback
            "https://cloudflare-ipfs.com/ipfs/"  # Fallback
        ]
        self.default_gateway = self.gateways[0]
        
        # Validate configuration
        if not (self.jwt or (self.api_key and self.api_secret)):
            logger.warning("Pinata credentials not configured. IPFS functionality will be limited.")
    
    def _get_headers(self, content_type: Optional[str] = None) -> Dict[str, str]:
        """
        Get authentication headers for Pinata API.
        
        Args:
            content_type: Optional content type header
            
        Returns:
            Headers dictionary with authentication
        """
        if self.jwt:
            headers = {"Authorization": f"Bearer {self.jwt}"}
        elif self.api_key and self.api_secret:
            headers = {
                "pinata_api_key": self.api_key,
                "pinata_secret_api_key": self.api_secret
            }
        else:
            raise ValueError("Pinata credentials not configured")
        
        if content_type:
            headers["Content-Type"] = content_type
        
        return headers
    
    def pin_file(
        self, 
        file: BinaryIO, 
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Pin a file to IPFS via Pinata.
        
        Args:
            file: File-like object (BytesIO, opened file, etc.)
            filename: Name for the file
            metadata: Optional metadata to attach (campaign_id, creator, etc.)
        
        Returns:
            {
                "IpfsHash": "QmXxxx...",
                "PinSize": 1234567,
                "Timestamp": "2026-02-09T12:00:00.000Z"
            }
        
        Raises:
            requests.HTTPError: If pinning fails
            ValueError: If credentials not configured
        """
        try:
            # Prepare file for upload
            files = {
                "file": (filename, file)
            }
            
            # Prepare metadata
            pinata_options = {}
            if metadata:
                pinata_options["customPinPolicy"] = {
                    "regions": [
                        {"id": "FRA1", "desiredReplicationCount": 2},
                        {"id": "NYC1", "desiredReplicationCount": 2}
                    ]
                }
            
            data = {}
            if metadata:
                data["pinataMetadata"] = json.dumps({
                    "name": filename,
                    **metadata
                })
            
            if pinata_options:
                data["pinataOptions"] = json.dumps(pinata_options)
            
            # Make request
            headers = self._get_headers()
            response = requests.post(
                self.pin_file_url,
                files=files,
                data=data,
                headers=headers,
                timeout=300  # 5 minutes for large files
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"✅ File pinned to IPFS: {result['IpfsHash']} ({filename})")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to pin file to IPFS: {e}")
            raise
    
    def pin_json(
        self, 
        json_data: Dict[str, Any],
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pin JSON metadata to IPFS (for NFTs, receipts, etc.).
        
        Args:
            json_data: Dictionary to pin as JSON
            name: Optional name for the pinned content
        
        Returns:
            {
                "IpfsHash": "QmXxxx...",
                "PinSize": 1234,
                "Timestamp": "2026-02-09T12:00:00.000Z"
            }
        
        Example NFT metadata:
            {
                "name": "TrustVoice Donation Receipt #12345",
                "description": "Tax-deductible donation receipt",
                "image": "ipfs://QmImageHash",
                "attributes": [
                    {"trait_type": "Amount", "value": "100 USD"},
                    {"trait_type": "Date", "value": "2026-02-09"}
                ]
            }
        """
        try:
            payload = {
                "pinataContent": json_data
            }
            
            if name:
                payload["pinataMetadata"] = {
                    "name": name,
                    "keyvalues": {
                        "uploaded_at": datetime.utcnow().isoformat(),
                        "type": "json_metadata"
                    }
                }
            
            headers = self._get_headers(content_type="application/json")
            response = requests.post(
                self.pin_json_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"✅ JSON pinned to IPFS: {result['IpfsHash']} ({name or 'unnamed'})")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to pin JSON to IPFS: {e}")
            raise
    
    def unpin(self, ipfs_hash: str) -> bool:
        """
        Remove a pin from Pinata (free up storage space).
        
        Args:
            ipfs_hash: IPFS hash to unpin (QmXxxx...)
        
        Returns:
            True if successful, False otherwise
        
        Warning: Content will be removed from IPFS network if no other nodes pin it!
        """
        try:
            headers = self._get_headers()
            response = requests.delete(
                f"{self.unpin_url}/{ipfs_hash}",
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            logger.info(f"✅ Unpinned from IPFS: {ipfs_hash}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to unpin from IPFS: {e}")
            return False
    
    def get_gateway_url(self, ipfs_hash: str, gateway: Optional[str] = None) -> str:
        """
        Convert IPFS hash to public gateway URL.
        
        Args:
            ipfs_hash: IPFS hash (QmXxxx... or bafyxxx...)
            gateway: Optional specific gateway URL
        
        Returns:
            Full HTTP URL to access content
        
        Example:
            "QmXxxx..." -> "https://gateway.pinata.cloud/ipfs/QmXxxx..."
        """
        gateway_url = gateway or self.default_gateway
        return f"{gateway_url}{ipfs_hash}"
    
    def get_ipfs_uri(self, ipfs_hash: str) -> str:
        """
        Convert IPFS hash to ipfs:// URI (for NFT metadata).
        
        Args:
            ipfs_hash: IPFS hash
        
        Returns:
            "ipfs://QmXxxx..."
        """
        return f"ipfs://{ipfs_hash}"
    
    def test_connection(self) -> bool:
        """
        Test Pinata API connection.
        
        Returns:
            True if credentials are valid and API is accessible
        """
        try:
            headers = self._get_headers()
            response = requests.get(
                "https://api.pinata.cloud/data/testAuthentication",
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"✅ Pinata connection successful: {result.get('message')}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Pinata connection failed: {e}")
            return False
    
    def get_pin_list(self, status: str = "pinned", limit: int = 10) -> Dict[str, Any]:
        """
        List pinned content from Pinata.
        
        Args:
            status: Pin status filter (pinned, unpinned)
            limit: Maximum number of items to return
        
        Returns:
            {
                "count": 5,
                "rows": [
                    {
                        "ipfs_pin_hash": "QmXxxx...",
                        "size": 1234567,
                        "date_pinned": "2026-02-09T12:00:00.000Z",
                        "metadata": {...}
                    }
                ]
            }
        """
        try:
            headers = self._get_headers()
            params = {
                "status": status,
                "pageLimit": limit
            }
            
            response = requests.get(
                "https://api.pinata.cloud/data/pinList",
                headers=headers,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get pin list: {e}")
            return {"count": 0, "rows": []}


# Global instance
ipfs_service = IPFSService()


# Convenience functions
def pin_campaign_video(video_file: BinaryIO, campaign_id: int, campaign_title: str) -> str:
    """
    Pin a campaign transparency video to IPFS.
    
    Args:
        video_file: Video file object
        campaign_id: Campaign database ID
        campaign_title: Campaign name
    
    Returns:
        IPFS hash (QmXxxx...)
    """
    result = ipfs_service.pin_file(
        file=video_file,
        filename=f"campaign_{campaign_id}_video.mp4",
        metadata={
            "campaign_id": campaign_id,
            "campaign_title": campaign_title,
            "content_type": "campaign_video",
            "uploaded_at": datetime.utcnow().isoformat()
        }
    )
    return result["IpfsHash"]


def pin_tax_receipt_metadata(donation_id: int, receipt_data: Dict[str, Any]) -> str:
    """
    Pin tax receipt NFT metadata to IPFS.
    
    Args:
        donation_id: Donation database ID
        receipt_data: NFT metadata dictionary
    
    Returns:
        IPFS hash (QmXxxx...)
    """
    result = ipfs_service.pin_json(
        json_data=receipt_data,
        name=f"tax_receipt_{donation_id}"
    )
    return result["IpfsHash"]


if __name__ == "__main__":
    # Test connection
    print("Testing Pinata connection...")
    if ipfs_service.test_connection():
        print("✅ Pinata is configured and working!")
    else:
        print("❌ Pinata connection failed. Check your credentials in .env")

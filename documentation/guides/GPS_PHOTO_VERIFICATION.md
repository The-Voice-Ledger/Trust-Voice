# GPS Photo Verification Implementation Guide

**TrustVoice Platform - Impact Verification System**

---

## Overview

GPS photo verification enables field officers to upload geotagged photos as proof of project completion. The system extracts GPS coordinates from photo metadata (EXIF data), validates location authenticity, and stores immutable records for donor transparency.

---

## Technical Approach

### 1. EXIF Metadata Extraction

**Primary Method:** Extract GPS coordinates embedded in photo metadata by smartphones.

**Python Libraries:**
```bash
pip install Pillow piexif GPSPhoto exifread
```

**Key Libraries:**
- **Pillow + piexif**: Image processing and EXIF manipulation
- **GPSPhoto**: Specialized GPS extraction from photos
- **exifread**: Read EXIF tags including GPS, timestamp, camera model

**Advantages:**
- 90%+ of modern smartphones embed GPS in photos by default
- No additional app or permission required from field officers
- Captures exact location where photo was taken
- Includes timestamp for verification

---

## Implementation Flow

### Step 1: Photo Upload Channels

**Multiple upload methods:**
1. **WhatsApp/Telegram Bot**: Field officer sends photo via chat
2. **Web Dashboard**: NGO admin uploads via browser
3. **Mobile App**: Direct upload from React Native app
4. **Email**: Automated parsing of photo attachments

### Step 2: EXIF Data Extraction

**Process:**
```python
# Pseudo-code structure
def extract_gps_from_photo(image_file):
    # 1. Load image
    # 2. Extract EXIF data
    # 3. Parse GPS coordinates (lat, lon)
    # 4. Extract timestamp
    # 5. Extract device info (camera model, phone)
    
    return {
        "latitude": -2.5164,
        "longitude": 32.9175,
        "timestamp": "2025-12-15T14:30:22Z",
        "device": "iPhone 14 Pro",
        "altitude": 1205.5  # meters (optional)
    }
```

**Key EXIF Tags:**
- `GPSLatitude` / `GPSLongitude`: Coordinates
- `GPSTimeStamp`: UTC time when photo taken
- `DateTime`: Local time
- `Make` / `Model`: Camera/phone info
- `GPSAltitude`: Elevation (optional)

### Step 3: Validation & Anti-Fraud

**Validation Checks:**

1. **GPS Coordinates Present?**
   - If missing: Flag for manual review or request re-upload
   - Option: Allow manual coordinate entry as fallback

2. **Location Proximity Check**
   ```python
   # Verify photo location within reasonable radius of campaign
   campaign_location = (-2.5000, 32.9000)  # Campaign center
   photo_location = (-2.5164, 32.9175)     # Photo GPS
   
   distance = haversine_distance(campaign_location, photo_location)
   
   if distance > 50_km:  # Configurable threshold
       flag_for_review("Photo location too far from campaign")
   ```

3. **Timestamp Validation**
   ```python
   # Check photo taken recently (not old photo reused)
   photo_timestamp = extract_timestamp(exif)
   upload_timestamp = datetime.now()
   
   time_diff = upload_timestamp - photo_timestamp
   
   if time_diff > timedelta(days=7):  # Max 7 days old
       flag_for_review("Photo older than 7 days")
   ```

4. **Duplicate Detection**
   ```python
   # Hash photo to detect reuse
   photo_hash = compute_perceptual_hash(image)
   
   if photo_hash in database:
       flag_for_review("Photo already used in another campaign")
   ```

5. **EXIF Manipulation Check**
   - Cross-reference GPS with IP geolocation of uploader
   - Check for inconsistencies (e.g., GPS says Tanzania but IP says India)
   - Verify EXIF data wasn't manually edited (harder to detect)

### Step 4: Storage & Display

**Database Schema:**
```sql
CREATE TABLE impact_photos (
    id UUID PRIMARY KEY,
    campaign_id UUID REFERENCES campaigns(id),
    uploader_id UUID REFERENCES users(id),
    
    -- Photo storage
    photo_url TEXT NOT NULL,  -- S3/Cloudflare R2 URL
    photo_hash TEXT NOT NULL,  -- For duplicate detection
    
    -- GPS data
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    altitude DECIMAL(10, 2),
    gps_accuracy DECIMAL(10, 2),  -- meters
    
    -- Timestamps
    photo_taken_at TIMESTAMPTZ,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Device info
    device_make TEXT,
    device_model TEXT,
    
    -- Validation
    validation_status VARCHAR(20) CHECK (validation_status IN 
        ('pending', 'approved', 'rejected', 'flagged')),
    validation_notes TEXT,
    distance_from_campaign DECIMAL(10, 2),  -- km
    
    -- Blockchain
    blockchain_hash TEXT,  -- IPFS or Ethereum hash
    blockchain_timestamp TIMESTAMPTZ,
    
    -- Metadata
    caption TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Storage Options:**
- **Images**: AWS S3, Cloudflare R2, or DigitalOcean Spaces
- **EXIF Data**: PostgreSQL database
- **Blockchain**: IPFS for decentralized storage + Ethereum for proof

### Step 5: Donor Display

**Show on Campaign Page:**
```
[Photo Thumbnail]
📍 Location: Mwanza, Tanzania (-2.5164, 32.9175)
📅 Taken: Dec 15, 2025 at 2:30 PM
📷 Device: iPhone 14 Pro
✓ GPS Verified
✓ Location within 5km of project site
✓ Blockchain Secured: 0x8f3a...

[View on Map] [View Full Size] [Blockchain Proof]
```

---

## Fallback Methods

### For Phones Without GPS or GPS Disabled

**Option 1: Browser/App Geolocation**
```javascript
// Request location at upload time
navigator.geolocation.getCurrentPosition((position) => {
    const coords = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy
    };
    // Attach to photo upload
});
```

**Option 2: Manual Entry**
- Officer enters coordinates manually
- Flag as "User-provided GPS" (less trustworthy)
- Require admin approval

**Option 3: IP Geolocation**
- Use IP address to approximate location
- Very rough (city-level at best)
- Only as last resort

---

## Python Implementation Example

```python
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
import hashlib

class GPSPhotoVerifier:
    
    def extract_gps_data(self, image_path):
        """Extract GPS coordinates and metadata from photo EXIF"""
        try:
            image = Image.open(image_path)
            exif = image._getexif()
            
            if not exif:
                return {"error": "No EXIF data found"}
            
            gps_data = {}
            
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                
                if tag == "GPSInfo":
                    for gps_tag_id in value:
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = value[gps_tag_id]
            
            if not gps_data:
                return {"error": "No GPS data in photo"}
            
            # Convert GPS coordinates to decimal degrees
            lat = self._convert_to_degrees(gps_data.get("GPSLatitude"))
            lon = self._convert_to_degrees(gps_data.get("GPSLongitude"))
            
            # Adjust for N/S and E/W
            if gps_data.get("GPSLatitudeRef") == "S":
                lat = -lat
            if gps_data.get("GPSLongitudeRef") == "W":
                lon = -lon
            
            return {
                "latitude": lat,
                "longitude": lon,
                "altitude": gps_data.get("GPSAltitude"),
                "timestamp": self._extract_timestamp(exif),
                "device": f"{exif.get(271)} {exif.get(272)}",  # Make + Model
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _convert_to_degrees(self, gps_coord):
        """Convert GPS coordinates to decimal degrees"""
        d, m, s = gps_coord
        return d + (m / 60.0) + (s / 3600.0)
    
    def validate_location(self, photo_coords, campaign_coords, max_distance_km=50):
        """Validate photo location is within acceptable radius"""
        from math import radians, cos, sin, asin, sqrt
        
        # Haversine formula
        lat1, lon1 = radians(photo_coords[0]), radians(photo_coords[1])
        lat2, lon2 = radians(campaign_coords[0]), radians(campaign_coords[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        distance_km = 6371 * c  # Earth radius in km
        
        return {
            "valid": distance_km <= max_distance_km,
            "distance_km": round(distance_km, 2)
        }
    
    def compute_photo_hash(self, image_path):
        """Generate perceptual hash for duplicate detection"""
        import imagehash
        
        image = Image.open(image_path)
        return str(imagehash.average_hash(image))
```

---

## Alternative: ExifRead Library

**Simpler approach for basic GPS extraction:**

```python
import exifread

def simple_gps_extract(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)
        
        gps_lat = tags.get('GPS GPSLatitude')
        gps_lon = tags.get('GPS GPSLongitude')
        gps_lat_ref = tags.get('GPS GPSLatitudeRef')
        gps_lon_ref = tags.get('GPS GPSLongitudeRef')
        
        if gps_lat and gps_lon:
            return {
                "latitude": convert_to_decimal(gps_lat, gps_lat_ref),
                "longitude": convert_to_decimal(gps_lon, gps_lon_ref),
                "datetime": str(tags.get('EXIF DateTimeOriginal')),
            }
    
    return None
```

---

## Security & Anti-Fraud Measures

### 1. Multi-Photo Requirement
- Require 2-3 photos from different angles
- GPS coordinates should be very close (within 100m)
- Timestamps should be within minutes of each other

### 2. Cross-Reference Checks
- IP geolocation of uploader vs GPS coordinates
- Upload device fingerprint
- Historical pattern analysis (has this user uploaded legitimate photos before?)

### 3. Manual Review Queue
- Admin dashboard for flagged photos
- Show side-by-side: GPS location on map + photo
- Approve/reject workflow

### 4. Blockchain Immutability
- Hash photo + GPS data + timestamp
- Store hash on Ethereum or IPFS
- Creates permanent audit trail
- Donors can verify authenticity

---

## Integration Points

### API Endpoint
```
POST /api/campaigns/{campaign_id}/impact-photos

FormData:
  - photo: File (image/jpeg, image/png)
  - caption: String (optional)
  - manual_lat: Float (optional, if GPS missing)
  - manual_lon: Float (optional, if GPS missing)

Response:
{
  "photo_id": "uuid",
  "gps_extracted": true,
  "latitude": -2.5164,
  "longitude": 32.9175,
  "validation_status": "approved",
  "distance_from_campaign_km": 4.2,
  "blockchain_hash": "0x8f3a...",
  "url": "https://cdn.trustvoice.com/photos/uuid.jpg"
}
```

### Telegram/WhatsApp Integration
```python
# When field officer sends photo via Telegram
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # 1. Download photo from Telegram servers
    photo = bot.download_file(message.photo[-1].file_id)
    
    # 2. Extract GPS
    gps_data = extract_gps_from_photo(photo)
    
    # 3. Validate against campaign location
    validation = validate_location(gps_data, campaign.location)
    
    # 4. Store in database + upload to S3
    # 5. Store hash on blockchain
    # 6. Notify donors
    
    bot.reply_to(message, f"✓ Photo verified! Location: {gps_data['latitude']}, {gps_data['longitude']}")
```

---

## Cost Considerations

**Storage Costs:**
- S3/R2: ~$0.023/GB/month
- Average photo: 2-5MB
- 1000 photos = 3GB = ~$0.07/month

**Blockchain Costs:**
- IPFS pinning: $0.15/GB/month (Pinata)
- Ethereum gas: $1-5 per transaction (can batch)
- Alternative: Use testnet initially, mainnet later

**Processing Costs:**
- EXIF extraction: Near-zero (server CPU)
- Image hashing: ~1ms per image
- Validation: Negligible

---

## Privacy Considerations

**Field Officer Privacy:**
- Strip personal EXIF data (except GPS/timestamp)
- Remove camera serial numbers
- Anonymize device identifiers

**Beneficiary Privacy:**
- Blur faces if requested
- Don't show exact home addresses
- Show region-level GPS (e.g., "Mwanza District" not exact coordinates)

---

## Recommended Packages

```bash
# Python dependencies
pip install Pillow              # Image processing
pip install piexif              # EXIF manipulation
pip install GPSPhoto            # GPS-specific extraction
pip install exifread            # Alternative EXIF reader
pip install imagehash           # Perceptual hashing
pip install geopy               # Distance calculations

# Optional
pip install python-telegram-bot # Telegram integration
pip install boto3               # AWS S3 storage
pip install web3                # Ethereum/blockchain
pip install ipfshttpclient      # IPFS storage
```

---

## Implementation Phases

### Phase 1: Basic GPS Extraction (Lab 6)
- Extract GPS from uploaded photos
- Store in database
- Display on campaign page
- Validation: proximity check

### Phase 2: Anti-Fraud (Lab 6)
- Duplicate detection via hashing
- Timestamp validation
- Manual review queue for flagged photos

### Phase 3: Blockchain Integration (Lab 6)
- Store photo hashes on IPFS
- Record proof on Ethereum
- Donor-facing verification

### Phase 4: Advanced Features (Future)
- Machine learning: Detect fake/manipulated photos
- Computer vision: Verify photo content matches project description
- Geofencing: Auto-approve if within tight radius

---

## Testing Strategy

**Unit Tests:**
- GPS extraction from sample photos
- Coordinate conversion accuracy
- Distance calculation validation
- Hash generation consistency

**Integration Tests:**
- Upload via API endpoint
- Telegram bot photo handling
- S3 storage integration
- Database persistence

**Manual Testing:**
- Test with real smartphones (iOS, Android)
- Photos with GPS enabled/disabled
- Various image formats (JPEG, PNG, HEIC)
- Edge cases: old photos, no EXIF, manipulated EXIF

---

## Troubleshooting

**Problem:** "No GPS data in photo"
- **Cause:** GPS disabled on phone, indoor photo, old device
- **Solution:** Fallback to browser geolocation or manual entry

**Problem:** "Photo location too far from campaign"
- **Cause:** Wrong GPS coordinates, phone GPS drift, different project site
- **Solution:** Manual review, allow NGO admin to override

**Problem:** "Duplicate photo detected"
- **Cause:** Same photo uploaded twice, stock photo used
- **Solution**: Reject duplicate, request new photo

**Problem:** "EXIF data stripped"
- **Cause:** WhatsApp/social media apps remove EXIF, privacy settings
- **Solution:** Direct upload via web/app instead of social media

---

## Success Metrics

**Adoption:**
- % of impact photos with valid GPS data
- Target: >80% success rate

**Trust:**
- % of donors viewing GPS-verified photos
- Donor feedback on transparency

**Fraud Prevention:**
- # of flagged photos caught
- False positive rate <5%

---

## References

- EXIF Standard: https://exiftool.org/TagNames/EXIF.html
- GPS Coordinate Formats: https://en.wikipedia.org/wiki/Geographic_coordinate_system
- Haversine Distance Formula: https://en.wikipedia.org/wiki/Haversine_formula
- IPFS Documentation: https://docs.ipfs.tech/
- Pillow EXIF Guide: https://pillow.readthedocs.io/

---

**Document Version:** 1.0  
**Last Updated:** December 22, 2025  
**Author:** TrustVoice Technical Team

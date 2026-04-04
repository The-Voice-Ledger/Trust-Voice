"""Upload Moringa Oasis media to Cloudflare R2."""
import boto3, os, mimetypes
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto",
)

bucket = os.getenv("R2_VIDEOS_BUCKET", "trustvoice")
public_url = os.getenv("R2_PUBLIC_URL", "").rstrip("/")
prefix = "oasis"

files = [
    "documentation/DroneView1.mp4",
    "documentation/DroneView2.mp4",
    "documentation/GroundView.mp4",
    "documentation/FarmNew1.jpeg",
    "documentation/Oasis1.jpeg",
    "documentation/Oasis2.jpeg",
    "documentation/Oasis3.jpeg",
    "documentation/Oasis4.jpeg",
    "documentation/Oasis5.jpeg",
    "documentation/Oasis6.jpeg",
    "documentation/MorinaGreen.jpeg",
    "documentation/murrrphoto-vineyards-5943255.jpg",
]

for f in files:
    fname = os.path.basename(f)
    key = f"{prefix}/{fname}"
    ct, _ = mimetypes.guess_type(f)
    ct = ct or "application/octet-stream"
    size_mb = os.path.getsize(f) / (1024 * 1024)
    print(f"Uploading {fname} ({size_mb:.1f} MB) -> {key} ...", flush=True)
    s3.upload_file(
        f, bucket, key,
        ExtraArgs={"ContentType": ct, "CacheControl": "public, max-age=31536000"},
    )
    print(f"  OK  {public_url}/{key}")

print("\nAll uploads complete!")

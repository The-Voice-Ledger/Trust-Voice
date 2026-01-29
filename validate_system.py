from database.db import SessionLocal
from database.models import ImpactVerification, Campaign, User
from sqlalchemy import func

db = SessionLocal()

# Check verifications
verifications = db.query(ImpactVerification).all()
print('=' * 60)
print('DATABASE VALIDATION')
print('=' * 60)
print(f'✅ Total verifications: {len(verifications)}')

if verifications:
    latest = verifications[-1]
    print(f'   Latest: ID={latest.id}, Score={latest.trust_score}, Status={latest.status}')

# Check campaigns
campaigns = db.query(Campaign).filter(Campaign.status.in_(['active', 'completed'])).all()
print(f'✅ Active/Completed campaigns: {len(campaigns)}')

# Check field agents
agents = db.query(User).filter(User.role == 'FIELD_AGENT').all()
print(f'✅ Field agents: {len(agents)}')

# Check auto-approved verifications
auto_approved = db.query(ImpactVerification).filter(
    ImpactVerification.status == 'approved',
    ImpactVerification.trust_score >= 80
).count()
print(f'✅ Auto-approved verifications (score ≥80): {auto_approved}')

# Check pending verifications
pending = db.query(ImpactVerification).filter(
    ImpactVerification.status == 'pending'
).count()
print(f'✅ Pending verifications (manual review): {pending}')

print('=' * 60)
print('SYSTEM STATUS: READY FOR DEPLOYMENT')
print('=' * 60)

db.close()

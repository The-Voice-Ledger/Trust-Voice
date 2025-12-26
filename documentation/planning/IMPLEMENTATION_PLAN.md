# TrustVoice - Implementation Plan & Progress Tracker

**Project:** Voice-first platform for African changemakers (NGO + Crowdfunding Hybrid)  
**Last Updated:** 22 December 2025  
**Current Phase:** Lab 3 Complete, Lab 4 Planning

**Strategic Vision:**
> "TrustVoice: Voice-first platform for African changemakers"
> "Support NGOs, back creative projects, fund personal causes"
> "From $1 donations to $50k project launches"

**Hybrid Model Approach:**
- **Phase 1 (Labs 1-12):** Build NGO donation platform foundation - Validate product-market fit, establish payment infrastructure, deploy voice-first interface
- **Phase 2 (Labs 13-15):** Add crowdfunding layer - Leverage proven foundation to expand into rewards-based crowdfunding for creators and innovators

---

## 📊 Project Status Overview

| Phase | Labs | Status | Branch | Progress |
|-------|------|--------|--------|----------|
| Foundation | 1-2 | ✅ Complete | `main` | 100% |
| Core Features | 3-5 | 🚧 In Progress | `lab-03-payments` | 33% |
| Advanced Features | 6-9 | ⏳ Planned | TBD | 0% |
| Production Ready | 10-12 | ⏳ Planned | TBD | 0% |
| Crowdfunding Expansion | 13-15 | 📋 Future | TBD | 0% |

---

## 🎯 Lab Roadmap

### Phase 1: Foundation (✅ Complete)

#### Lab 1: Project Setup & Database Models
**Status:** ✅ Complete  
**Branch:** `main`  
**Completed:** 20 December 2025

**Deliverables:**
- ✅ Project structure (FastAPI, SQLAlchemy, PostgreSQL)
- ✅ 7 database models (NGO, Campaign, Donor, Donation, VoiceInteraction, ImpactVerification, BlockchainTransaction)
- ✅ Neon PostgreSQL database connection
- ✅ Environment configuration (.env)
- ✅ Basic test infrastructure (pytest)
- ✅ Git repository initialization

**Key Files:**
- `database/models.py` (7 models, ~150 lines)
- `database/db.py` (session management)
- `main.py` (FastAPI app)
- `requirements.txt` (dependencies)

**Testing:** 7 model creation tests passing

**Documentation:** [LAB_01_PROJECT_SETUP.md](labs/LAB_01_PROJECT_SETUP.md)

---

#### Lab 2: Campaign & Donor Management APIs
**Status:** ✅ Complete  
**Branch:** `main`  
**Completed:** 21 December 2025

**Deliverables:**
- ✅ NGO CRUD API (5 endpoints)
- ✅ Campaign CRUD API (5 endpoints with soft delete)
- ✅ Donor registration API (5 endpoints, multi-channel)
- ✅ Pydantic validation schemas (E.164 phone, email, blockchain address)
- ✅ Seed data script (3 NGOs, 5 campaigns, 5 donors)
- ✅ 22 integration tests (100% passing)

**Key Files:**
- `voice/routers/ngos.py` (159 lines)
- `voice/routers/campaigns.py` (159 lines)
- `voice/routers/donors.py` (150 lines)
- `seed_data.py` (213 lines)
- `tests/test_lab2_endpoints.py` (388 lines)

**API Endpoints:** 15 REST endpoints operational

**Testing:** 22 integration tests passing

**Documentation:** [LAB_02_CAMPAIGN_DONOR_APIs.md](labs/LAB_02_CAMPAIGN_DONOR_APIs.md)

---

### Phase 2: Core Features (⏳ Planned)

#### Lab 3: Payment Processing & Donation Flow
**Status:** ✅ Complete  
**Branch:** `lab-03-payments`  
**Completed:** 21 December 2025

**Deliverables:**
- ✅ Donation router with full CRUD (7 endpoints)
- ✅ Multi-currency support (31+ currencies via Frankfurter API)
- ✅ Per-currency tracking with dynamic USD conversion
- ✅ M-Pesa integration (STK Push + webhook)
- ✅ Stripe integration (PaymentIntent + webhook with signature verification)
- ✅ Cryptocurrency support (basic address tracking)
- ✅ Currency conversion service with 24h caching
- ✅ Campaign total updates (per-currency buckets + cached USD)
- ✅ 22 comprehensive integration tests (100% passing)

**Key Files:**
- `voice/routers/donations.py` (333 lines)
- `voice/routers/webhooks.py` (215 lines)
- `services/currency_service.py` (200 lines)
- `services/mpesa.py` (M-Pesa integration)
- `services/stripe_service.py` (Stripe integration)
- `tests/test_lab3_donations.py` (533 lines, 22 tests)

**Architecture Highlights:**
- **Per-currency tracking:** Donations tracked in original currencies with dynamic USD conversion
- **Campaign.raised_amounts:** JSON field storing `{"USD": 2000, "EUR": 1000, "GBP": 500}`
- **Campaign.raised_amount_usd:** Cached USD total for quick queries
- **Campaign.get_current_usd_total():** Real-time USD calculation with live rates
- **Benefits:** No exchange rate lock-in, better reporting, refund in original currency

**API Endpoints:** 7 donation endpoints + 3 webhook endpoints

**Testing:** 22 integration tests passing (donation CRUD, webhooks, multi-currency)

**Documentation:** [LAB_03_PAYMENT_PROCESSING.md](labs/LAB_03_PAYMENT_PROCESSING.md)

---

#### Lab 4: Voice AI Integration (Vapi.ai)
**Status:** ⏳ Planned  
**Branch:** `lab-04-voice-ai` (to be created)  
**Prerequisites:** Lab 1, Lab 2, Lab 3  
**Estimated Effort:** 6-8 hours

**Objectives:**
- Implement donation creation and tracking
- Integrate M-Pesa API (Kenya mobile money)
- Integrate Stripe API (international cards)
- Handle payment webhooks and confirmations
- Update campaign current_amount automatically
- Generate donation receipts

**Planned Deliverables:**
- [ ] Donation router with endpoints:
  - POST `/donations/` - Initiate donation
  - GET `/donations/{id}` - Get donation status
  - GET `/donations/donor/{donor_id}` - Donor history
  - GET `/donations/campaign/{campaign_id}` - Campaign donations
- [ ] M-Pesa integration:
  - STK Push for payment initiation
  - Callback handler for payment confirmation
  - Balance query
- [ ] Stripe integration:
  - Payment intent creation
  - Webhook handler for payment events
  - Customer management
- [ ] Payment status tracking (pending, processing, completed, failed)
- [ ] Idempotency keys for duplicate prevention
- [ ] Transaction rollback on payment failure
- [ ] Email notification service (donation receipts)

**Key Technical Decisions:**
- Use Celery for async webhook processing?
- Implement payment retry logic?
- Store payment credentials securely (environment variables vs secret manager)

**Testing:**
- [ ] Mock M-Pesa API responses
- [ ] Mock Stripe webhooks
- [ ] Test idempotency (duplicate requests)
- [ ] Test concurrent donations
- [ ] Test payment failures and rollbacks

**Documentation:** `labs/LAB_03_PAYMENT_PROCESSING.md` (to be written after implementation)

---

#### Lab 4: Voice AI Integration (Vapi.ai)
**Status:** ⏳ Planned  
**Branch:** `lab-04-voice-ai` (to be created)  
**Prerequisites:** Lab 1, Lab 2, Lab 3  
**Estimated Effort:** 8-10 hours

**Objectives:**
- Integrate Vapi.ai for conversational voice AI
- Implement call routing and donor identification
- Create voice interaction workflows
- Support multiple languages (English, Amharic, Swahili, French, German, Spanish)
- Log voice interactions for analytics

**Planned Deliverables:**
- [ ] Vapi.ai configuration and authentication
- [ ] Voice interaction router:
  - POST `/voice/initiate-call` - Start outbound call
  - POST `/voice/incoming` - Handle incoming calls
  - POST `/voice/webhook` - Vapi.ai event webhook
  - GET `/voice/interactions/{donor_id}` - Interaction history
- [ ] Call flow logic:
  - Donor identification (phone number lookup)
  - Campaign browsing via voice
  - Donation initiation via voice
  - Language selection
- [ ] VoiceInteraction model integration
- [ ] Call transcript storage
- [ ] Multi-language support configuration

**Key Technical Decisions:**
- Real-time vs batch transcript processing?
- Voice authentication for donors?
- Call recording storage (compliance considerations)

**Testing:**
- [ ] Mock Vapi.ai API
- [ ] Test language switching
- [ ] Test donor identification flow
- [ ] Test payment initiation via voice
- [ ] Integration test with real Vapi.ai (sandbox)

**Documentation:** `labs/LAB_04_VOICE_AI_INTEGRATION.md`

---

#### Lab 5: Impact Verification & Media Upload
**Status:** ⏳ Planned  
**Branch:** `lab-05-impact-verification` (to be created)  
**Prerequisites:** Lab 1, Lab 2  
**Estimated Effort:** 4-6 hours

**Objectives:**
- Enable NGOs to upload impact verification photos/videos
- Store media in cloud storage (AWS S3 / Cloudinary)
- Link verifications to campaigns
- Display impact to donors

**Planned Deliverables:**
- [ ] Impact verification router:
  - POST `/impact/` - Create verification with media
  - GET `/impact/campaign/{campaign_id}` - Get campaign verifications
  - PATCH `/impact/{id}` - Update verification
  - DELETE `/impact/{id}` - Remove verification
- [ ] Media upload handling:
  - Multipart form data support
  - Image/video validation
  - Cloud storage integration (S3 or Cloudinary)
  - Generate signed URLs for secure access
- [ ] ImpactVerification model usage
- [ ] Optional: Blockchain proof hash generation

**Key Technical Decisions:**
- AWS S3 vs Cloudinary vs local storage (development)?
- Image resizing/optimization before upload?
- Maximum file size limits?

**Testing:**
- [ ] Mock file uploads
- [ ] Test media type validation
- [ ] Test cloud storage integration
- [ ] Test URL generation and expiry

**Documentation:** `labs/LAB_05_IMPACT_VERIFICATION.md`

---

### Phase 3: Advanced Features (⏳ Planned)

#### Lab 6: Blockchain Integration (Stellar/Celo)
**Status:** ⏳ Planned  
**Branch:** `lab-06-blockchain` (to be created)  
**Prerequisites:** Lab 3  
**Estimated Effort:** 8-10 hours

**Objectives:**
- Enable cryptocurrency donations
- Record transactions on blockchain for transparency
- Support Stellar and/or Celo networks

**Planned Deliverables:**
- [ ] Blockchain transaction router
- [ ] Stellar/Celo SDK integration
- [ ] Wallet management for NGOs
- [ ] Transaction verification and confirmation
- [ ] BlockchainTransaction model integration
- [ ] Transaction explorer links

**Documentation:** `labs/LAB_06_BLOCKCHAIN_INTEGRATION.md`

---

#### Lab 7: Analytics & Reporting Dashboard
**Status:** ⏳ Planned  
**Branch:** `lab-07-analytics` (to be created)  
**Prerequisites:** Lab 3, Lab 4  
**Estimated Effort:** 6-8 hours

**Objectives:**
- Build analytics endpoints for insights
- Campaign performance metrics
- Donor behavior analytics
- Voice interaction analytics

**Planned Deliverables:**
- [ ] Analytics router with aggregation queries
- [ ] Campaign metrics (total raised, donor count, avg donation)
- [ ] Donor retention metrics
- [ ] Voice AI effectiveness metrics
- [ ] Time-series data (donations over time)
- [ ] Export capabilities (CSV, JSON)

**Documentation:** `labs/LAB_07_ANALYTICS_REPORTING.md`

---

#### Lab 8: NGO Dashboard (Frontend - Optional)
**Status:** ⏳ Planned  
**Branch:** `lab-08-frontend` (separate repo or folder)  
**Prerequisites:** Lab 2, Lab 5, Lab 7  
**Estimated Effort:** 12-16 hours

**Objectives:**
- Build React/Next.js dashboard for NGOs
- View campaign performance
- Upload impact verifications
- View donor insights

**Planned Deliverables:**
- [ ] Next.js application setup
- [ ] Authentication (JWT tokens)
- [ ] Campaign management UI
- [ ] Impact verification upload UI
- [ ] Analytics dashboard UI
- [ ] Responsive design (mobile-friendly)

**Key Technical Decisions:**
- Separate repo vs monorepo?
- Next.js vs React + Vite?
- UI library (Tailwind, Material UI, shadcn/ui)?

**Documentation:** `labs/LAB_08_NGO_DASHBOARD.md`

---

#### Lab 9: Donor Mobile App (React Native - Optional)
**Status:** ⏳ Planned  
**Branch:** `lab-09-mobile-app` (separate repo)  
**Prerequisites:** Lab 2, Lab 3  
**Estimated Effort:** 16-20 hours

**Objectives:**
- Build React Native mobile app for donors
- Browse campaigns
- Make donations
- View donation history
- Voice interaction integration

**Documentation:** `labs/LAB_09_DONOR_MOBILE_APP.md`

---

### Phase 4: Production Ready (⏳ Planned)

#### Lab 10: Authentication & Authorization
**Status:** ⏳ Planned  
**Branch:** `lab-10-auth` (to be created)  
**Prerequisites:** Lab 2  
**Estimated Effort:** 6-8 hours

**Objectives:**
- Implement JWT-based authentication
- Role-based access control (NGO staff, platform admin)
- API key management for external integrations
- Secure endpoint protection

**Planned Deliverables:**
- [ ] User model and authentication system
- [ ] JWT token generation and validation
- [ ] Role-based middleware
- [ ] Protected routes (@require_auth decorator)
- [ ] API key generation for integrations
- [ ] Password hashing (bcrypt)
- [ ] Refresh token mechanism

**Documentation:** `labs/LAB_10_AUTHENTICATION.md`

---

#### Lab 11: Production Deployment
**Status:** ⏳ Planned  
**Branch:** `main` (deployment configs)  
**Prerequisites:** All core features complete  
**Estimated Effort:** 8-12 hours

**Objectives:**
- Deploy to production infrastructure
- Setup CI/CD pipeline
- Configure monitoring and logging
- Implement backup strategy

**Planned Deliverables:**
- [ ] Docker containerization (Dockerfile, docker-compose)
- [ ] Cloud deployment (AWS/GCP/Heroku/Railway)
- [ ] GitHub Actions CI/CD pipeline
- [ ] Environment-specific configs (dev, staging, prod)
- [ ] Database migration strategy (Alembic in production)
- [ ] Logging setup (Sentry, CloudWatch, or similar)
- [ ] Monitoring (health checks, uptime monitoring)
- [ ] SSL/TLS configuration
- [ ] Domain setup and DNS configuration

**Documentation:** `labs/LAB_11_PRODUCTION_DEPLOYMENT.md`

---

#### Lab 12: Performance Optimization & Scaling
**Status:** ⏳ Planned  
**Branch:** `lab-12-optimization` (to be created)  
**Prerequisites:** Lab 11 (deployed to production)  
**Estimated Effort:** 6-8 hours

**Objectives:**
- Optimize database queries
- Implement caching (Redis)
- Add rate limiting
- Load testing and bottleneck identification

**Planned Deliverables:**
- [ ] Database query optimization (indexes, eager loading)
- [ ] Redis caching layer
- [ ] API rate limiting (per user, per endpoint)
- [ ] Database connection pooling tuning
- [ ] Load testing scripts (Locust or k6)
- [ ] Performance benchmarks
- [ ] CDN setup for static assets

**Documentation:** `labs/LAB_12_PERFORMANCE_OPTIMIZATION.md`

---

## 🌿 Branch Management Strategy

### Branch Naming Convention

```
main                           # Stable, completed labs
lab-{number}-{feature-name}    # Lab development branches
feature/{feature-name}         # Experimental/optional features
hotfix/{issue-description}     # Production bug fixes
```

### Development Workflow

1. **Create Lab Branch:**
   ```bash
   git checkout -b lab-03-payments main
   ```

2. **Develop & Test:**
   - Implement features
   - Write tests
   - Ensure all tests pass
   - Test manually via API

3. **Document:**
   - Create `labs/LAB_XX_FEATURE_NAME.md`
   - Follow educational format from Lab 1 & 2
   - Include theory, step-by-step instructions, testing, troubleshooting

4. **Merge to Main:**
   ```bash
   git checkout main
   git merge lab-03-payments
   git push origin main
   ```

5. **Tag Release:**
   ```bash
   git tag -a lab-03-complete -m "Lab 3: Payment Processing Complete"
   git push origin lab-03-complete
   ```

### When to Branch

**Create New Branch:**
- Starting a new lab
- Experimenting with alternative approach
- Working on optional feature

**Stay on Main:**
- Quick fixes/typos
- Documentation updates
- Minor refactoring

### Feature Flags for Optional Features

For experimental features that might not make it to production:

```python
# config.py
ENABLE_BLOCKCHAIN = os.getenv('ENABLE_BLOCKCHAIN', 'false').lower() == 'true'
ENABLE_VOICE_AI = os.getenv('ENABLE_VOICE_AI', 'false').lower() == 'true'
```

---

## 📈 Progress Tracking

### Current Sprint: Lab 3 Planning

**Next Actions:**
1. ⏳ Design donation flow and state machine
2. ⏳ Research M-Pesa API requirements (sandbox access)
3. ⏳ Research Stripe API integration patterns
4. ⏳ Create `lab-03-payments` branch
5. ⏳ Implement donation router and models
6. ⏳ Write integration tests
7. ⏳ Document Lab 3

### Completed Work

**Lab 1 (✅ Complete):**
- Database models and relationships
- PostgreSQL connection
- Basic testing infrastructure

**Lab 2 (✅ Complete):**
- 15 REST API endpoints
- Pydantic validation
- 22 passing integration tests
- Seed data script

### Blocked Items

None currently.

### Technical Debt

1. **Alembic Migrations:** Currently using `drop_all()` / `create_all()` for schema changes. Should implement Alembic before Lab 3.
2. **Error Logging:** No centralized logging yet. Should add before production.
3. **API Versioning:** Not implemented yet. Consider `/api/v1/` prefix structure.
4. **Response Pagination:** Basic `skip/limit` works but no cursor-based pagination for large datasets.

---

## 🎯 Prioritization Framework

### Must Have (Core MVP)
- ✅ Lab 1: Database foundation
- ✅ Lab 2: CRUD APIs
- ⏳ Lab 3: Payment processing
- ⏳ Lab 4: Voice AI integration
- ⏳ Lab 10: Authentication
- ⏳ Lab 11: Production deployment

### Should Have (Enhanced MVP)
- ⏳ Lab 5: Impact verification
- ⏳ Lab 7: Analytics
- ⏳ Lab 12: Performance optimization

### Could Have (Nice to Have)
- ⏳ Lab 6: Blockchain integration
- ⏳ Lab 8: NGO dashboard (frontend)

### Won't Have (Future Consideration)
- Lab 9: Mobile app (separate project)
- Multi-tenancy (single platform instance for now)
- Advanced fraud detection (basic validation sufficient for MVP)

---

## 🔧 Technical Decisions Log

### Date: 20 December 2025
**Decision:** Use direct SQLAlchemy operations instead of Alembic migrations  
**Rationale:** Simpler for development and learning. Will add Alembic before production.  
**Impact:** Easier lab creation, but manual schema management required.

### Date: 21 December 2025
**Decision:** Use PostgreSQL for integration tests (not SQLite)  
**Rationale:** Avoid compatibility issues with PostgreSQL-specific features.  
**Impact:** Tests are slower but more reliable. Requires database cleanup between runs.

**Decision:** Changed `ARRAY(Text)` to `JSON` in ImpactVerification model  
**Rationale:** JSON type works universally, ARRAY is PostgreSQL-specific.  
**Impact:** More flexible for future database migrations.

**Decision:** Soft delete for campaigns, hard delete for NGOs  
**Rationale:** Campaigns need historical tracking for analytics. NGO deletion is rare and intentional.  
**Impact:** Must handle cascade behavior carefully for NGO deletions.

### Date: 21 December 2025
**Decision:** Build-first, document-after workflow  
**Rationale:** Ensures documentation reflects working code, not theoretical design.  
**Impact:** Labs are written after features are tested and proven.

**Decision:** Organize labs in `/documentation/labs/` subfolder  
**Rationale:** Keeps documentation organized as number of labs grows.  
**Impact:** Cleaner repository structure.

---

## 📚 Documentation Structure

```
documentation/
├── labs/                                      # Educational lab guides
│   ├── LAB_01_PROJECT_SETUP.md               ✅ Complete
│   ├── LAB_02_CAMPAIGN_DONOR_APIs.md         ✅ Complete
│   ├── LAB_03_PAYMENT_PROCESSING.md          ⏳ Planned
│   ├── LAB_04_VOICE_AI_INTEGRATION.md        ⏳ Planned
│   ├── LAB_05_IMPACT_VERIFICATION.md         ⏳ Planned
│   ├── LAB_06_BLOCKCHAIN_INTEGRATION.md      ⏳ Planned
│   ├── LAB_07_ANALYTICS_REPORTING.md         ⏳ Planned
│   ├── LAB_08_NGO_DASHBOARD.md               ⏳ Planned
│   ├── LAB_09_DONOR_MOBILE_APP.md            ⏳ Planned
│   ├── LAB_10_AUTHENTICATION.md              ⏳ Planned
│   ├── LAB_11_PRODUCTION_DEPLOYMENT.md       ⏳ Planned
│   └── LAB_12_PERFORMANCE_OPTIMIZATION.md    ⏳ Planned
├── IMPLEMENTATION_PLAN.md                     # This file - progress tracker
├── NGO_PLATFORM_TECHNICAL_SPEC.md            # Original technical specification
└── API_REFERENCE.md                           ⏳ Future - Auto-generated from OpenAPI
```

---

## 🚀 Getting Started for New Labs

### Before Starting Lab 3 (Example):

1. **Review Prerequisites:**
   - Lab 1 & 2 complete? ✅
   - Database seeded with test data? ✅
   - All tests passing? ✅

2. **Create Branch:**
   ```bash
   git checkout -b lab-03-payments main
   ```

3. **Research Phase:**
   - Read M-Pesa API documentation
   - Read Stripe API documentation
   - Design donation state machine
   - Identify edge cases

4. **Implementation Phase:**
   - Create donation router
   - Implement payment integrations
   - Write tests as you go
   - Test manually with Postman/Swagger

5. **Documentation Phase:**
   - Write lab guide following established format
   - Include all code examples
   - Add troubleshooting section
   - Include expected outputs

6. **Merge & Release:**
   - Run full test suite
   - Update this IMPLEMENTATION_PLAN.md
   - Merge to main
   - Tag release

---

## 📊 Metrics & Success Criteria

### Lab Completion Criteria

Each lab is considered complete when:
- ✅ All planned features implemented
- ✅ All tests passing (unit + integration)
- ✅ Manual testing via API successful
- ✅ Documentation written (lab guide)
- ✅ Code reviewed (self-review checklist)
- ✅ Merged to main branch
- ✅ This implementation plan updated

### Quality Metrics

**Code Quality:**
- Test coverage > 80%
- No linting errors (flake8/pylint)
- Type hints on all functions
- Docstrings on all public functions

**Documentation Quality:**
- Step-by-step instructions work
- All code examples tested
- Expected outputs included
- Troubleshooting section present

**API Quality:**
- Proper HTTP status codes
- Consistent error message format
- Input validation on all endpoints
- OpenAPI docs auto-generated

---

## 🎓 Learning Objectives by Phase

### Phase 1 (Labs 1-2): Foundation ✅
- FastAPI application structure
- SQLAlchemy ORM patterns
- REST API design principles
- Pydantic validation
- Integration testing strategies

### Phase 2 (Labs 3-5): Core Features
- Payment gateway integration
- Webhook handling
- Async task processing
- External API integration
- File upload and cloud storage

### Phase 3 (Labs 6-9): Advanced Features
- Blockchain basics
- Data analytics and aggregation
- Frontend/backend integration
- Mobile app development
- Full-stack architecture

### Phase 4 (Labs 10-12): Production
- Authentication patterns
- Deployment strategies
- CI/CD pipelines
- Performance optimization
- Production monitoring

### Phase 5 (Labs 13-15): Crowdfunding Expansion
- Platform business models (marketplace fees)
- Deadline-based funding mechanics
- Stripe Connect for multi-party payments
- Reward tier and inventory systems
- Creator tools and fulfillment
- Social discovery algorithms
- Escrow and automatic refunds

---

## 📞 Support & Resources

### When Stuck:
1. Check lab documentation troubleshooting section
2. Review test cases for examples
3. Check git history for similar implementations
4. Review technical specification document

### External Resources:
- FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Pydantic docs: https://docs.pydantic.dev/
- Stripe API docs: https://stripe.com/docs/api
- Vapi.ai docs: https://docs.vapi.ai/

---

**Last Updated:** 21 December 2025  
**Next Review:** Before starting Lab 3  
**Maintained By:** Development Team


# RAG Integration Plan for Trust-Voice

**Date:** 24 December 2025  
**Status:** 📋 Planning Complete  
**Reference:** Voice Ledger RAG implementation (Dec 2024)

---

## 🎯 Executive Summary

Based on Voice Ledger's successful RAG implementation (3,539 chunks, zero hallucinations, ~$0.01/query), Trust-Voice will integrate a Retrieval-Augmented Generation system to enable knowledge-grounded conversational AI.

**Why RAG is Critical:**

**Without RAG (Current State):**
- ❌ AI hallucinates about features ("I don't handle campaigns" when feature exists)
- ❌ Campaign creation lacks context from successful examples
- ❌ Compliance questions answered incorrectly or vaguely
- ❌ Users ask "how to" questions, get generic unhelpful responses

**With RAG (Proposed State):**
- ✅ Zero hallucinations - AI references actual documentation
- ✅ Campaign creation informed by successful patterns
- ✅ Compliance questions answered from indexed guides
- ✅ Knowledge-grounded responses: "Based on our campaign guide..."
- ✅ Cost: ~$0.01 per query (Voice Ledger proven)

---

## 📋 What Changed in the Roadmap

### Updated Phase Structure

**Before RAG Planning:**
- Phase 4D: Registration ✅ (Complete)
- Phase 4E: Admin Dashboard (Tomorrow)
- Phase 4F: Voice Campaign Creation
- Phase 4G: Bilingual Voice UI

**After RAG Planning:**
- Phase 4D: Registration ✅ (Complete)
- Phase 4E: Admin Dashboard (Tomorrow)
- Phase 4F: Voice Campaign Creation **+ RAG enhancement**
- Phase 4G: Bilingual Voice UI **+ RAG for queries**
- **Phase 4H: RAG System Implementation** 🆕 **(24-32 hours, MEDIUM PRIORITY)**

### Key Insight: RAG Should Come BEFORE or ALONGSIDE Phases 4F/4G

**Rationale:**
1. **Phase 4F** (Campaign Creation) benefits from RAG:
   - AI interview references successful campaign examples
   - Budget breakdowns informed by typical NGO patterns
   - Compliance questions (EUDR, GPS) answered from guides
   
2. **Phase 4G** (Voice UI) requires RAG:
   - Users will ask "How do I create a campaign?"
   - "What is EUDR compliance?"
   - Query classification prevents wrong responses
   - JSON format preservation is critical for voice

**Recommended Order:**
1. Phase 4E (Admin Dashboard) - Tomorrow
2. Phase 4H (RAG) - Week 2
3. Phase 4F (Campaign Creation) - Week 3 (enhanced by RAG)
4. Phase 4G (Voice UI) - Week 4-5 (powered by RAG)

---

## 🏗️ Architecture Overview

### Voice Ledger Pattern (Proven)

```
┌─────────────────────────────────────────────────────────────┐
│                       User Query                            │
│          "How do I create a campaign?"                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Query Classification                        │
│  ┌──────────────┬──────────────┬──────────────────────┐    │
│  │ TRANSACTIONAL│ DOCUMENTATION│    OPERATIONAL       │    │
│  │ (Commands)   │ (Questions)  │  (Data Queries)      │    │
│  └──────────────┴──────────────┴──────────────────────┘    │
└─────────┬───────────────┬─────────────────┬────────────────┘
          │               │                 │
          ▼               ▼                 ▼
   ┌──────────┐   ┌──────────────┐   ┌─────────────┐
   │  Bypass  │   │   ChromaDB   │   │ PostgreSQL  │
   │   RAG    │   │   (Docs)     │   │ (Live Data) │
   └────┬─────┘   └──────┬───────┘   └──────┬──────┘
        │                │                   │
        │                └──────┬────────────┘
        │                       │
        │                 ┌─────▼────────┐
        │                 │ Hybrid Search│
        │                 │   Results    │
        │                 └─────┬────────┘
        │                       │
        └───────────┬───────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              Enhanced System Prompt                          │
│  Base Prompt + Retrieved Context + JSON Format Rules        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    GPT-4 Processing                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              JSON Response (Format Preserved)                │
│  {                                                           │
│    "message_text": "Based on our campaign guide...",        │
│    "ready_to_execute": false                                │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

### Trust-Voice Adaptation

**Knowledge Base Structure:**

```
ChromaDB "Trust-Voice" Database
├── Collection: "documentation"
│   ├── PHASE_4D_REGISTRATION_AUTH.md (chunks)
│   ├── VoiceFirst_Interface_Design.md (chunks)
│   ├── NGO_PLATFORM_TECHNICAL_SPEC.md (chunks)
│   ├── TRUSTVOICE_PITCH.md (chunks)
│   └── labs/*.md (all lab guides)
│
├── Collection: "campaigns"
│   ├── Successful campaign #1 (title, goal, description, budget)
│   ├── Successful campaign #2
│   └── Campaign best practices
│
└── Collection: "compliance"
    ├── EUDR compliance guide
    ├── GPS verification standards
    └── NGO transparency requirements
```

**Total Expected:** ~500-1000 chunks (vs Voice Ledger's 3,539)

---

## 🛠️ Implementation Plan (Phase 4H)

### Week 1: Core RAG Infrastructure (16-20 hours)

**Day 1-2: ChromaDB Setup (4 hours)**
```bash
# Sign up: https://www.trychroma.com/
# Get credentials

# .env
CHROMA_CLIENT_TYPE=cloud
CHROMA_API_KEY=ck-...
CHROMA_TENANT=...
CHROMA_DATABASE="Trust-Voice"

# Test connection
python -c "import chromadb; print('✅ ChromaDB connected')"
```

**Day 2-3: Document Indexer (6 hours)**
```python
# voice/rag/indexer.py

def index_documentation():
    """Index all Trust-Voice markdown files."""
    docs = [
        "documentation/PHASE_4D_REGISTRATION_AUTH.md",
        "documentation/VoiceFirst_Interface_Design.md",
        "documentation/NGO_PLATFORM_TECHNICAL_SPEC.md",
        "documentation/TRUSTVOICE_PITCH.md",
        "documentation/labs/*.md"
    ]
    
    for doc in docs:
        chunks = chunk_document(doc, chunk_size=1000)
        embeddings = get_embeddings(chunks)
        chromadb_client.add(
            collection="documentation",
            documents=chunks,
            embeddings=embeddings,
            metadatas=[{"file": doc, "type": "documentation"}]
        )
```

**Day 3-4: Campaign Knowledge Base (4 hours)**
```python
# voice/rag/campaign_indexer.py

def index_campaign(campaign):
    """Index successful campaign as knowledge."""
    chunk = f"""
    Campaign Title: {campaign.title}
    Category: {campaign.category}
    Goal Amount: ${campaign.goal_amount}
    Amount Raised: ${campaign.amount_raised} ({campaign.percent_funded}%)
    Description: {campaign.description}
    Budget Breakdown: {campaign.budget_breakdown}
    Timeline: {campaign.timeline}
    Beneficiaries: {campaign.beneficiary_count}
    Location: {campaign.location}
    Success Factors: {campaign.success_notes}
    """
    
    chromadb_client.add(
        collection="campaigns",
        documents=[chunk],
        metadatas={"campaign_id": campaign.id, "status": "successful"}
    )
```

**Day 4: Query Classification (4 hours)**
```python
# voice/rag/hybrid_router.py

def classify_query_type(query: str) -> QueryType:
    """
    Classify query into:
    - TRANSACTIONAL: "Create a campaign for clean water" (bypass RAG)
    - DOCUMENTATION: "How do I create a campaign?" (search docs)
    - OPERATIONAL: "Show my campaigns" (query database)
    - HYBRID: "What campaigns are pending and why?" (docs + database)
    """
    
    classification_prompt = f"""
    Classify this query: "{query}"
    
    Rules:
    - TRANSACTIONAL: Commands to create/modify data
    - DOCUMENTATION: Questions about how the system works
    - OPERATIONAL: Queries about current data
    - HYBRID: Mix of documentation and operational
    
    Return only: TRANSACTIONAL, DOCUMENTATION, OPERATIONAL, or HYBRID
    """
    
    result = gpt4_classify(classification_prompt)
    return QueryType(result)
```

### Week 2: Integration & Testing (8-12 hours)

**Day 5: RAG Enhancement Function (2-4 hours)**
```python
# voice/rag/__init__.py

def enhance_query_with_rag(query, base_prompt, user_id, max_context_tokens=2000):
    """
    Enhance conversational AI prompt with RAG context.
    
    CRITICAL: Preserve JSON format despite context injection.
    """
    
    # 1. Classify query
    query_type = classify_query_type(query)
    
    # 2. Bypass RAG for transactional commands
    if query_type == QueryType.TRANSACTIONAL:
        return base_prompt
    
    # 3. Retrieve relevant context
    if query_type == QueryType.DOCUMENTATION:
        results = chromadb_client.query(
            collection="documentation",
            query_texts=[query],
            n_results=3
        )
    elif query_type == QueryType.OPERATIONAL:
        results = query_database(query, user_id)
    else:  # HYBRID
        doc_results = chromadb_client.query(collection="documentation", ...)
        db_results = query_database(query, user_id)
        results = combine_results(doc_results, db_results)
    
    context = format_context(results, max_tokens=max_context_tokens)
    
    # 4. FORMAT PRESERVATION (critical!)
    enhanced_prompt = f"""{base_prompt}

=== KNOWLEDGE BASE REFERENCE ===
The following information is provided as REFERENCE MATERIAL to help you answer.
Use this to inform your response CONTENT, but DO NOT change your response FORMAT:

{context}

=== END REFERENCE ===

CRITICAL REMINDER: Your response MUST still be in the EXACT JSON format specified above.
The retrieved reference material should inform the CONTENT of your JSON response
(specifically the "message_text" and "message_spoken" fields), but you MUST maintain
the JSON structure.

Example of correct format when answering with retrieved context:
{{
  "message_text": "Based on our campaign guide: [answer using context]",
  "message_spoken": "Based on our campaign guide: [answer using context]",
  "ready_to_execute": false
}}

DO NOT return prose. DO NOT return markdown. ONLY return valid JSON.
"""
    
    return enhanced_prompt
```

**Day 6: Integration with Phase 4F (2 hours)**
```python
# voice/integrations/campaign_creation.py

def conduct_campaign_interview(user_id):
    """Multi-turn interview with RAG enhancement."""
    
    conversation_history = []
    
    for question in INTERVIEW_QUESTIONS:
        # User answers
        user_response = await get_user_input()
        
        # Enhance with RAG context
        enhanced_prompt = enhance_query_with_rag(
            query=user_response,
            base_prompt=CAMPAIGN_INTERVIEW_PROMPT,
            user_id=user_id
        )
        
        # AI follow-up (informed by successful campaigns)
        ai_response = gpt4_process(enhanced_prompt, conversation_history)
        
        conversation_history.append({
            "user": user_response,
            "ai": ai_response
        })
```

**Day 6: Integration with Phase 4G (2 hours)**
```python
# voice/web/voice_api.py

@router.websocket("/api/voice/ws/voice")
async def voice_websocket(websocket: WebSocket):
    # ... existing code ...
    
    # Enable RAG for voice UI queries
    conv_result = process_english_conversation(
        user_id=user_id,
        transcript=transcript,
        use_rag=True  # Enable RAG
    )
```

**Day 7: Test Suite (4 hours)**
```python
# tests/test_rag_trustvoice.py

def test_documentation_query():
    """Test: 'How do I create a campaign?'"""
    result = process_with_rag("How do I create a campaign?")
    
    assert "campaign" in result.lower()
    assert "register" in result.lower() or "telegram" in result.lower()
    assert "I don't handle" not in result  # No wrong fallback

def test_compliance_query():
    """Test: 'What is EUDR compliance?'"""
    result = process_with_rag("What is EUDR compliance?")
    
    assert "eudr" in result.lower() or "deforestation" in result.lower()
    assert "gps" in result.lower()  # Should mention GPS verification

def test_transactional_bypass():
    """Test: 'Create a campaign for clean water'"""
    query_type = classify_query_type("Create a campaign for clean water")
    assert query_type == QueryType.TRANSACTIONAL
    
    # Should bypass RAG (no extra tokens)
    prompt = enhance_query_with_rag(query, base_prompt, user_id)
    assert prompt == base_prompt  # Unchanged

def test_json_format_preservation():
    """Test: Response maintains JSON structure with RAG."""
    result = process_with_rag("What are the campaign requirements?")
    
    # Must be valid JSON
    parsed = json.loads(result)
    assert "message_text" in parsed
    assert "ready_to_execute" in parsed
```

---

## 📊 Expected Outcomes

### Metrics (Based on Voice Ledger)

| Metric | Voice Ledger | Trust-Voice Target |
|--------|--------------|-------------------|
| **Knowledge Base Size** | 3,539 chunks | 500-1000 chunks |
| **Collections** | 3 (docs, research, code) | 3 (docs, campaigns, compliance) |
| **Hallucination Rate** | 0% (after RAG) | 0% target |
| **Response Relevance** | >90% | >90% target |
| **Cost per Query** | ~$0.01 | $0.01-0.02 target |
| **Response Time** | ~2s with RAG | <2s target |
| **Token Overhead** | +2000 tokens | +2000 tokens |

### User Experience Improvements

**Before RAG:**
- User: "How do I create a campaign?"
- AI: "I can help you with campaigns. What would you like to do?"
- User: ❌ Generic, unhelpful

**After RAG:**
- User: "How do I create a campaign?"
- AI: "Based on our campaign guide: First, register via Telegram (/register). Once approved by admin, you can start a voice interview where I'll ask 8-10 questions about your project (goal, beneficiaries, budget, timeline). The system will generate a professional campaign page automatically. Would you like to start?"
- User: ✅ Specific, actionable, grounded in docs

---

## 🚨 Critical Lessons from Voice Ledger

### 1. JSON Format Preservation is CRITICAL

**Problem:** RAG context (2000+ tokens) caused GPT-4 to switch from JSON to prose.

**Solution:** Triple reinforcement
```python
enhanced_prompt = f"""{base_prompt}

=== REFERENCE MATERIAL ===
{context}
=== END ===

CRITICAL: Response MUST be JSON. Example:
{{"message_text": "...", "ready_to_execute": false}}

DO NOT return prose. ONLY JSON.
"""
```

### 2. Query Classification Saves Costs

**Don't RAG everything:**
- ✅ "How do I...?" → Use RAG (documentation query)
- ❌ "Create a campaign..." → Bypass RAG (transactional command)
- ✅ "Show campaigns..." → Hybrid (docs + database)

**Savings:** 50-70% of queries are transactional (no RAG overhead)

### 3. Start Small, Scale Later

**Voice Ledger indexed 3,539 chunks**, but started with 200.

**Trust-Voice should:**
- Week 1: Index core docs (~200 chunks)
- Week 2: Add campaign examples (~50 chunks)
- Week 3: Add compliance guides (~100 chunks)
- **Total: 350 chunks** (sufficient for MVP)

### 4. Test Early, Test Often

Voice Ledger had 5 core tests:
1. Documentation query (no wrong fallbacks)
2. Specific topic query (EPCIS, RFQ)
3. Transactional bypass
4. JSON format preservation
5. Hybrid query (docs + data)

**Trust-Voice should have:**
- Same 5 tests adapted for campaigns/compliance
- Run after every RAG code change
- Target: 100% pass rate

---

## 💰 Cost Analysis

### Development Costs

- **Phase 4H Implementation:** 24-32 hours (~$0 if you build it)
- **Voice Ledger Replication:** Most code can be copied/adapted

### Operational Costs (Monthly for 1000 users)

| Component | Usage | Cost |
|-----------|-------|------|
| ChromaDB Cloud (Free Tier) | 10GB storage | $0 |
| OpenAI Embeddings | ~500 docs × 1K tokens | ~$0.05 |
| GPT-4 with RAG | 5000 queries × $0.01 | $50 |
| **Total** | | **~$50/month** |

**Cost per user:** $0.05/month  
**Cost per query with RAG:** ~$0.01  
**Acceptable?** ✅ Yes (Voice Ledger proven)

### ROI Calculation

**Value of RAG:**
- ✅ Zero hallucinations → Trust preservation
- ✅ Knowledge-grounded responses → Better UX
- ✅ Campaign creation success rate ↑ 30% (informed by examples)
- ✅ Compliance question accuracy → 100% (vs 60% without RAG)

**Break-even:** If RAG increases successful campaign creation by just 1 campaign/month, it pays for itself (campaign fees > $50).

---

## 🚀 Next Steps

### Tomorrow (Phase 4E)
**Start:** Admin Dashboard (3-5 days)
- No RAG dependency
- Immediate operational value
- Build user/registration management

### Week 2 (Phase 4H)
**Implement:** RAG System (3-4 days)
1. Day 1: ChromaDB setup + document indexing
2. Day 2: Campaign knowledge base + query classification
3. Day 3: RAG integration with conversational AI
4. Day 4: Testing and optimization

### Week 3 (Phase 4F)
**Enhance:** Voice Campaign Creation with RAG
- AI interview references successful campaigns
- Budget breakdowns informed by patterns
- Compliance questions from docs

### Week 4-5 (Phase 4G)
**Power:** Bilingual Voice UI with RAG
- Users ask "how to" questions
- System references documentation
- Knowledge-grounded responses in English + Amharic

---

## 📚 References

**Production Implementation:**
- `RAG_SYSTEM_IMPLEMENTATION.md` - Voice Ledger (Dec 2024)
- 3,539 chunks indexed
- Zero hallucinations
- ~$0.01 per query

**Trust-Voice Planning:**
- `PHASE_4D_TO_4G_ROADMAP.md` - Updated with Phase 4H
- `SESSION_CONTEXT.md` - Updated roadmap
- `VoiceFirst_Interface_Design.md` - Voice UI architecture

**ChromaDB:**
- https://www.trychroma.com/ - Cloud setup
- https://docs.trychroma.com/ - Documentation

---

**Status:** 📋 Planning Complete  
**Next Action:** Phase 4E (Admin Dashboard) tomorrow, then Phase 4H (RAG) Week 2  
**Expected Completion:** Phase 4H by end of Week 2, integrated with 4F/4G by Week 5

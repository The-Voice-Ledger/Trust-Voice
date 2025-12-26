# AddisAI & ChromaDB Integration Guide for Trust-Voice

**Date:** December 25, 2025  
**Purpose:** Complete integration guide for AddisAI voice interface and ChromaDB RAG system

---

## 📋 Table of Contents

1. [ChromaDB Cloud Setup](#chromadb-cloud-setup)
2. [AddisAI Voice Interface Integration](#addisai-voice-interface-integration)
3. [Implementation Roadmap](#implementation-roadmap)
4. [Code Examples](#code-examples)

---

## 🗄️ ChromaDB Cloud Setup

### Credentials (Trust-Voice)

```bash
# Add to .env file
CHROMA_API_KEY=ck-6qcWqtM8nBUShEns7t5BTToiPNFuT7FdJuCfHzexUtw1
CHROMA_TENANT=72183ad1-b676-4eb4-9e6c-b9bbde30ad6a
CHROMA_DATABASE="Trust-Voice"
CHROMA_CLIENT_TYPE=cloud
```

### FastAPI Integration Pattern

**File:** `database/chroma_connection.py` (NEW)

```python
"""
ChromaDB Cloud connection singleton for Trust-Voice RAG system.
Provides dependency injection for FastAPI routes.
"""
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from fastapi import Depends
from dotenv import load_dotenv
import os

load_dotenv()

# Singleton instances
_client: ClientAPI | None = None
_collection: Collection | None = None

def get_chroma_client() -> ClientAPI:
    """
    Get or create ChromaDB Cloud client (singleton).
    
    Returns:
        ClientAPI: ChromaDB client instance
    """
    global _client
    if _client is None:
        _client = chromadb.CloudClient(
            api_key=os.getenv("CHROMA_API_KEY"),
            tenant=os.getenv("CHROMA_TENANT"),
            database=os.getenv("CHROMA_DATABASE")
        )
    return _client

def get_chroma_collection(
    client: ClientAPI = Depends(get_chroma_client),
    collection_name: str = "trustvoice_knowledge_base"
) -> Collection:
    """
    Get or create ChromaDB collection (singleton).
    
    Args:
        client: ChromaDB client (injected)
        collection_name: Collection name (default: trustvoice_knowledge_base)
        
    Returns:
        Collection: ChromaDB collection instance
    """
    global _collection
    if _collection is None:
        _collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Trust-Voice knowledge base for RAG"}
        )
    return _collection
```

### Usage in FastAPI Routes

**Example:** `voice/routers/rag_api.py` (NEW)

```python
from fastapi import APIRouter, HTTPException, Depends
from database.chroma_connection import get_chroma_collection
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/rag", tags=["RAG"])

class DocumentRequest(BaseModel):
    ids: List[str]
    documents: List[str]
    metadatas: List[dict]

class QueryRequest(BaseModel):
    query: str
    n_results: int = 3

@router.post("/documents/")
async def add_documents(
    request: DocumentRequest, 
    collection=Depends(get_chroma_collection)
):
    """
    Add documents to ChromaDB knowledge base.
    
    Example:
        POST /api/rag/documents/
        {
          "ids": ["doc1", "doc2"],
          "documents": ["Campaign creation guide...", "Donation FAQ..."],
          "metadatas": [
            {"category": "campaign", "section": "creation"},
            {"category": "donation", "section": "faq"}
          ]
        }
    """
    try:
        collection.add(
            ids=request.ids,
            documents=request.documents,
            metadatas=request.metadatas
        )
        return {
            "message": "Documents added successfully", 
            "count": len(request.ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/")
async def query_documents(
    request: QueryRequest,
    collection=Depends(get_chroma_collection)
):
    """
    Query ChromaDB for relevant documents.
    
    Example:
        POST /api/rag/query/
        {
          "query": "How do I create a campaign?",
          "n_results": 3
        }
    """
    try:
        results = collection.query(
            query_texts=[request.query],
            n_results=request.n_results
        )
        return {
            "documents": results['documents'][0],
            "metadatas": results['metadatas'][0],
            "distances": results['distances'][0]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Testing ChromaDB Connection

```bash
# Add documents via curl
curl -X POST "http://localhost:8001/api/rag/documents/" \
     -H "Content-Type: application/json" \
     -d '{
       "ids": ["guide1", "guide2"],
       "documents": [
         "To create a campaign, use the voice command: Create campaign for water project goal 10000 dollars",
         "Donations can be made via M-Pesa or Stripe. Minimum donation is 1 dollar."
       ],
       "metadatas": [
         {"category": "campaign", "type": "guide"},
         {"category": "donation", "type": "faq"}
       ]
     }'

# Query documents
curl -X POST "http://localhost:8001/api/rag/query/" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "How do I create a campaign?",
       "n_results": 2
     }'
```

---

## 🎤 AddisAI Voice Interface Integration

### Overview

AddisAI provides:
- **Speech-to-Text (STT):** Amharic & Afan Oromo transcription
- **Text-to-Speech (TTS):** Native voice synthesis
- **Chat API:** Conversational AI in local languages

**Pricing:** TBD (estimated $0.01-0.02/min based on Voice Ledger comparisons)

### API Endpoints

| Endpoint | Method | Purpose | Language Support |
|----------|--------|---------|------------------|
| `/v1/audio/transcribe` | POST | Speech-to-Text | `am`, `om` |
| `/v1/chat/completions` | POST | Conversational AI | `am`, `om` |
| `/v1/audio/speech` | POST | Text-to-Speech | `am`, `om` |

### Provider Abstraction Pattern

**File:** `voice/providers/addis_ai.py` (NEW)

```python
"""
AddisAI provider for Amharic voice processing.
Implements STT, TTS, and conversational AI.
"""
import os
import httpx
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class AddisAIProvider:
    """
    AddisAI API client for Amharic voice processing.
    """
    
    def __init__(self):
        self.api_key = os.getenv("ADDIS_AI_API_KEY")
        if not self.api_key:
            raise ValueError("ADDIS_AI_API_KEY not set in environment")
        
        self.base_url = "https://api.addisassistant.com/api"
        self.default_language = "am"  # Amharic
        self.default_voice = "female-1"
    
    async def transcribe(
        self, 
        audio_path: str, 
        language: str = "am"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text using AddisAI STT.
        
        Args:
            audio_path: Path to audio file
            language: 'am' (Amharic) or 'om' (Afan Oromo)
            
        Returns:
            {
                "text": "transcribed text",
                "language": "am",
                "confidence": 0.95
            }
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(audio_path, 'rb') as audio_file:
                    files = {"audio": audio_file}
                    data = {"language": language}
                    
                    response = await client.post(
                        f"{self.base_url}/v1/audio/transcribe",
                        headers={"X-API-Key": self.api_key},
                        files=files,
                        data=data
                    )
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    return {
                        "text": result.get("text", ""),
                        "language": language,
                        "confidence": result.get("confidence", 0.85)
                    }
        except Exception as e:
            logger.error(f"AddisAI transcription failed: {e}")
            raise
    
    async def text_to_speech(
        self, 
        text: str, 
        language: str = "am",
        voice_id: Optional[str] = None
    ) -> bytes:
        """
        Convert text to speech using AddisAI TTS.
        
        Args:
            text: Text to convert
            language: 'am' (Amharic) or 'om' (Afan Oromo)
            voice_id: Voice ID (default: female-1)
            
        Returns:
            Audio bytes (WAV format)
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/audio/speech",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": text,
                        "language": language,
                        "voice_id": voice_id or self.default_voice
                    }
                )
                
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"AddisAI TTS failed: {e}")
            raise
    
    async def chat_completion(
        self,
        message: str,
        conversation_history: list = None,
        language: str = "am"
    ) -> str:
        """
        Get conversational AI response using AddisAI.
        
        Args:
            message: User message
            conversation_history: Previous messages
            language: 'am' (Amharic) or 'om' (Afan Oromo)
            
        Returns:
            AI response text
        """
        try:
            messages = conversation_history or []
            messages.append({"role": "user", "content": message})
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "addis-1-alef",
                        "messages": messages,
                        "language": language
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"AddisAI chat failed: {e}")
            raise
```

### OpenAI Provider (English)

**File:** `voice/providers/openai_voice.py` (NEW)

```python
"""
OpenAI provider for English voice processing.
Implements Whisper STT and TTS.
"""
import os
import openai
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OpenAIProvider:
    """
    OpenAI API client for English voice processing.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        
        openai.api_key = self.api_key
    
    async def transcribe(
        self, 
        audio_path: str, 
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Transcribe audio using OpenAI Whisper API.
        
        Args:
            audio_path: Path to audio file
            language: Language code (default: 'en')
            
        Returns:
            {
                "text": "transcribed text",
                "language": "en",
                "confidence": 1.0
            }
        """
        try:
            with open(audio_path, 'rb') as audio_file:
                response = await openai.Audio.atranscribe(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )
                
                return {
                    "text": response.text,
                    "language": language,
                    "confidence": 1.0  # Whisper doesn't return confidence
                }
        except Exception as e:
            logger.error(f"OpenAI transcription failed: {e}")
            raise
    
    async def text_to_speech(
        self, 
        text: str, 
        voice: str = "alloy"
    ) -> bytes:
        """
        Convert text to speech using OpenAI TTS.
        
        Args:
            text: Text to convert
            voice: Voice ID (alloy, echo, fable, onyx, nova, shimmer)
            
        Returns:
            Audio bytes (MP3 format)
        """
        try:
            response = await openai.Audio.atts_1(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            return response.content
        except Exception as e:
            logger.error(f"OpenAI TTS failed: {e}")
            raise
```

### Language Router

**File:** `voice/providers/voice_router.py` (NEW)

```python
"""
Routes voice processing to appropriate provider based on user language preference.
"""
from typing import Dict, Any
from voice.providers.addis_ai import AddisAIProvider
from voice.providers.openai_voice import OpenAIProvider
from database.models import User

class VoiceRouter:
    """
    Routes voice requests to AddisAI (Amharic) or OpenAI (English).
    """
    
    def __init__(self):
        self.addis_ai = AddisAIProvider()
        self.openai = OpenAIProvider()
    
    async def transcribe(
        self, 
        audio_path: str, 
        user: User
    ) -> Dict[str, Any]:
        """
        Route transcription to correct provider based on user language.
        
        Args:
            audio_path: Path to audio file
            user: User object with preferred_language
            
        Returns:
            Transcription result
        """
        if user.preferred_language == "am":
            return await self.addis_ai.transcribe(audio_path, "am")
        else:
            return await self.openai.transcribe(audio_path, "en")
    
    async def text_to_speech(
        self, 
        text: str, 
        user: User
    ) -> bytes:
        """
        Route TTS to correct provider based on user language.
        
        Args:
            text: Text to convert
            user: User object with preferred_language
            
        Returns:
            Audio bytes
        """
        if user.preferred_language == "am":
            return await self.addis_ai.text_to_speech(text, "am")
        else:
            return await self.openai.text_to_speech(text)
```

### Web Voice UI Implementation

**Frontend File:** `frontend/voice-ui.html` (NEW)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trust-Voice - Voice Assistant</title>
    <link rel="stylesheet" href="css/voice.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Trust-Voice Assistant</h1>
            <div class="language-switcher">
                <button id="lang-en" class="active">🇺🇸 English</button>
                <button id="lang-am">🇪🇹 አማርኛ</button>
            </div>
        </header>
        
        <div class="voice-controls">
            <button id="start-recording" class="btn-primary">
                🎤 Start Recording
            </button>
            <button id="stop-recording" class="btn-danger" disabled>
                ⏹️ Stop Recording
            </button>
        </div>
        
        <div class="conversation-container">
            <div id="conversation-history"></div>
        </div>
    </div>
    
    <script src="js/voice-controller.js"></script>
</body>
</html>
```

**Frontend JavaScript:** `frontend/js/voice-controller.js` (NEW)

```javascript
/**
 * Trust-Voice Web Voice Controller
 * Handles recording, transcription, and playback
 */

class TrustVoiceController {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8001/api';
        this.currentLanguage = 'en';
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        
        this.initElements();
        this.initEventListeners();
        this.loadUserLanguagePreference();
    }
    
    initElements() {
        this.startBtn = document.getElementById('start-recording');
        this.stopBtn = document.getElementById('stop-recording');
        this.langEnBtn = document.getElementById('lang-en');
        this.langAmBtn = document.getElementById('lang-am');
        this.conversationHistory = document.getElementById('conversation-history');
    }
    
    initEventListeners() {
        this.startBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.langEnBtn.addEventListener('click', () => this.switchLanguage('en'));
        this.langAmBtn.addEventListener('click', () => this.switchLanguage('am'));
    }
    
    async loadUserLanguagePreference() {
        try {
            const token = localStorage.getItem('auth_token');
            if (!token) return;
            
            const response = await fetch(`${this.apiBaseUrl}/auth/me`, {
                headers: {'Authorization': `Bearer ${token}`}
            });
            
            if (response.ok) {
                const user = await response.json();
                this.currentLanguage = user.preferred_language || 'en';
                this.updateLanguageUI();
            }
        } catch (error) {
            console.error('Error loading language preference:', error);
        }
    }
    
    async switchLanguage(lang) {
        this.currentLanguage = lang;
        this.updateLanguageUI();
        
        // Save to database if authenticated
        const token = localStorage.getItem('auth_token');
        if (token) {
            try {
                await fetch(`${this.apiBaseUrl}/users/me/language`, {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({language: lang})
                });
            } catch (error) {
                console.error('Error saving language preference:', error);
            }
        }
    }
    
    updateLanguageUI() {
        this.langEnBtn.classList.toggle('active', this.currentLanguage === 'en');
        this.langAmBtn.classList.toggle('active', this.currentLanguage === 'am');
    }
    
    async startRecording() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({audio: true});
            this.mediaRecorder = new MediaRecorder(this.stream);
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => this.processAudio();
            
            this.audioChunks = [];
            this.mediaRecorder.start();
            
            // Update UI
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            
            this.addMessage('Listening...', 'system');
        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.addMessage('Error accessing microphone. Please check permissions.', 'error');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
            this.stream.getTracks().forEach(track => track.stop());
            
            // Update UI
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
            
            this.addMessage('Processing audio...', 'system');
        }
    }
    
    async processAudio() {
        const audioBlob = new Blob(this.audioChunks, {type: 'audio/wav'});
        
        try {
            // Step 1: Transcribe audio
            const formData = new FormData();
            formData.append('audio', audioBlob);
            formData.append('language', this.currentLanguage);
            
            const transcribeResponse = await fetch(
                `${this.apiBaseUrl}/voice/transcribe`,
                {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                    }
                }
            );
            
            if (!transcribeResponse.ok) {
                throw new Error('Transcription failed');
            }
            
            const transcriptData = await transcribeResponse.json();
            this.addMessage(transcriptData.text, 'user');
            
            // Step 2: Process with NLU and get response
            const chatResponse = await fetch(
                `${this.apiBaseUrl}/voice/process`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                    },
                    body: JSON.stringify({
                        transcript: transcriptData.text,
                        language: this.currentLanguage
                    })
                }
            );
            
            if (!chatResponse.ok) {
                throw new Error('Processing failed');
            }
            
            const chatData = await chatResponse.json();
            this.addMessage(chatData.response_text, 'assistant');
            
            // Step 3: Play audio response (if available)
            if (chatData.audio_url) {
                await this.playAudio(chatData.audio_url);
            }
            
        } catch (error) {
            console.error('Error processing audio:', error);
            this.addMessage('Error processing audio. Please try again.', 'error');
        }
    }
    
    async playAudio(audioUrl) {
        const audio = new Audio(audioUrl);
        await audio.play();
    }
    
    addMessage(text, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.textContent = text;
        this.conversationHistory.appendChild(messageDiv);
        this.conversationHistory.scrollTop = this.conversationHistory.scrollHeight;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new TrustVoiceController();
});
```

---

## 🗺️ Implementation Roadmap

### Phase 1: ChromaDB Integration (Week 1, 10-12 hours)

**Day 1 (4 hours):**
- [ ] Create `database/chroma_connection.py`
- [ ] Add ChromaDB credentials to `.env`
- [ ] Test connection with simple document add/query

**Day 2 (4 hours):**
- [ ] Create `voice/routers/rag_api.py`
- [ ] Implement document indexing endpoint
- [ ] Implement query endpoint
- [ ] Test with campaign guides and FAQs

**Day 3 (2-4 hours):**
- [ ] Copy RAG enhancement from Voice Ledger
- [ ] Integrate with existing voice pipeline
- [ ] Test query classification
- [ ] Verify JSON format preservation

### Phase 2: AddisAI Integration (Week 2, 12-16 hours)

**Day 1 (4 hours):**
- [ ] Sign up for AddisAI API key
- [ ] Create `voice/providers/addis_ai.py`
- [ ] Test STT with sample Amharic audio
- [ ] Test TTS with Amharic text

**Day 2 (4 hours):**
- [ ] Create `voice/providers/openai_voice.py`
- [ ] Create `voice/providers/voice_router.py`
- [ ] Test language routing logic
- [ ] Update existing ASR to use router

**Day 3 (4-8 hours):**
- [ ] Create web voice UI (`frontend/voice-ui.html`)
- [ ] Implement `VoiceController` JavaScript class
- [ ] Test recording + playback
- [ ] Test language switching

### Phase 3: Testing & Deployment (Week 3, 6-8 hours)

- [ ] End-to-end testing (Amharic + English)
- [ ] Mobile browser testing (iOS Safari, Android Chrome)
- [ ] Performance testing (<2s STT, <1s TTS)
- [ ] Cost tracking and optimization
- [ ] Documentation updates

---

## 📝 Environment Variables Summary

```bash
# ChromaDB Cloud
CHROMA_API_KEY=ck-6qcWqtM8nBUShEns7t5BTToiPNFuT7FdJuCfHzexUtw1
CHROMA_TENANT=72183ad1-b676-4eb4-9e6c-b9bbde30ad6a
CHROMA_DATABASE="Trust-Voice"
CHROMA_CLIENT_TYPE=cloud

# AddisAI (Sign up at platform.addisassistant.com)
ADDIS_AI_API_KEY=<your_key_here>

# OpenAI (Already configured)
OPENAI_API_KEY=<your_existing_key>
```

---

## 🎯 Success Criteria

### ChromaDB Integration
- [ ] Can add documents via API
- [ ] Can query documents with >90% relevance
- [ ] RAG-enhanced responses have no hallucinations
- [ ] Query latency <200ms
- [ ] Cost per query <$0.02

### AddisAI Integration
- [ ] Amharic STT works with >85% accuracy
- [ ] Amharic TTS sounds natural
- [ ] Language routing works based on user preference
- [ ] Web voice UI works on mobile browsers
- [ ] Total latency <5 seconds (STT + NLU + TTS)

---

## 📚 References

- **ChromaDB Docs:** https://docs.trychroma.com/
- **AddisAI Platform:** https://platform.addisassistant.com/docs
- **AddisAI Voice Interface:** https://platform.addisassistant.com/docs/examples-and-tutorials/voice-interface
- **Voice Ledger Lab 17:** Working reference implementation
- **Voice Ledger RAG:** 3,539 chunks, zero hallucinations, production proven

---

**Status:** Ready for implementation  
**Next Step:** Start with ChromaDB integration (Phase 1, Day 1)  
**Estimated Total Time:** 28-36 hours (3-4 weeks)


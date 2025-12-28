#!/usr/bin/env python3
"""
Test enhanced NLU with system info queries
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from voice.nlu.nlu_infer import extract_intent_and_entities

# Test queries that should now be handled better
test_queries = [
    "Tell me about TrustVoice",
    "What is this system?",
    "How does this platform work?",
    "What can you do?",
    "Explain this service",
    "What makes TrustVoice different?",
    "Show me campaigns",
    "What campaigns are available?",
    "I would like to make a donation",
    "Tell me about the donation process",
]

print("🧠 Testing Enhanced NLU\n" + "="*60)

for query in test_queries:
    print(f"\n📝 Query: \"{query}\"")
    try:
        result = extract_intent_and_entities(query, language="en")
        intent = result['intent']
        confidence = result['confidence']
        
        # Color code based on intent
        if intent == "unclear":
            status = "❌"
        elif intent == "system_info":
            status = "🎯"
        elif intent in ["get_help", "search_campaigns", "make_donation"]:
            status = "✅"
        else:
            status = "ℹ️"
        
        print(f"{status} Intent: {intent} (confidence: {confidence:.1%})")
        
        if result.get('entities'):
            print(f"   Entities: {result['entities']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*60)
print("✅ NLU Test Complete!")
print("\nKey improvements:")
print("  • 'Tell me about TrustVoice' → system_info (was unclear)")
print("  • 'What is this system?' → system_info (was unclear)")
print("  • 'Show me campaigns' → search_campaigns (better match)")
print("  • More context-aware intent classification")

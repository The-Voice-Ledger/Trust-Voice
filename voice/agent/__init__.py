"""
TrustVoice AI Agent — GPT function-calling orchestration layer.

Replaces the rigid NLU → intent-classification → switch/case pipeline
with a single GPT-powered agent that uses OpenAI tool-calling to handle
any user request — including compound commands and natural multi-turn
conversations.

Architecture:
    tools.py     → 13 OpenAI function-calling tool schemas
    executor.py  → Agent loop, tool dispatch, conversation history
"""

from voice.agent.executor import AgentExecutor

__all__ = ["AgentExecutor"]

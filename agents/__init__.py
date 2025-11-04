"""
Agents module for intelligent job matching.

This module contains LangChain-based agents for:
- Conversational job matching with clarification
- Intelligent job search and recommendation
- Adaptive scoring based on candidate profile
"""

from .conversational_agent import ConversationalJobAgent

__all__ = ["ConversationalJobAgent"]

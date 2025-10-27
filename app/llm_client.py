from __future__ import annotations

import google.generativeai as genai
import ssl
from typing import List, Dict, Optional
from .config import get_settings


class GeminiClient:
    """Thin wrapper around google.generativeai for consistent chat completions.

    - Uses Settings.GEMINI_API_KEY and Settings.GEMINI_MODEL (default: gemini-2.5-flash)
    - Accepts OpenAI-style messages and maps them to Gemini message format
    - Supports configurable max_tokens and temperature
    
    SYSTEM PROMPT HANDLING:
    Gemini 2.0 Flash does not have a dedicated 'system' role like OpenAI models.
    Instead, system instructions are embedded into the first user message with clear
    visual separation. This approach preserves 100% of the original prompt content,
    formatting, tone, personality, and all attributes while adapting to Gemini's API.
    
    The conversion ensures that complex system prompts (like Sapient's personality,
    rules, constraints, and formatting guidelines) are fully preserved and given
    ABSOLUTE PRIORITY through visual hierarchy and explicit labeling.
    """

    def __init__(self, model: Optional[str] = None):
        settings = get_settings()
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set. Please configure it in .env")

        # --- DIAGNOSTIC STEP ---
        # Print the SSL certificate path Python is using.
        try:
            cert_path = ssl.get_default_verify_paths()
            print(f"✅ [DIAGNOSTIC] Python SSL cert path: {cert_path.cafile}")
        except Exception as e:
            print(f"❌ [DIAGNOSTIC] Could not get Python SSL cert path: {e}")
        # --- END DIAGNOSTIC ---
        
        # CRITICAL FIX: Force REST API instead of gRPC
        # The default gRPC transport is being blocked/timing out in this environment
        # Using REST transport resolves 504 Deadline Exceeded errors
        import google.generativeai.types as genai_types
        genai.configure(
            api_key=api_key,
            transport="rest"  # Force REST instead of gRPC
        )
        self.model_name = model or settings.GEMINI_MODEL or "gemini-2.5-flash"
        
        # Configure safety settings for internal corporate data processing
        # Setting BLOCK_NONE is appropriate because:
        # 1. This processes pre-vetted MBA job descriptions (not user content)
        # 2. No adversarial actors (authenticated students only)
        # 3. Business terminology (FMCG, Portfolio Management) was incorrectly blocked
        # 4. Even BLOCK_ONLY_HIGH caused false positives on legitimate queries
        # See GEMINI_SAFETY_FIX.md for full rationale
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        self.safety_settings = [
            {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
            {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_NONE},
            {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_NONE},
            {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
        ]
        
        self._model = genai.GenerativeModel(self.model_name, safety_settings=self.safety_settings)

    def _to_gemini_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, List[str]]]:
        """Convert OpenAI-style messages to Gemini format.
        
        CRITICAL: Preserves ALL content, formatting, tone, and personality from system prompts.
        System instructions are embedded into the first user message with clear visual separation.
        """
        gemini_messages: List[Dict[str, List[str]]] = []
        system_content = None
        
        # First pass: extract all system messages and preserve their full content
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            
            if role == "system":
                # Store system content for embedding into first user message
                # Preserve ALL formatting, newlines, structure, personality traits
                if system_content is None:
                    system_content = content
                else:
                    # If multiple system messages, concatenate them
                    system_content += f"\n\n{content}"
        
        # Second pass: build Gemini messages with embedded system instructions
        first_user_message = True
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            
            if role == "system":
                # Skip; already extracted above
                continue
            elif role == "user":
                # Embed system instructions into the FIRST user message only
                if first_user_message and system_content:
                    # Use clear visual separation to distinguish system instructions from user query
                    # This preserves the authority and structure of complex system prompts
                    combined_content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SYSTEM INSTRUCTIONS (ABSOLUTE PRIORITY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{system_content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER QUERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{content}"""
                    gemini_messages.append({"role": "user", "parts": [combined_content]})
                    first_user_message = False
                else:
                    # Subsequent user messages don't need system instructions repeated
                    gemini_messages.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [content]})
                first_user_message = False  # After assistant response, we're past the first turn
            else:
                # Default to user role
                if first_user_message and system_content:
                    combined_content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SYSTEM INSTRUCTIONS (ABSOLUTE PRIORITY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{system_content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER QUERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{content}"""
                    gemini_messages.append({"role": "user", "parts": [combined_content]})
                    first_user_message = False
                else:
                    gemini_messages.append({"role": "user", "parts": [content]})
        
        return gemini_messages

    def _safe_get_text(self, resp) -> str:
        """Safely extract text from Gemini response, handling safety blocks.
        
        Args:
            resp: Gemini response object
            
        Returns:
            Response text, or fallback message if blocked
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # First check if response has any candidates at all
        if not hasattr(resp, 'candidates') or not resp.candidates:
            logger.error("❌ Gemini returned no candidates")
            if hasattr(resp, 'prompt_feedback'):
                feedback = resp.prompt_feedback
                logger.warning(f"📋 Prompt feedback: {feedback}")
                if hasattr(feedback, 'block_reason'):
                    logger.warning(f"🚫 Prompt blocked - Reason: {feedback.block_reason}")
                    return f"The prompt was blocked by Gemini's safety filters. Reason: {feedback.block_reason}. Please rephrase your question."
            return "No response generated. Please try rephrasing your question."
        
        candidate = resp.candidates[0]
        
        # Check if candidate has any parts with text
        if not hasattr(candidate, 'content') or not candidate.content:
            logger.warning("⚠️  Candidate has no content")
            finish_reason = getattr(candidate, 'finish_reason', None)
            logger.warning(f"⚠️  Finish reason: {finish_reason}")
            
            # Check safety ratings
            if hasattr(candidate, 'safety_ratings'):
                safety_ratings = candidate.safety_ratings
                logger.warning(f"🛡️  Safety ratings: {safety_ratings}")
                for rating in safety_ratings:
                    logger.warning(f"   - Category: {getattr(rating, 'category', 'unknown')}, Probability: {getattr(rating, 'probability', 'unknown')}")
            
            return "Response was blocked or empty. Please try rephrasing your question."
        
        try:
            # Try to access the text directly
            return getattr(resp, "text", "") or ""
        except (ValueError, AttributeError) as e:
            # Response was blocked or malformed
            logger.error(f"❌ Error accessing response text: {e}")
            
            # Detailed logging for debugging
            finish_reason = getattr(candidate, 'finish_reason', None)
            logger.warning(f"⚠️  Finish reason: {finish_reason}")
            
            # Log safety ratings
            if hasattr(candidate, 'safety_ratings'):
                safety_ratings = candidate.safety_ratings
                logger.warning(f"�️  Safety ratings: {safety_ratings}")
                for rating in safety_ratings:
                    cat = getattr(rating, 'category', 'unknown')
                    prob = getattr(rating, 'probability', 'unknown')
                    logger.warning(f"   - Category: {cat}, Probability: {prob}")
            
            # Check prompt feedback
            if hasattr(resp, 'prompt_feedback'):
                feedback = resp.prompt_feedback
                logger.warning(f"📋 Prompt feedback: {feedback}")
                if hasattr(feedback, 'block_reason'):
                    logger.warning(f"🚫 Block reason: {feedback.block_reason}")
            
            return "I found relevant information but encountered a content filter. Please try rephrasing your question or contact support."
    
    def _get_finish_reason_name(self, finish_reason) -> str:
        """Convert finish reason enum to human-readable name."""
        reason_map = {
            0: "UNSPECIFIED",
            1: "STOP",
            2: "MAX_TOKENS",
            3: "SAFETY",
            4: "RECITATION",
            5: "OTHER"
        }
        return reason_map.get(finish_reason, f"UNKNOWN({finish_reason})")

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 3000, temperature: float = 0.7, timeout: Optional[float] = None) -> str:
        """Send messages to Gemini and return the response.
        
        Args:
            messages: List of OpenAI-style messages (automatically converted)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            timeout: Request timeout in seconds (default: 60.0)
            
        Returns:
            Generated text response
        """
        import os
        
        # Use configurable timeout, defaulting to 60 seconds
        request_timeout = timeout or float(os.getenv("GEMINI_TIMEOUT_SECONDS", "60.0"))
        
        gemini_messages = self._to_gemini_messages(messages)
        
        try:
            # If we have only one message, use generate_content directly
            if len(gemini_messages) == 1:
                resp = self._model.generate_content(
                    gemini_messages[0]["parts"][0],
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=temperature,
                    ),
                    request_options={"timeout": request_timeout},
                )
                return self._safe_get_text(resp)
            
            # For multi-turn conversations, use chat with history
            # Split into history (all but last) and current message (last)
            history = gemini_messages[:-1]
            current_msg = gemini_messages[-1]
            
            convo = self._model.start_chat(history=history)
            resp = convo.send_message(
                current_msg["parts"][0],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
                request_options={"timeout": request_timeout},
            )
            return self._safe_get_text(resp)
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Gemini API error: {e}")
            logger.error(f"   Request timeout: {request_timeout}s")
            logger.error(f"   Model: {self.model_name}")
            
            # Re-raise with more context
            if "timeout" in str(e).lower():
                raise TimeoutError(f"Gemini API timeout after {request_timeout}s: {e}") from e
            else:
                raise RuntimeError(f"Gemini API error: {e}") from e


def get_gemini_client(model: Optional[str] = None) -> GeminiClient:
    return GeminiClient(model=model)

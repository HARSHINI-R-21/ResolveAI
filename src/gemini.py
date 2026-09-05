"""
ResolveAI Gemini API Client Wrapper
Handles intent detection and grounded natural-language response generation.
NOTE: Business decisions (RESOLVE, ASK, ESCALATE) are strictly governed by src/rules.py.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    """
    Client for interacting with Google Gemini API for intent classification and grounded text generation.
    Fails safely with deterministic fallback responses if API key is missing or API call fails.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.client = None
        self.sdk_type = None
        self._init_sdk()

    def _init_sdk(self):
        """
        Initializes Google GenAI SDK if API key is present.
        """
        if not self.api_key:
            print("[INFO] GEMINI_API_KEY not set. Operating in safe fallback mode.")
            return

        try:
            # Try official google-genai SDK first
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.sdk_type = "google-genai"
        except ImportError:
            try:
                # Fallback to google-generativeai SDK if installed
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                self.client = legacy_genai.GenerativeModel("gemini-1.5-flash")
                self.sdk_type = "google-generativeai"
            except Exception as e:
                print(f"[WARNING] Gemini SDK initialization failed: {e}")
                self.client = None

    def detect_intent(self, message: str) -> Dict[str, Any]:
        """
        Detects customer domain intent (BILLING, CONNECTION, PLAN, REFUND, OTHER).
        Does NOT determine resolution decision (RESOLVE/ASK/ESCALATE).
        """
        if not message or not message.strip():
            return {"intent": "OTHER", "confidence": 0.0}

        # Deterministic keyword fallback classifier
        msg_lower = message.lower()
        fallback_intent = "OTHER"
        if any(w in msg_lower for w in ["bill", "billing", "charge", "payment", "invoice", "cost"]):
            fallback_intent = "BILLING"
        elif any(w in msg_lower for w in ["internet", "connection", "outage", "offline", "router", "wifi", "broadband", "down", "disconnect"]):
            fallback_intent = "CONNECTION"
        elif any(w in msg_lower for w in ["plan", "upgrade", "speed", "package", "subscription"]):
            fallback_intent = "PLAN"
        elif any(w in msg_lower for w in ["refund", "credit", "compensation", "reimbursement"]):
            fallback_intent = "REFUND"

        if not self.client:
            return {"intent": fallback_intent, "confidence": 0.85, "source": "keyword_fallback"}

        prompt = f"""You are a customer support intent classification system.
Classify the following customer support message into EXACTLY ONE of these categories:
- BILLING
- CONNECTION
- PLAN
- REFUND
- OTHER

Message: "{message}"

Return ONLY a JSON object in this exact format:
{{"intent": "CATEGORY_NAME", "confidence": 0.95}}
Do NOT include markdown formatting or extra commentary."""

        try:
            raw_text = self._call_gemini_raw(prompt)
            parsed = self._clean_and_parse_json(raw_text)
            intent = str(parsed.get("intent", "")).upper()
            if intent in ["BILLING", "CONNECTION", "PLAN", "REFUND", "OTHER"]:
                return {
                    "intent": intent,
                    "confidence": float(parsed.get("confidence", 0.9)),
                    "source": "gemini_api"
                }
        except Exception as e:
            print(f"[WARNING] Gemini intent detection API call failed: {e}")

        return {"intent": fallback_intent, "confidence": 0.80, "source": "keyword_fallback"}

    def generate_grounded_response(
        self,
        rule_decision: Dict[str, Any],
        customer_record: Optional[Dict[str, Any]],
        ticket_history: List[Dict[str, Any]],
        article: Optional[Dict[str, Any]],
        customer_message: str
    ) -> str:
        """
        Generates grounded natural-language response based on Python RuleEngine decision.
        """
        decision = rule_decision.get("decision", "ESCALATE")

        if decision == "RESOLVE":
            return self._generate_resolve_response(rule_decision, customer_record, article, customer_message)
        elif decision == "ASK":
            return self._generate_ask_response(rule_decision, customer_record, customer_message)
        else:
            return self._generate_escalate_response(rule_decision, customer_record, ticket_history, article, customer_message)

    def _generate_resolve_response(
        self,
        rule_decision: Dict[str, Any],
        customer_record: Optional[Dict[str, Any]],
        article: Optional[Dict[str, Any]],
        customer_message: str
    ) -> str:
        article_id = rule_decision.get("article_id", "")
        reason = rule_decision.get("reason", "")
        
        fallback_resp = f"Based on your account records and support guide [{article_id}], your query has been analyzed: {reason}"
        if customer_record:
            fallback_resp += f" (Customer Plan: {customer_record.get('plan')}, Current Bill: ${customer_record.get('current_bill')})."

        if not self.client:
            return fallback_resp

        prompt = f"""You are a professional grounded customer support assistant.
Write a concise, polite response answering the customer.

STRICT GROUNDING INSTRUCTIONS:
Use ONLY the supplied customer data, rule decision, and knowledge-base content below.
Do NOT invent account facts, prices, plans, policies, or troubleshooting history.

CUSTOMER DATA:
{json.dumps(customer_record or {}, indent=2)}

RULE DECISION:
Decision: RESOLVE
Reason: {reason}

KNOWLEDGE BASE ARTICLE:
Article ID: {article_id}
Title: {article.get('title') if article else ''}
Content: {article.get('content', '')[:600] if article else ''}

CUSTOMER MESSAGE:
"{customer_message}"

Write a concise support response ready for an agent to review (max 3 sentences)."""

        try:
            resp = self._call_gemini_raw(prompt)
            if resp and resp.strip():
                return resp.strip()
        except Exception as e:
            print(f"[WARNING] Gemini resolve response generation failed: {e}")

        return fallback_resp

    def _generate_ask_response(
        self,
        rule_decision: Dict[str, Any],
        customer_record: Optional[Dict[str, Any]],
        customer_message: str
    ) -> str:
        missing_info = rule_decision.get("missing_information", [])
        missing_str = ", ".join(missing_info) if missing_info else "additional details"

        fallback_resp = f"To assist you with your request, please provide the following details: {missing_str}."

        if not self.client:
            return fallback_resp

        prompt = f"""You are a customer support assistant requesting missing details.

STRICT GROUNDING INSTRUCTIONS:
Ask ONLY for the missing information identified by the system below.
Do NOT invent additional required fields or ask unnecessary questions.

MISSING INFORMATION REQUIRED:
{json.dumps(missing_info, indent=2)}

CUSTOMER MESSAGE:
"{customer_message}"

Write a polite, concise support message asking the customer for EXACTLY these missing details."""

        try:
            resp = self._call_gemini_raw(prompt)
            if resp and resp.strip():
                return resp.strip()
        except Exception as e:
            print(f"[WARNING] Gemini ask response generation failed: {e}")

        return fallback_resp

    def _generate_escalate_response(
        self,
        rule_decision: Dict[str, Any],
        customer_record: Optional[Dict[str, Any]],
        ticket_history: List[Dict[str, Any]],
        article: Optional[Dict[str, Any]],
        customer_message: str
    ) -> str:
        escalation_facts = rule_decision.get("escalation_facts", [])
        previous_attempts = rule_decision.get("previous_attempts", [])
        reason = rule_decision.get("reason", "Issue requires human supervisor evaluation.")

        facts_bullet = "\n- ".join(escalation_facts) if escalation_facts else "No specific escalation facts logged."
        attempts_bullet = "\n- ".join(previous_attempts) if previous_attempts else "None logged."

        fallback_resp = (
            "HANDOVER SUMMARY\n\n"
            "ESTABLISHED FACTS:\n"
            f"- {facts_bullet}\n\n"
            "PREVIOUS ATTEMPTS:\n"
            f"- {attempts_bullet}\n\n"
            "HANDOVER SUMMARY:\n"
            f"Case escalated to a human support specialist. Reason: {reason}"
        )

        if not self.client:
            return fallback_resp

        prompt = f"""You are a technical support coordinator generating a structured human-support handover summary.

STRICT GROUNDING INSTRUCTIONS:
Use ONLY the factual details provided below. Do NOT invent technical details or facts.

ESTABLISHED FACTS:
{json.dumps(escalation_facts, indent=2)}
Customer Account: {json.dumps(customer_record or {}, indent=2)}

PREVIOUS ATTEMPTS:
{json.dumps(previous_attempts, indent=2)}

REASON FOR ESCALATION:
{reason}

Format the handover output clearly with these three exact sections:
ESTABLISHED FACTS
PREVIOUS ATTEMPTS
HANDOVER SUMMARY"""

        try:
            resp = self._call_gemini_raw(prompt)
            if resp and resp.strip():
                return resp.strip()
        except Exception as e:
            print(f"[WARNING] Gemini escalation handover generation failed: {e}")

        return fallback_resp

    def _call_gemini_raw(self, prompt: str) -> str:
        """
        Executes API call using configured Gemini SDK.
        """
        if not self.client:
            raise RuntimeError("Gemini API client is not initialized.")

        if self.sdk_type == "google-genai":
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
                return response.text
            except Exception:
                # Fallback model attempt
                response = self.client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt
                )
                return response.text
        elif self.sdk_type == "google-generativeai":
            response = self.client.generate_content(prompt)
            return response.text
        else:
            raise RuntimeError("Unsupported Gemini SDK configuration.")

    def _clean_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        """
        Cleans markdown wrappers and parses JSON safely.
        """
        text = raw_text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text.strip())

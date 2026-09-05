"""
ResolveAI Core Support Assistant Coordinator
Orchestrates intent detection, data retrieval, deterministic rule evaluation, and Gemini response generation.
"""

from typing import Dict, Any, Optional
from src.gemini import GeminiClient
from src.retrieval import get_customer, get_tickets, search_articles
from src.rules import RuleEngine

class SupportAssistant:
    """
    Coordinator executing the complete resolution lifecycle:
    1. Intent detection (via Gemini or keyword fallback)
    2. Context retrieval (customer profile, ticket history, KB articles)
    3. Deterministic rule evaluation (RuleEngine -> RESOLVE, ASK, ESCALATE)
    4. Grounded response generation (via Gemini or rule fallback)
    """
    def __init__(self, data_path: str = "data", api_key: Optional[str] = None):
        self.data_path = data_path
        self.gemini_client = GeminiClient(api_key=api_key)
        self.rule_engine = RuleEngine(data_path=data_path)

    def process_request(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a support request payload containing:
        - customer_id (optional)
        - query / message / issue_details (required)
        - category (optional)
        """
        customer_id = request_payload.get("customer_id")
        customer_message = (
            request_payload.get("query")
            or request_payload.get("message")
            or request_payload.get("issue_details")
            or ""
        )
        category = request_payload.get("category")

        # Step 1: Detect Intent via Gemini (or keyword fallback)
        intent_res = self.gemini_client.detect_intent(customer_message)
        intent = intent_res.get("intent", category.upper() if category else "OTHER")
        confidence = intent_res.get("confidence", 0.0)

        # Step 2: Retrieve local grounded context
        customer_record = get_customer(customer_id, data_path=self.data_path) if customer_id else None
        ticket_history = get_tickets(customer_id, data_path=self.data_path) if customer_id else []
        retrieved_articles = search_articles(customer_message, category=category or intent, data_path=self.data_path)

        top_article = retrieved_articles[0] if retrieved_articles else None

        # Step 3: Run Deterministic Business Rule Engine (RuleEngine is ALWAYS Authoritative)
        rule_decision = self.rule_engine.evaluate(
            customer_id=customer_id,
            customer_message=customer_message,
            category=category or intent,
            customer_record=customer_record,
            ticket_history=ticket_history,
            retrieved_articles=retrieved_articles
        )

        # Step 4: Generate Grounded Natural Language Response via Gemini (or safe fallback)
        response_text = self.gemini_client.generate_grounded_response(
            rule_decision=rule_decision,
            customer_record=customer_record,
            ticket_history=ticket_history,
            article=top_article,
            customer_message=customer_message
        )

        # Build consistent final response payload
        return {
            "status": "success",
            "customer_id": customer_id,
            "intent": intent,
            "confidence": confidence,
            "decision": rule_decision["decision"],
            "reasoning": rule_decision["reason"],
            "response_text": response_text,
            "missing_information": rule_decision.get("missing_information", []),
            "evidence": rule_decision.get("evidence", []),
            "article_id": rule_decision.get("article_id"),
            "escalation_facts": rule_decision.get("escalation_facts", []),
            "previous_attempts": rule_decision.get("previous_attempts", [])
        }

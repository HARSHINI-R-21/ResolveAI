"""
ResolveAI Deterministic Business Rules Engine
Enforces decision logic: RESOLVE, ASK, or ESCALATE.
Prevents LLM fact invention and handles edge cases safely.
"""

import re
from typing import Dict, Any, List, Optional
from src.retrieval import get_customer, get_tickets, search_articles

DECISION_RESOLVE = "RESOLVE"
DECISION_ASK = "ASK"
DECISION_ESCALATE = "ESCALATE"

class RuleEngine:
    """
    Deterministic rule engine for evaluating customer support cases.
    Returns a consistent dictionary with decision: RESOLVE, ASK, or ESCALATE.
    """
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path

    def evaluate(
        self,
        customer_id: Optional[str] = None,
        customer_message: Optional[str] = None,
        category: Optional[str] = None,
        customer_record: Optional[Dict[str, Any]] = None,
        ticket_history: Optional[List[Dict[str, Any]]] = None,
        retrieved_articles: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates support query against business rules and verified local data.
        Returns decision dictionary (RESOLVE, ASK, or ESCALATE).
        """
        # 1. Edge Case: Empty customer message
        if not customer_message or not str(customer_message).strip():
            return {
                "decision": DECISION_ASK,
                "reason": "Customer message is empty. Please describe the customer issue or request.",
                "missing_information": ["Customer issue description / message"],
                "evidence": [],
                "article_id": None
            }

        customer_message_str = str(customer_message).strip()

        # 2. Retrieve customer record if customer_id provided but record is None
        if customer_record is None and customer_id:
            customer_record = get_customer(customer_id, data_path=self.data_path)

        # 3. Retrieve tickets if customer_id provided but tickets is None
        if ticket_history is None and customer_id:
            ticket_history = get_tickets(customer_id, data_path=self.data_path)
        elif ticket_history is None:
            ticket_history = []

        # 4. Edge Case: Unknown customer ID provided
        if customer_id and not customer_record:
            return {
                "decision": DECISION_ASK,
                "reason": f"Customer ID '{customer_id}' was not found in verified customer records.",
                "missing_information": ["Valid Customer ID or account verification details"],
                "evidence": [],
                "article_id": None
            }

        # 5. Retrieve support articles if not provided
        if retrieved_articles is None:
            retrieved_articles = search_articles(customer_message_str, category=category, data_path=self.data_path)

        top_article = retrieved_articles[0] if retrieved_articles else None
        article_id = top_article.get("article_id") if top_article else None

        # 6. Edge Case: No matching support article found (Unsupported intent / domain)
        if not top_article:
            return {
                "decision": DECISION_ESCALATE,
                "reason": "The customer query is not covered by any available local support knowledge base article.",
                "missing_information": [],
                "evidence": [],
                "article_id": None,
                "escalation_facts": ["No relevant knowledge base article found for query."],
                "previous_attempts": []
            }

        # 7. Check for ESCALATION rules (Priority order to prevent unsafe resolution)
        escalation_res = self._evaluate_escalation(
            customer_record=customer_record,
            ticket_history=ticket_history,
            top_article=top_article,
            customer_message=customer_message_str
        )
        if escalation_res:
            return escalation_res

        # 8. Check for ASK rules (Missing required information)
        ask_res = self._evaluate_ask(
            customer_record=customer_record,
            top_article=top_article,
            customer_message=customer_message_str
        )
        if ask_res:
            return ask_res

        # 9. Default to RESOLVE when grounded and fully supported
        return self._evaluate_resolve(
            customer_record=customer_record,
            top_article=top_article,
            customer_message=customer_message_str
        )

    def _evaluate_escalation(
        self,
        customer_record: Optional[Dict[str, Any]],
        ticket_history: List[Dict[str, Any]],
        top_article: Dict[str, Any],
        customer_message: str
    ) -> Optional[Dict[str, Any]]:
        """
        Checks all strong escalation triggers. Returns ESCALATE dict or None.
        """
        article_id = top_article.get("article_id", "")
        msg_lower = customer_message.lower()

        # Collect open tickets and previous troubleshooting attempts
        open_tickets = [
            t for t in ticket_history
            if str(t.get("status", "")).lower() in ["open", "unresolved", "pending"]
        ]

        previous_attempts = []
        for t in ticket_history:
            for attempt in t.get("previous_attempts", []):
                if attempt not in previous_attempts:
                    previous_attempts.append(attempt)

        escalation_facts = []

        # Rule A: Multiple open/unresolved tickets for customer
        if len(open_tickets) >= 2:
            escalation_facts.append(f"Customer has {len(open_tickets)} active unresolved support tickets.")

        # Rule B: Persistent connection outage on inactive account (e.g. C005)
        is_inactive_conn = customer_record and customer_record.get("connection_status") == "inactive"
        if is_inactive_conn and (open_tickets or "down" in msg_lower or "outage" in msg_lower):
            escalation_facts.append("Broadband connection status is inactive despite paid billing status.")

        # Rule C: Customer mentions repeated contacts or failed troubleshooting
        has_repeated_contact = any(
            phrase in msg_lower
            for phrase in ["contacted support", "already contacted", "called twice", "tried restarting", "already tried", "three days", "multiple times"]
        )
        if has_repeated_contact and (open_tickets or is_inactive_conn):
            escalation_facts.append("Customer reports repeated support contacts without issue resolution.")

        # Rule D: Refund / Credit request exceeds agent authorization limit ($20.00) in REFUND-001
        if article_id == "REFUND-001":
            amounts = re.findall(r"\$(\d+(?:\.\d+)?)", customer_message)
            exceeds_limit = False
            for amt_str in amounts:
                if float(amt_str) > 20.0:
                    exceeds_limit = True
                    escalation_facts.append(f"Requested refund/credit amount (${amt_str}) exceeds agent authorization limit ($20.00).")
            
            if "manager" in msg_lower or "cash" in msg_lower or "bank" in msg_lower:
                exceeds_limit = True
                escalation_facts.append("Customer requested cash refund or managerial override.")

        # If any escalation facts present, return ESCALATE
        if escalation_facts:
            evidence = []
            if customer_record:
                evidence.append(f"Customer ID: {customer_record.get('customer_id')}")
                evidence.append(f"Name: {customer_record.get('name')}")
                evidence.append(f"Connection Status: {customer_record.get('connection_status')}")
                evidence.append(f"Billing Status: {customer_record.get('billing_status')}")
            evidence.append(f"Open Tickets: {len(open_tickets)}")
            evidence.append(f"Article ID: {article_id}")

            return {
                "decision": DECISION_ESCALATE,
                "reason": "Case triggered escalation rules: " + "; ".join(escalation_facts),
                "missing_information": [],
                "evidence": evidence,
                "article_id": article_id,
                "escalation_facts": escalation_facts,
                "previous_attempts": previous_attempts
            }

        return None

    def _evaluate_ask(
        self,
        customer_record: Optional[Dict[str, Any]],
        top_article: Dict[str, Any],
        customer_message: str
    ) -> Optional[Dict[str, Any]]:
        """
        Checks if required information is missing for supported issues.
        Returns ASK dict or None.
        """
        article_id = top_article.get("article_id", "")
        msg_lower = customer_message.lower()
        missing_info = []

        # Plan Upgrade (PLAN-001): Requires target plan / speed preference
        if article_id == "PLAN-001":
            has_specific_plan = any(
                plan_name in msg_lower
                for plan_name in ["ultrafiber", "basicfiber", "gigabitmax", "5g flex", "5g unlimited", "100", "500", "1000"]
            )
            if not has_specific_plan:
                missing_info.append("Desired plan tier or target internet speed (e.g. 500 Mbps, GigabitMax)")
                missing_info.append("Usage requirements (e.g. remote work, streaming, mobile hotspot)")

        # Connection Troubleshooting (CONN-001): If modem/light details are missing
        elif article_id == "CONN-001":
            if "light" not in msg_lower and "router" not in msg_lower and "led" not in msg_lower and "restart" not in msg_lower:
                missing_info.append("Modem LED light status (e.g., solid green vs flashing red)")
                missing_info.append("Whether router power cycle has been attempted")

        if missing_info:
            evidence = []
            if customer_record:
                evidence.append(f"Customer ID: {customer_record.get('customer_id')}")
                evidence.append(f"Current Plan: {customer_record.get('plan')}")
            evidence.append(f"Article ID: {article_id}")

            return {
                "decision": DECISION_ASK,
                "reason": f"Issue is supported by {article_id}, but requires additional specific details from customer.",
                "missing_information": missing_info,
                "evidence": evidence,
                "article_id": article_id
            }

        return None

    def _evaluate_resolve(
        self,
        customer_record: Optional[Dict[str, Any]],
        top_article: Dict[str, Any],
        customer_message: str
    ) -> Dict[str, Any]:
        """
        Builds RESOLVE response when all information is grounded and verified.
        """
        article_id = top_article.get("article_id", "")
        
        evidence = []
        if customer_record:
            evidence.append(f"Customer ID: {customer_record.get('customer_id')}")
            evidence.append(f"Name: {customer_record.get('name')}")
            evidence.append(f"Plan: {customer_record.get('plan')}")
            evidence.append(f"Current Bill: ${customer_record.get('current_bill')}")
            evidence.append(f"Billing Status: {customer_record.get('billing_status')}")
            evidence.append(f"Connection Status: {customer_record.get('connection_status')}")
        
        evidence.append(f"Article Cited: {article_id} - {top_article.get('title')}")

        return {
            "decision": DECISION_RESOLVE,
            "reason": f"Query is fully supported by knowledge base article {article_id} and verified customer account data.",
            "missing_information": [],
            "evidence": evidence,
            "article_id": article_id
        }

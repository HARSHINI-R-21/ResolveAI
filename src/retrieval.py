"""
ResolveAI Local Data & Knowledge Base Retriever
Deterministic data-access functions for loading customers and support tickets.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def load_customers(data_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load customers from customers.json.
    Handles missing JSON files and malformed JSON gracefully.
    """
    file_path = Path(data_path) / "customers.json" if data_path else DATA_DIR / "customers.json"
    if not file_path.exists():
        print(f"[WARNING] Customers file not found at: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            print(f"[WARNING] Customers file content is not a list: {file_path}")
            return []
    except json.JSONDecodeError as e:
        print(f"[WARNING] Malformed JSON in customers file ({file_path}): {e}")
        return []
    except Exception as e:
        print(f"[WARNING] Unexpected error loading customers file ({file_path}): {e}")
        return []

def load_tickets(data_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load tickets from tickets.json.
    Handles missing JSON files and malformed JSON gracefully.
    """
    file_path = Path(data_path) / "tickets.json" if data_path else DATA_DIR / "tickets.json"
    if not file_path.exists():
        print(f"[WARNING] Tickets file not found at: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            print(f"[WARNING] Tickets file content is not a list: {file_path}")
            return []
    except json.JSONDecodeError as e:
        print(f"[WARNING] Malformed JSON in tickets file ({file_path}): {e}")
        return []
    except Exception as e:
        print(f"[WARNING] Unexpected error loading tickets file ({file_path}): {e}")
        return []

def get_customer(customer_id: str, data_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve customer record by customer_id.
    Returns None if customer_id is unknown or not found.
    """
    if not customer_id or not isinstance(customer_id, str):
        return None

    target_id = customer_id.strip().upper()
    customers = load_customers(data_path)
    
    for customer in customers:
        if isinstance(customer, dict) and str(customer.get("customer_id", "")).strip().upper() == target_id:
            return customer
            
    return None

def get_tickets(customer_id: str, data_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all support tickets for a given customer_id.
    Returns empty list if customer_id is unknown or has no tickets.
    """
    if not customer_id or not isinstance(customer_id, str):
        return []

    target_id = customer_id.strip().upper()
    tickets = load_tickets(data_path)
    
    matching_tickets = [
        ticket for ticket in tickets
        if isinstance(ticket, dict) and str(ticket.get("customer_id", "")).strip().upper() == target_id
    ]
    return matching_tickets

class KnowledgeRetriever:
    """
    Retriever class wrapping deterministic data loading and retrieval methods.
    """
    def __init__(self, data_path: str = "data"):
        self.data_path = data_path

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        return get_customer(customer_id, data_path=self.data_path)

    def get_tickets(self, customer_id: str) -> List[Dict[str, Any]]:
        return get_tickets(customer_id, data_path=self.data_path)

    def search_articles(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Placeholder for semantic search (not implemented in Step 2).
        """
        raise NotImplementedError("Article semantic search is not implemented yet.")

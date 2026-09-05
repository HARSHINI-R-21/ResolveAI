"""
ResolveAI Local Data & Knowledge Base Retriever
Deterministic data-access functions for loading customers, support tickets, and knowledge base articles.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ARTICLES_DIR = DATA_DIR / "articles"

# Default Keyword Mappings for Deterministic Keyword Matching
KEYWORD_MAPPING = {
    "BILL-001": ["bill", "billing", "charge", "payment", "invoice", "increase", "overage", "fee", "cost", "due"],
    "CONN-001": ["internet", "connection", "outage", "offline", "router", "network", "broadband", "wifi", "wi-fi", "disconnect", "slow", "down"],
    "PLAN-001": ["plan", "upgrade", "package", "subscription", "speed", "tier", "downgrade", "data", "gigabit", "fiber"],
    "REFUND-001": ["refund", "credit", "compensation", "reimbursement", "money", "return", "claim", "reimburse"]
}

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

def load_articles(data_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load all Markdown articles from data/articles/.
    Handles missing directory and individual malformed articles gracefully.
    """
    articles_dir = Path(data_path) / "articles" if data_path else ARTICLES_DIR
    if not articles_dir.exists() or not articles_dir.is_dir():
        print(f"[WARNING] Articles directory not found at: {articles_dir}")
        return []

    articles = []
    for file_path in articles_dir.glob("*.md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse Title (first H1 line)
            title = file_path.stem.replace("_", " ").title()
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()

            # Parse Article ID
            article_id = f"KB-{file_path.stem.upper()}"
            id_match = re.search(r"\*\*Article ID:\*\*\s*([A-Z0-9\-]+)", content, re.IGNORECASE)
            if id_match:
                article_id = id_match.group(1).strip()

            # Parse Category
            category = file_path.stem
            cat_match = re.search(r"\*\*Category:\*\*\s*(.+)$", content, re.MULTILINE)
            if cat_match:
                category = cat_match.group(1).strip()

            articles.append({
                "id": article_id,
                "article_id": article_id,
                "title": title,
                "category": category,
                "filename": file_path.name,
                "file_path": str(file_path),
                "content": content
            })
        except Exception as e:
            print(f"[WARNING] Failed to load article file ({file_path}): {e}")
            continue

    return articles

def search_articles(query: str, category: Optional[str] = None, data_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search articles deterministically using local keyword matching.
    Returns matching articles sorted by relevance score.
    Handles empty queries and missing files gracefully.
    """
    if not query or not isinstance(query, str) or not query.strip():
        return []

    articles = load_articles(data_path)
    if not articles:
        return []

    # Clean and tokenize query
    query_clean = query.lower()
    query_words = set(re.findall(r"\w+", query_clean))

    scored_articles = []
    for article in articles:
        article_id = article.get("article_id", "")
        content_lower = article.get("content", "").lower()
        title_lower = article.get("title", "").lower()

        score = 0

        # Check explicit keyword mapping
        mapped_keywords = KEYWORD_MAPPING.get(article_id, [])
        for kw in mapped_keywords:
            if kw in query_words or kw in query_clean:
                score += 5

        # Check title word overlaps
        for word in query_words:
            if len(word) > 2:
                if word in title_lower:
                    score += 3
                if word in content_lower:
                    score += 1

        # Check category match filter
        if category and category.lower() in article.get("category", "").lower():
            score += 4

        if score > 0:
            scored_article = dict(article)
            scored_article["score"] = score
            scored_articles.append(scored_article)

    # Sort by relevance score descending
    scored_articles.sort(key=lambda x: x["score"], reverse=True)
    return scored_articles

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
        return search_articles(query, category=category, data_path=self.data_path)

# utils/search_history.py

import json
import os
from Config import SEARCH_HISTORY_FILE, MAX_SEARCH_HISTORY, TOP_MOST_SEARCHED

def load_search_history():
    if not os.path.exists(SEARCH_HISTORY_FILE):
        return []
    with open(SEARCH_HISTORY_FILE, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_search_history(history):
    with open(SEARCH_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_search_term(term):
    term = term.strip().lower()
    if not term:
        return
    history = load_search_history()
    history = [h for h in history if h != term]
    history.insert(0, term)
    if len(history) > MAX_SEARCH_HISTORY:
        history = history[:MAX_SEARCH_HISTORY]
    save_search_history(history)

def get_recent_searches():
    return load_search_history()

def get_most_searched():
    if not os.path.exists(SEARCH_HISTORY_FILE):
        return []
    with open(SEARCH_HISTORY_FILE, encoding="utf-8") as f:
        history = json.load(f)
    from collections import Counter
    counts = Counter(history)
    return counts.most_common(TOP_MOST_SEARCHED)

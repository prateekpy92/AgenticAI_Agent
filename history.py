import json
import os
from datetime import datetime
from typing import List, Dict

class HistoryManager:
    def __init__(self, history_file: str = "search_history.json"):
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """Load history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def _save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_entry(self, question: str, answer: str, filename: str):
        """Add a new entry to history"""
        entry = {
            "question": question,
            "answer": answer,
            "filename": filename,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.append(entry)
        self._save_history()
    
    def get_history(self) -> List[Dict]:
        """Get all history entries"""
        return self.history
    
    def clear_history(self):
        """Clear all history"""
        self.history = []
        self._save_history()
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
    
    def get_recent_entries(self, count: int = 10) -> List[Dict]:
        """Get recent history entries"""
        return self.history[-count:] if len(self.history) > count else self.history

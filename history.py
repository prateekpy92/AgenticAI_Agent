import json
import os
from datetime import datetime
from typing import List, Dict
import csv

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
            "id": len(self.history) + 1,
            "question": question,
            "answer": answer,
            "filename": filename,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d")
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
    
    def search_history(self, query: str) -> List[Dict]:
        """Search through history entries"""
        query_lower = query.lower()
        results = []
        
        for entry in self.history:
            if (query_lower in entry['question'].lower() or 
                query_lower in entry['answer'].lower() or 
                query_lower in entry['filename'].lower()):
                results.append(entry)
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get usage statistics"""
        if not self.history:
            return {"total_queries": 0, "unique_files": 0, "date_range": "No data"}
        
        unique_files = set(entry['filename'] for entry in self.history)
        dates = [entry['date'] for entry in self.history]
        
        return {
            "total_queries": len(self.history),
            "unique_files": len(unique_files),
            "date_range": f"{min(dates)} to {max(dates)}" if dates else "No data",
            "most_recent": self.history[-1]['timestamp'] if self.history else "Never"
        }
    
    def export_to_csv(self, filename: str = None) -> str:
        """Export history to CSV file"""
        if not filename:
            filename = f"pdf_qa_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'timestamp', 'filename', 'question', 'answer']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for entry in self.history:
                    writer.writerow({
                        'id': entry['id'],
                        'timestamp': entry['timestamp'],
                        'filename': entry['filename'],
                        'question': entry['question'],
                        'answer': entry['answer']
                    })
            
            return filename
        except Exception as e:
            raise Exception(f"Error exporting to CSV: {str(e)}")

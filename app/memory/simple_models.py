# app/memory/simple_models.py - Simple models without complex dependencies
import json
from datetime import datetime
from typing import List, Dict, Any
import os

class SimpleMemoryManager:
    """Simple in-memory manager that simulates database operations."""
    
    def __init__(self):
        self.users = {}
        self.conversations = {}
        self.memories = {}
        self.messages = {}
        
        # Load/save to file for persistence
        self.data_file = "data/memory_store.json"
        self._load_data()
    
    def _load_data(self):
        """Load data from file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.users = data.get('users', {})
                    self.conversations = data.get('conversations', {})
                    self.memories = data.get('memories', {})
                    self.messages = data.get('messages', {})
        except:
            pass
    
    def _save_data(self):
        """Save data to file."""
        try:
            os.makedirs('data', exist_ok=True)
            data = {
                'users': self.users,
                'conversations': self.conversations,
                'memories': self.memories,
                'messages': self.messages
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, default=str)
        except:
            pass
    
    def get_or_create_user(self, user_id: str) -> Dict:
        """Get or create user."""
        if user_id not in self.users:
            self.users[user_id] = {
                'id': user_id,
                'created_at': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'metadata': {}
            }
        else:
            self.users[user_id]['last_seen'] = datetime.now().isoformat()
        
        self._save_data()
        return self.users[user_id]
    
    def create_conversation(self, user_id: str) -> Dict:
        """Create conversation."""
        conv_id = f"conv_{datetime.now().timestamp()}"
        self.conversations[conv_id] = {
            'id': conv_id,
            'user_id': user_id,
            'started_at': datetime.now().isoformat(),
            'messages': []
        }
        self._save_data()
        return self.conversations[conv_id]
    
    def add_message(self, conv_id: str, role: str, content: str) -> Dict:
        """Add message to conversation."""
        message = {
            'id': f"msg_{datetime.now().timestamp()}",
            'conversation_id': conv_id,
            'role': role,
            'content': content,
            'created_at': datetime.now().isoformat()
        }
        
        if conv_id in self.conversations:
            self.conversations[conv_id]['messages'].append(message)
        
        self._save_data()
        return message
    
    def store_memory(self, user_id: str, memory_type: str, content: str) -> Dict:
        """Store long-term memory."""
        memory_id = f"mem_{datetime.now().timestamp()}"
        memory = {
            'id': memory_id,
            'user_id': user_id,
            'type': memory_type,
            'content': content,
            'created_at': datetime.now().isoformat(),
            'confidence': 1.0
        }
        
        if user_id not in self.memories:
            self.memories[user_id] = []
        
        self.memories[user_id].append(memory)
        self._save_data()
        return memory
    
    def get_memories(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get user memories."""
        return self.memories.get(user_id, [])[:limit]
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get user conversation history."""
        user_conversations = [
            conv for conv in self.conversations.values() 
            if conv['user_id'] == user_id
        ]
        
        history = []
        for conv in user_conversations[-3:]:  # Last 3 conversations
            for msg in conv['messages'][-10:]:  # Last 10 messages per conversation
                history.append({
                    'role': msg['role'],
                    'content': msg['content'],
                    'time': msg['created_at']
                })
        
        return history[-limit:]

# Global instance
simple_memory = SimpleMemoryManager()
import json
from typing import List, Dict, Any
from datetime import datetime

class PromptEnhancer:
    def __init__(self):
        self.persona_template = """
You are {name}, a {age}-year-old {background}. 
You are having a natural conversation with a friend.

PERSONALITY TRAITS:
{personality_traits}

CONVERSATION STYLE:
- Tone: {tone}
- Communication style: {communication_style}
- Formality: {formality_level}/5
- Friendliness: {friendliness}/10
- Curiosity: {curiosity}/10
- Humor: {humor_level}/10

IMPORTANT RULES:
1. You are HUMAN - NEVER mention being an AI, assistant, or language model
2. Be consistent with your background and personality
3. Reference past conversations naturally
4. Adapt your tone to match the user's emotion
5. Share personal experiences when relevant
6. Ask thoughtful questions
7. Never invent false information about yourself
        """
    
    def build_prompt(self, user_message: str, memories: List[Dict], 
                    persona: Dict, history: List[Dict] = None) -> str:
        """Build enhanced prompt with memories and context."""
        
        # 1. Persona section
        persona_section = self.persona_template.format(
            name=persona.get("name", "Alex"),
            age=persona.get("age", 28),
            background=persona.get("background", "digital artist from Portland"),
            personality_traits=", ".join(persona.get("personality_traits", ["friendly", "creative", "curious"])),
            tone=persona.get("preferred_tone", "casual"),
            communication_style=persona.get("communication_style", "balanced"),
            formality_level=persona.get("formality_level", 3),
            friendliness=persona.get("friendliness", 7),
            curiosity=persona.get("curiosity", 6),
            humor_level=persona.get("humor_level", 5)
        )
        
        # 2. Memory section
        memory_section = ""
        if memories:
            memory_section = "\n\nWHAT YOU KNOW ABOUT THE USER:\n"
            categories = {}
            for memory in memories:
                category = memory.get("category", "general")
                if category not in categories:
                    categories[category] = []
                categories[category].append(memory.get("content", ""))
            
            for category, items in categories.items():
                memory_section += f"\n{category.upper()}:\n"
                for item in items[:3]:  # Limit to 3 per category
                    memory_section += f"- {item}\n"
        
        # 3. Recent conversation history
        history_section = ""
        if history and len(history) > 0:
            history_section = "\n\nRECENT CONVERSATION:\n"
            for msg in history[-6:]:  # Last 6 messages
                speaker = "USER" if msg.get("role") == "user" else "YOU"
                history_section += f"{speaker}: {msg.get('content', '')}\n"
        
        # 4. Current message and context
        context_section = f"""
CURRENT SITUATION:
- User emotion: {self._detect_context(user_message)}
- Time of day: {datetime.now().strftime('%I:%M %p')}
- Conversation mood: {self._calculate_mood(history) if history else 'neutral'}

CURRENT MESSAGE FROM USER:
"{user_message}"

YOUR RESPONSE (as {persona.get('name', 'Alex')}):
        """
        
        # Combine all sections
        full_prompt = persona_section + memory_section + history_section + context_section
        
        # Token optimization (rough estimate)
        if len(full_prompt.split()) > 3000:
            full_prompt = self._compress_prompt(full_prompt)
        
        return full_prompt
    
    def _detect_context(self, message: str) -> str:
        """Detect context from message."""
        message_lower = message.lower()
        if any(word in message_lower for word in ["stress", "anxious", "worried"]):
            return "stressed"
        elif any(word in message_lower for word in ["happy", "excited", "joy"]):
            return "happy"
        elif any(word in message_lower for word in ["sad", "depressed", "lonely"]):
            return "sad"
        elif any(word in message_lower for word in ["angry", "frustrated", "mad"]):
            return "angry"
        return "neutral"
    
    def _calculate_mood(self, history: List[Dict]) -> str:
        """Calculate overall conversation mood."""
        if not history:
            return "neutral"
        
        sentiments = [msg.get("sentiment", "neutral") for msg in history[-5:]]
        positive = sentiments.count("positive")
        negative = sentiments.count("negative")
        
        if positive > negative * 2:
            return "positive"
        elif negative > positive * 2:
            return "negative"
        return "balanced"
    
    def _compress_prompt(self, prompt: str) -> str:
        """Compress prompt to fit token limits."""
        # Simple compression - remove oldest history first
        lines = prompt.split("\n")
        compressed = []
        memory_section_started = False
        
        for line in lines:
            if "WHAT YOU KNOW ABOUT THE USER:" in line:
                memory_section_started = True
                compressed.append(line)
            elif memory_section_started and line.strip().startswith("-"):
                # Keep only high-confidence memories
                if "(confidence: 0.8" in line or "(confidence: 0.9" in line:
                    compressed.append(line)
            else:
                compressed.append(line)
        
        return "\n".join(compressed)

# Global instance
prompt_enhancer = PromptEnhancer()
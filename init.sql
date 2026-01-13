-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text similarity
-- For vector search (if using pgvector):
-- CREATE EXTENSION IF NOT EXISTS "vector";

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_memories_user_category 
ON long_term_memories(user_id, category);

CREATE INDEX IF NOT EXISTS idx_memories_confidence 
ON long_term_memories(confidence DESC) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_messages_conversation 
ON messages(conversation_id, created_at);

CREATE INDEX IF NOT EXISTS idx_conversations_user 
ON conversations(user_id, started_at DESC);
-- Drop tables if they exist to start fresh
DROP TABLE IF EXISTS public.knowledge_chat_messages CASCADE;
DROP TABLE IF EXISTS public.knowledge_chat_sessions CASCADE;

-- Create table for Knowledge Chat Sessions
CREATE TABLE IF NOT EXISTS public.knowledge_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New Chat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Create table for Knowledge Chat Messages
CREATE TABLE IF NOT EXISTS public.knowledge_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.knowledge_chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Enable RLS
ALTER TABLE public.knowledge_chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_chat_messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Sessions
CREATE POLICY "Users can view their own knowledge chat sessions"
    ON public.knowledge_chat_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own knowledge chat sessions"
    ON public.knowledge_chat_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own knowledge chat sessions"
    ON public.knowledge_chat_sessions FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own knowledge chat sessions"
    ON public.knowledge_chat_sessions FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for Messages
CREATE POLICY "Users can view messages of their sessions"
    ON public.knowledge_chat_messages FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.knowledge_chat_sessions s
        WHERE s.id = knowledge_chat_messages.session_id AND s.user_id = auth.uid()
    ));

CREATE POLICY "Users can insert messages into their sessions"
    ON public.knowledge_chat_messages FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM public.knowledge_chat_sessions s
        WHERE s.id = knowledge_chat_messages.session_id AND s.user_id = auth.uid()
    ));

-- Grant privileges to authenticated users and service role
GRANT ALL ON public.knowledge_chat_sessions TO authenticated, service_role;
GRANT ALL ON public.knowledge_chat_messages TO authenticated, service_role;

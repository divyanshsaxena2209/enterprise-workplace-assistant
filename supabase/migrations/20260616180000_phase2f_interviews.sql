-- Phase 2F: Interviews
CREATE TABLE IF NOT EXISTS public.interviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'Pending',
    meeting_link TEXT,
    management_notes TEXT,
    candidate_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_interviews_application ON public.interviews (application_id);

DROP TRIGGER IF EXISTS interviews_set_updated_at ON public.interviews;
CREATE TRIGGER interviews_set_updated_at
    BEFORE UPDATE ON public.interviews
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.interviews ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow full access to interviews" ON public.interviews;
CREATE POLICY "Allow full access to interviews"
    ON public.interviews FOR ALL
    USING (true);

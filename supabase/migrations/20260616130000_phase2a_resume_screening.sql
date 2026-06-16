-- =============================================================================
-- Phase 2A: Resume Screening Engine Migration
-- =============================================================================

-- Ensure uuid-ossp is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- 1. Candidates Table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    portfolio_url TEXT,
    is_deleted BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Index for soft delete filtering
CREATE INDEX IF NOT EXISTS idx_candidates_is_deleted ON public.candidates (is_deleted);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS candidates_set_updated_at ON public.candidates;
CREATE TRIGGER candidates_set_updated_at
    BEFORE UPDATE ON public.candidates
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- RLS
ALTER TABLE public.candidates ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow authenticated users to read candidates" ON public.candidates;
CREATE POLICY "Allow authenticated users to read candidates"
    ON public.candidates FOR SELECT
    USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow service role full access to candidates" ON public.candidates;
CREATE POLICY "Allow service role full access to candidates"
    ON public.candidates FOR ALL
    USING (true);


-- ---------------------------------------------------------------------------
-- 2. Resumes Table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES public.candidates(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    parsed_json JSONB DEFAULT '{}'::JSONB,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- RLS
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow authenticated users to read resumes" ON public.resumes;
CREATE POLICY "Allow authenticated users to read resumes"
    ON public.resumes FOR SELECT
    USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow service role full access to resumes" ON public.resumes;
CREATE POLICY "Allow service role full access to resumes"
    ON public.resumes FOR ALL
    USING (true);


-- ---------------------------------------------------------------------------
-- 3. Candidate Scores Table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.candidate_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES public.candidates(id) ON DELETE CASCADE,
    match_percentage INTEGER DEFAULT 0,
    ai_summary TEXT,
    strengths JSONB DEFAULT '[]'::JSONB,
    weaknesses JSONB DEFAULT '[]'::JSONB,
    recommendation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- RLS
ALTER TABLE public.candidate_scores ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow authenticated users to read candidate_scores" ON public.candidate_scores;
CREATE POLICY "Allow authenticated users to read candidate_scores"
    ON public.candidate_scores FOR SELECT
    USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow service role full access to candidate_scores" ON public.candidate_scores;
CREATE POLICY "Allow service role full access to candidate_scores"
    ON public.candidate_scores FOR ALL
    USING (true);

-- ---------------------------------------------------------------------------
-- 4. Storage Bucket Setup
-- ---------------------------------------------------------------------------
-- Insert 'resumes' bucket if it does not exist
INSERT INTO storage.buckets (id, name, public)
VALUES ('resumes', 'resumes', false)
ON CONFLICT (id) DO NOTHING;

-- Allow authenticated users to upload and download from the resumes bucket
DROP POLICY IF EXISTS "Allow authenticated users to upload resumes" ON storage.objects;
CREATE POLICY "Allow authenticated users to upload resumes" 
    ON storage.objects FOR INSERT 
    WITH CHECK (bucket_id = 'resumes' AND auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow authenticated users to read resumes" ON storage.objects;
CREATE POLICY "Allow authenticated users to read resumes" 
    ON storage.objects FOR SELECT 
    USING (bucket_id = 'resumes' AND auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow service role full access to resumes bucket" ON storage.objects;
CREATE POLICY "Allow service role full access to resumes bucket" 
    ON storage.objects FOR ALL 
    USING (bucket_id = 'resumes');

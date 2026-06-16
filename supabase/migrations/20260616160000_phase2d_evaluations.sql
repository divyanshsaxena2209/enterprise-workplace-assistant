-- =============================================================================
-- Phase 2D: AI Candidate Matching & Evaluation Engine
-- =============================================================================

-- Ensure uuid-ossp is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- 1. Recommendation Enum
-- ---------------------------------------------------------------------------
DROP TYPE IF EXISTS recommendation_level CASCADE;
CREATE TYPE recommendation_level AS ENUM ('Strongly Recommend', 'Recommend', 'Consider', 'Reject');

-- ---------------------------------------------------------------------------
-- 2. Clear Legacy Scores
-- ---------------------------------------------------------------------------
-- Legacy scores from Phase 2A were tied only to candidate_id and lacked job context.
-- Since they do not have application_id and we are making application_id NOT NULL,
-- we must clear the table to ensure a safe migration.
TRUNCATE TABLE public.candidate_scores;

-- ---------------------------------------------------------------------------
-- 3. Modify Candidate Scores Table
-- ---------------------------------------------------------------------------
ALTER TABLE public.candidate_scores
    DROP COLUMN IF EXISTS candidate_id,
    ADD COLUMN IF NOT EXISTS application_id UUID UNIQUE NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
    DROP COLUMN IF EXISTS recommendation, -- Drop the old text recommendation
    ADD COLUMN IF NOT EXISTS recommendation recommendation_level NOT NULL,
    DROP COLUMN IF EXISTS created_at,
    ADD COLUMN IF NOT EXISTS evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL;

-- ---------------------------------------------------------------------------
-- 4. Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_candidate_scores_application_id ON public.candidate_scores(application_id);
CREATE INDEX IF NOT EXISTS idx_candidate_scores_recommendation ON public.candidate_scores(recommendation);

-- ---------------------------------------------------------------------------
-- 5. RLS Policies
-- ---------------------------------------------------------------------------
-- Ensure RLS is enabled (it should be from Phase 2A, but just to be safe)
ALTER TABLE public.candidate_scores ENABLE ROW LEVEL SECURITY;

-- Drop legacy policies if they exist
DROP POLICY IF EXISTS "Allow authenticated users to read candidate_scores" ON public.candidate_scores;
DROP POLICY IF EXISTS "Allow service role full access to candidate_scores" ON public.candidate_scores;

-- Management can read all scores
DROP POLICY IF EXISTS "Allow management to read all scores" ON public.candidate_scores;
CREATE POLICY "Allow management to read all scores"
    ON public.candidate_scores FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role = 'MANAGEMENT'
        )
    );

-- Employees can read scores for their own applications
DROP POLICY IF EXISTS "Allow employees to read own application scores" ON public.candidate_scores;
CREATE POLICY "Allow employees to read own application scores"
    ON public.candidate_scores FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.applications 
            WHERE applications.id = candidate_scores.application_id AND applications.user_id = auth.uid()
        )
    );

-- Service role has full access
DROP POLICY IF EXISTS "Allow service role full access to scores" ON public.candidate_scores;
CREATE POLICY "Allow service role full access to scores"
    ON public.candidate_scores FOR ALL
    USING (true);

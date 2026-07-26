




CREATE EXTENSION IF NOT EXISTS "uuid-ossp";




DROP TYPE IF EXISTS recommendation_level CASCADE;
CREATE TYPE recommendation_level AS ENUM ('Strongly Recommend', 'Recommend', 'Consider', 'Reject');







TRUNCATE TABLE public.candidate_scores;




ALTER TABLE public.candidate_scores
    DROP COLUMN IF EXISTS candidate_id,
    ADD COLUMN IF NOT EXISTS application_id UUID UNIQUE NOT NULL REFERENCES public.applications(id) ON DELETE CASCADE,
    DROP COLUMN IF EXISTS recommendation, 
    ADD COLUMN IF NOT EXISTS recommendation recommendation_level NOT NULL,
    DROP COLUMN IF EXISTS created_at,
    ADD COLUMN IF NOT EXISTS evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL;




CREATE INDEX IF NOT EXISTS idx_candidate_scores_application_id ON public.candidate_scores(application_id);
CREATE INDEX IF NOT EXISTS idx_candidate_scores_recommendation ON public.candidate_scores(recommendation);





ALTER TABLE public.candidate_scores ENABLE ROW LEVEL SECURITY;


DROP POLICY IF EXISTS "Allow authenticated users to read candidate_scores" ON public.candidate_scores;
DROP POLICY IF EXISTS "Allow service role full access to candidate_scores" ON public.candidate_scores;


DROP POLICY IF EXISTS "Allow management to read all scores" ON public.candidate_scores;
CREATE POLICY "Allow management to read all scores"
    ON public.candidate_scores FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE profiles.id = auth.uid() AND profiles.role = 'MANAGEMENT'
        )
    );


DROP POLICY IF EXISTS "Allow employees to read own application scores" ON public.candidate_scores;
CREATE POLICY "Allow employees to read own application scores"
    ON public.candidate_scores FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.applications 
            WHERE applications.id = candidate_scores.application_id AND applications.user_id = auth.uid()
        )
    );


DROP POLICY IF EXISTS "Allow service role full access to scores" ON public.candidate_scores;
CREATE POLICY "Allow service role full access to scores"
    ON public.candidate_scores FOR ALL
    USING (true);

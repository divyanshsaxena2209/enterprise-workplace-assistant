-- Management access is request-and-approval, never self-assignment at signup.
-- This table is server-only; the frontend cannot read or change approval state
-- directly with anon/authenticated database credentials.

CREATE TABLE IF NOT EXISTS public.management_access_requests (
    profile_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    requested_role TEXT NOT NULL DEFAULT 'MANAGEMENT'
        CHECK (requested_role = 'MANAGEMENT'),
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    request_note TEXT CHECK (request_note IS NULL OR length(request_note) <= 500),
    reviewer_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    reviewer_note TEXT CHECK (reviewer_note IS NULL OR length(reviewer_note) <= 500),
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS management_access_requests_status_requested_at_idx
    ON public.management_access_requests (status, requested_at ASC);

ALTER TABLE public.management_access_requests ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.management_access_requests FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON TABLE public.management_access_requests TO service_role;

CREATE OR REPLACE FUNCTION public.review_management_access_request(
    p_profile_id UUID,
    p_decision TEXT,
    p_reviewer_id UUID,
    p_reviewer_note TEXT DEFAULT NULL
)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    current_request_status TEXT;
    target_role TEXT;
    target_is_active BOOLEAN;
    changed_rows INTEGER;
    normalized_note TEXT;
BEGIN
    IF p_decision NOT IN ('APPROVE', 'REJECT') THEN
        RAISE EXCEPTION 'Decision must be APPROVE or REJECT'
            USING ERRCODE = '22023';
    END IF;

    normalized_note := NULLIF(btrim(p_reviewer_note), '');
    IF normalized_note IS NOT NULL AND length(normalized_note) > 500 THEN
        RAISE EXCEPTION 'Reviewer note must be 500 characters or fewer'
            USING ERRCODE = '22023';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM public.profiles AS reviewer
        WHERE reviewer.id = p_reviewer_id
          AND reviewer.role::text = 'MANAGEMENT'
          AND reviewer.is_active IS TRUE
    ) THEN
        RAISE EXCEPTION 'An active Management profile is required to review requests'
            USING ERRCODE = '42501';
    END IF;

    SELECT request.status
      INTO current_request_status
      FROM public.management_access_requests AS request
     WHERE request.profile_id = p_profile_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Management access request not found'
            USING ERRCODE = 'P0002';
    END IF;

    IF current_request_status <> 'PENDING' THEN
        RAISE EXCEPTION 'Only pending requests can be reviewed'
            USING ERRCODE = '55000';
    END IF;

    IF p_decision = 'APPROVE' THEN
        SELECT profile.role::text, profile.is_active
          INTO target_role, target_is_active
          FROM public.profiles AS profile
         WHERE profile.id = p_profile_id
         FOR UPDATE;

        IF NOT FOUND OR target_is_active IS NOT TRUE OR target_role <> 'EMPLOYEE' THEN
            RAISE EXCEPTION 'Only active employee profiles can be promoted through this request'
                USING ERRCODE = '55000';
        END IF;

        UPDATE public.profiles
           SET role = 'MANAGEMENT',
               is_management_verified = TRUE,
               updated_at = now()
         WHERE id = p_profile_id;

        UPDATE public.management_access_requests
           SET status = 'APPROVED',
               reviewer_id = p_reviewer_id,
               reviewer_note = normalized_note,
               reviewed_at = now(),
               updated_at = now()
         WHERE profile_id = p_profile_id;

        RETURN 'APPROVED';
    END IF;

    UPDATE public.management_access_requests
       SET status = 'REJECTED',
           reviewer_id = p_reviewer_id,
           reviewer_note = normalized_note,
           reviewed_at = now(),
           updated_at = now()
     WHERE profile_id = p_profile_id;

    RETURN 'REJECTED';
END;
$$;

REVOKE ALL ON FUNCTION public.review_management_access_request(UUID, TEXT, UUID, TEXT)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.review_management_access_request(UUID, TEXT, UUID, TEXT)
    TO service_role;

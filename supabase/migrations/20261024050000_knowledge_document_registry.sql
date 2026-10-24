-- Private, backend-only registry for knowledge document objects.
-- File bytes live in the configured object storage provider; this table stores stable
-- object keys and enough metadata to list/download/delete documents across browsers.
CREATE TABLE IF NOT EXISTS public.knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL CHECK (length(btrim(filename)) > 0),
    storage_provider TEXT NOT NULL CHECK (storage_provider IN ('supabase', 's3')),
    file_key TEXT NOT NULL CHECK (length(btrim(file_key)) > 0),
    file_url TEXT,
    index_source TEXT NOT NULL CHECK (length(btrim(index_source)) > 0),
    pages INTEGER NOT NULL DEFAULT 0 CHECK (pages >= 0),
    chunks INTEGER NOT NULL DEFAULT 0 CHECK (chunks >= 0),
    uploaded_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT knowledge_documents_provider_key_unique UNIQUE (storage_provider, file_key)
);

CREATE INDEX IF NOT EXISTS knowledge_documents_created_at_idx
    ON public.knowledge_documents (created_at DESC);

ALTER TABLE public.knowledge_documents ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.knowledge_documents FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.knowledge_documents TO service_role;

CREATE POLICY knowledge_documents_service_role_only
    ON public.knowledge_documents
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

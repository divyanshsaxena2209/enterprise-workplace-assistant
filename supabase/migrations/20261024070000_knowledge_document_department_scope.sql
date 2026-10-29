-- Add an explicit visibility scope for knowledge/RAG documents.
-- Existing registered documents become company-wide until a manager re-tags them.
ALTER TABLE public.knowledge_documents
    ADD COLUMN IF NOT EXISTS department_scope TEXT NOT NULL DEFAULT 'ALL';

UPDATE public.knowledge_documents
SET department_scope = 'ALL'
WHERE department_scope IS NULL OR btrim(department_scope) = '';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'knowledge_documents_department_scope_check'
          AND conrelid = 'public.knowledge_documents'::regclass
    ) THEN
        ALTER TABLE public.knowledge_documents
            ADD CONSTRAINT knowledge_documents_department_scope_check
            CHECK (
                department_scope = 'ALL'
                OR (
                    length(btrim(department_scope)) BETWEEN 1 AND 100
                    AND upper(btrim(department_scope)) <> 'ALL'
                )
            );
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS knowledge_documents_department_scope_idx
    ON public.knowledge_documents (department_scope);

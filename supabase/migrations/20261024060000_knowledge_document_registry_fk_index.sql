-- Cover the registry uploader foreign key for profile delete/update lookups.
CREATE INDEX IF NOT EXISTS knowledge_documents_uploaded_by_idx
    ON public.knowledge_documents (uploaded_by);

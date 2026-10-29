-- A missing scope must never silently become company-wide.
-- Uploads through the current API always write an explicit scope. REVIEW_REQUIRED
-- protects any future/older writer that omits department_scope.
ALTER TABLE public.knowledge_documents
    ALTER COLUMN department_scope SET DEFAULT 'REVIEW_REQUIRED';

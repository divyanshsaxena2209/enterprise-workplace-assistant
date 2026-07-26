
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'onboarding_status') THEN
        CREATE TYPE onboarding_status AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED');
    END IF;
END $$;


DROP TABLE IF EXISTS public.onboarding_history CASCADE;
DROP TABLE IF EXISTS public.employee_onboarding_progress CASCADE;
DROP TABLE IF EXISTS public.onboarding_steps CASCADE;
DROP TABLE IF EXISTS public.onboarding_templates CASCADE;


CREATE TABLE IF NOT EXISTS public.onboarding_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);


ALTER TABLE public.onboarding_templates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read access to onboarding_templates" ON public.onboarding_templates FOR SELECT USING (true);
CREATE POLICY "Allow management to write onboarding_templates" ON public.onboarding_templates FOR ALL USING (
    EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE profiles.id = auth.uid() AND profiles.role IN ('MANAGEMENT', 'ADMIN', 'HR')
    )
);


CREATE TABLE IF NOT EXISTS public.onboarding_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES public.onboarding_templates(id) ON DELETE CASCADE,
    step_name TEXT NOT NULL,
    description TEXT,
    step_order INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);


ALTER TABLE public.onboarding_steps ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read access to onboarding_steps" ON public.onboarding_steps FOR SELECT USING (true);
CREATE POLICY "Allow management to write onboarding_steps" ON public.onboarding_steps FOR ALL USING (
    EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE profiles.id = auth.uid() AND profiles.role IN ('MANAGEMENT', 'ADMIN', 'HR')
    )
);


alter publication supabase_realtime add table public.onboarding_steps;


CREATE TABLE IF NOT EXISTS public.employee_onboarding_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    step_id UUID REFERENCES public.onboarding_steps(id) ON DELETE CASCADE,
    status onboarding_status DEFAULT 'PENDING'::onboarding_status,
    notes TEXT,
    assigned_date TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    completion_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);


ALTER TABLE public.employee_onboarding_progress REPLICA IDENTITY FULL;


ALTER TABLE public.employee_onboarding_progress ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow employees to view their own progress" ON public.employee_onboarding_progress FOR SELECT USING (auth.uid() = employee_id);
CREATE POLICY "Allow management to read/write all progress" ON public.employee_onboarding_progress FOR ALL USING (
    EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE profiles.id = auth.uid() AND profiles.role IN ('MANAGEMENT', 'ADMIN', 'HR')
    )
);


alter publication supabase_realtime add table public.employee_onboarding_progress;


CREATE TABLE IF NOT EXISTS public.onboarding_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    progress_id UUID REFERENCES public.employee_onboarding_progress(id) ON DELETE CASCADE,
    previous_status TEXT,
    new_status TEXT,
    updated_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);


ALTER TABLE public.onboarding_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow employees to view their own history" ON public.onboarding_history FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.employee_onboarding_progress 
        WHERE employee_onboarding_progress.id = public.onboarding_history.progress_id 
        AND employee_onboarding_progress.employee_id = auth.uid()
    )
);
CREATE POLICY "Allow management to read all history" ON public.onboarding_history FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE profiles.id = auth.uid() AND profiles.role IN ('MANAGEMENT', 'ADMIN', 'HR')
    )
);


CREATE OR REPLACE FUNCTION log_onboarding_history()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status) THEN
        INSERT INTO public.onboarding_history (progress_id, previous_status, new_status, updated_by)
        VALUES (NEW.id, OLD.status::TEXT, NEW.status::TEXT, auth.uid());
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO public.onboarding_history (progress_id, previous_status, new_status, updated_by)
        VALUES (NEW.id, NULL, NEW.status::TEXT, auth.uid());
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


CREATE TRIGGER trigger_employee_onboarding_progress_history
    AFTER INSERT OR UPDATE ON public.employee_onboarding_progress
    FOR EACH ROW EXECUTE FUNCTION log_onboarding_history();



INSERT INTO public.onboarding_templates (name, description, is_default)
VALUES ('Standard Enterprise Onboarding', 'Default company onboarding template.', true)
ON CONFLICT DO NOTHING;

DO $$ 
DECLARE
    default_template_id UUID;
BEGIN
    SELECT id INTO default_template_id FROM public.onboarding_templates WHERE is_default = true LIMIT 1;

    IF default_template_id IS NOT NULL THEN
        -- Before Joining
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Offer Accepted', 'Before Joining', 1);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Employee Profile Created', 'Before Joining', 2);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Account Provisioning Initiated', 'Before Joining', 3);
        
        -- Day 1
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Welcome Session', 'Day 1', 4);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'HR Documentation Verification', 'Day 1', 5);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'ID Card & Access Card Issued', 'Day 1', 6);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Company Policies Acknowledged', 'Day 1', 7);
        
        -- Week 1
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'IT System & Email Setup', 'Week 1', 8);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Development Environment / Software Access', 'Week 1', 9);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Team Introduction', 'Week 1', 10);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Manager Introduction', 'Week 1', 11);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Mandatory Compliance Training', 'Week 1', 12);

        -- Week 2
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Role-specific Training', 'Week 2', 13);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Department Orientation', 'Week 2', 14);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Initial Project Assignment', 'Week 2', 15);

        -- Week 3
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Mentor Check-in', 'Week 3', 16);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Progress Review', 'Week 3', 17);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Pending Task Verification', 'Week 3', 18);

        -- Week 4
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Final Onboarding Review', 'Week 4', 19);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Manager Approval', 'Week 4', 20);
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES (default_template_id, 'Onboarding Completed', 'Week 4', 21);
    END IF;
END $$;

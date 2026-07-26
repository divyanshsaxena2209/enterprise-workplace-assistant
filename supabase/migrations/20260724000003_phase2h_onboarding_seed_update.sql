

DO $$
DECLARE
    v_template_id UUID;
BEGIN
    -- Get the default template
    SELECT id INTO v_template_id FROM public.onboarding_templates WHERE is_default = true LIMIT 1;
    
    IF v_template_id IS NOT NULL THEN
        -- Delete all existing steps for this template
        DELETE FROM public.onboarding_steps WHERE template_id = v_template_id;
        
        -- Insert new standard enterprise steps
        INSERT INTO public.onboarding_steps (template_id, step_name, description, step_order) VALUES
        -- Before Joining
        (v_template_id, 'Offer Accepted', 'Before Joining: Candidate has accepted the job offer.', 1),
        (v_template_id, 'Employee Profile Created', 'Before Joining: Core profile details entered into the system.', 2),
        (v_template_id, 'Account Provisioning Initiated', 'Before Joining: IT triggered to create initial accounts.', 3),
        
        -- Day 1
        (v_template_id, 'Welcome Session', 'Day 1: HR Welcome and Orientation Session.', 4),
        (v_template_id, 'HR Documentation Verification', 'Day 1: Verification of I-9, Tax forms, and banking details.', 5),
        (v_template_id, 'ID Card & Access Card Issued', 'Day 1: Building access provisions granted.', 6),
        (v_template_id, 'Company Policies Acknowledged', 'Day 1: Read and sign the employee handbook.', 7),
        
        -- Week 1
        (v_template_id, 'IT System & Email Setup', 'Week 1: Finalize work email, SSO, and hardware setup.', 8),
        (v_template_id, 'Development Environment / Software Access', 'Week 1: Gain access to role-specific tools and repos.', 9),
        (v_template_id, 'Team Introduction', 'Week 1: Formal introduction to immediate team members.', 10),
        (v_template_id, 'Manager Introduction', 'Week 1: 1-on-1 meeting with direct manager.', 11),
        (v_template_id, 'Mandatory Compliance Training', 'Week 1: Security and Compliance video courses.', 12),
        
        -- Week 2
        (v_template_id, 'Role-specific Training', 'Week 2: Deep dive into daily responsibilities.', 13),
        (v_template_id, 'Department Orientation', 'Week 2: Broader department goals and structure.', 14),
        (v_template_id, 'Initial Project Assignment', 'Week 2: Assign first starter project or task.', 15),
        
        -- Week 3
        (v_template_id, 'Mentor Check-in', 'Week 3: Feedback session with assigned onboarding buddy.', 16),
        (v_template_id, 'Progress Review', 'Week 3: HR 30-day progress check.', 17),
        (v_template_id, 'Pending Task Verification', 'Week 3: Follow up on any incomplete administrative tasks.', 18),
        
        -- Week 4
        (v_template_id, 'Final Onboarding Review', 'Week 4: Comprehensive review of the first 30 days.', 19),
        (v_template_id, 'Manager Approval', 'Week 4: Manager signs off on completed onboarding.', 20),
        (v_template_id, 'Onboarding Completed', 'Week 4: Employee is fully transitioned into standard workflow.', 21);
    END IF;
END $$;

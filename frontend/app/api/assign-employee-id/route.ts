import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export async function POST(request: Request) {
  try {
    const { employeeId, newEmployeeId } = await request.json();

    if (!employeeId || !newEmployeeId) {
      return NextResponse.json({ error: 'Missing parameters' }, { status: 400 });
    }

    
    
    
    const path = require('path');
    const dotenv = require('dotenv');
    
    
    const envPath = path.resolve(process.cwd(), '../backend/.env');
    const result = dotenv.config({ path: envPath });
    
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || result.parsed?.SUPABASE_URL;
    const serviceRoleKey = result.parsed?.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !serviceRoleKey) {
        return NextResponse.json({ error: 'Server configuration error' }, { status: 500 });
    }

    const supabaseAdmin = createClient(supabaseUrl, serviceRoleKey);

    const { error } = await supabaseAdmin
      .from('profiles')
      .update({ employee_id: newEmployeeId })
      .eq('id', employeeId);

    if (error) {
      console.error("Error updating employee_id via admin:", error);
      throw error;
    }

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error("Assign ID Route Error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

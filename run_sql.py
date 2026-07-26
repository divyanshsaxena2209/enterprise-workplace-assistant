import asyncio
import os
from supabase import create_client

async def main():
    import psycopg2
    
    conn = psycopg2.connect("postgresql://postgres:postgres@127.0.0.1:54322/postgres")
    conn.autocommit = True
    cursor = conn.cursor()
    
    with open("supabase/migrations/20260724000000_phase2h_onboarding.sql", "r") as f:
        sql = f.read()
    
    try:
        cursor.execute(sql)
        print("SQL executed successfully.")
    except Exception as e:
        print(f"Error executing SQL: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    asyncio.run(main())

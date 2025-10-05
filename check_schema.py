#!/usr/bin/env python3
"""
Quick database schema checker
"""
import asyncio
import asyncpg

async def check_schema():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/defhack")
    
    # Check sensor_reading table structure
    print("📡 SENSOR_READING TABLE STRUCTURE:")
    query = """
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = 'sensor_reading'
    ORDER BY ordinal_position
    """
    rows = await conn.fetch(query)
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']} ({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
    
    print("\n📚 INTEL_DOC TABLE STRUCTURE:")
    query = """
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = 'intel_doc'
    ORDER BY ordinal_position
    """
    rows = await conn.fetch(query)
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']} ({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
    
    print("\n📄 DOC_CHUNK TABLE STRUCTURE:")
    query = """
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = 'doc_chunk'
    ORDER BY ordinal_position
    """
    rows = await conn.fetch(query)
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']} ({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_schema())
#!/usr/bin/env python3
"""
Debug the document search issue
"""
import asyncio
import asyncpg
from sqlalchemy import create_engine, text as sql
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

async def test_direct_db():
    """Test direct asyncpg connection"""
    print("=== DIRECT ASYNCPG TEST ===")
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/defhack")
    
    query = "BTG vulnerabilities"
    rows = await conn.fetch("""
      SELECT c.doc_id, c.chunk_idx, c.page, c.para, c.line_start, c.line_end,
             c.step_id, c.section, substring(c.text, 1, 200) as text_sample,
             ts_rank_cd(c.tsv, plainto_tsquery('english', $1)) AS tscore
      FROM doc_chunk c
      WHERE c.tsv @@ plainto_tsquery('english', $1)
      ORDER BY tscore DESC
      LIMIT 3
    """, query)
    
    print(f"Direct asyncpg found {len(rows)} results:")
    for row in rows:
        print(f"- Doc {row['doc_id']}, p{row['page']}, para{row['para']}: {row['text_sample']}...")
        print(f"  Score: {row['tscore']:.4f}")
    
    await conn.close()

async def test_sqlalchemy():
    """Test SQLAlchemy async engine (like the API uses)"""
    print("\n=== SQLALCHEMY ASYNC TEST ===")
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/defhack")
    
    query = "BTG vulnerabilities"
    async with engine.begin() as conn:
        try:
            result = await conn.execute(sql("""
              SELECT c.doc_id, c.chunk_idx, c.page, c.para, c.line_start, c.line_end,
                     c.step_id, c.section, substring(c.text, 1, 200) as text_sample,
                     ts_rank_cd(c.tsv, plainto_tsquery('english', :qtxt)) AS tscore
              FROM doc_chunk c
              WHERE c.tsv @@ plainto_tsquery('english', :qtxt)
              ORDER BY tscore DESC
              LIMIT :k;
            """), {"qtxt": query, "k": 3})
            
            rows = result.mappings().all()
            print(f"SQLAlchemy found {len(rows)} results:")
            for row in rows:
                print(f"- Doc {row['doc_id']}, p{row['page']}, para{row['para']}: {row['text_sample']}...")
                print(f"  Score: {row['tscore']:.4f}")
        except Exception as e:
            print(f"SQLAlchemy error: {e}")
    
    await engine.dispose()

async def main():
    await test_direct_db()
    await test_sqlalchemy()

if __name__ == "__main__":
    asyncio.run(main())
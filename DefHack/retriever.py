from openai import OpenAI
from sqlalchemy import text as sql
from .config import settings

client = OpenAI()

async def hybrid_search(db, query: str, k: int = 8):
    # Full-text search using PostgreSQL's built-in text search vectors
    try:
        print(f"[DEBUG] Searching for: '{query}' with k={k}")
        rows = (await db.execute(sql("""
          SELECT c.doc_id, c.chunk_idx, c.page, c.para, c.line_start, c.line_end,
                 c.step_id, c.section, c.text,
                 ts_rank_cd(c.tsv, plainto_tsquery('english', :qtxt)) AS tscore
          FROM doc_chunk c
          WHERE c.tsv @@ plainto_tsquery('english', :qtxt)
          ORDER BY tscore DESC
          LIMIT :k;
        """), {"qtxt": query, "k": k})).mappings().all()

        print(f"[DEBUG] Found {len(rows)} search results")
        results = [{
          "doc_id": str(r["doc_id"]),
          "page": r["page"], "para": r["para"],
          "line_start": r["line_start"], "line_end": r["line_end"],
          "step_id": r["step_id"], "section": r["section"],
          "text": r["text"]
        } for r in rows]
        
        return results
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        import traceback
        traceback.print_exc()
        return []
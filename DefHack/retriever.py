from openai import OpenAI
from sqlalchemy import text as sql
from .config import settings

client = OpenAI()

async def hybrid_search(db, query: str, k: int = 8):
    # For now, just do text search until we get pgvector working
    # Since no documents are uploaded yet, return empty list
    try:
        rows = (await db.execute(sql("""
          SELECT c.doc_id, c.chunk_idx, c.page, c.para, c.line_start, c.line_end,
                 c.step_id, c.section, c.text,
                 ts_rank_cd(c.tsv, plainto_tsquery('english', :qtxt)) AS tscore
          FROM doc_chunk c
          WHERE c.tsv @@ plainto_tsquery('english', :qtxt)
          ORDER BY tscore DESC
          LIMIT :k;
        """), {"qtxt": query, "k": k})).mappings().all()

        return [{
          "doc_id": str(r["doc_id"]),
          "page": r["page"], "para": r["para"],
          "line_start": r["line_start"], "line_end": r["line_end"],
          "step_id": r["step_id"], "section": r["section"],
          "text": r["text"]
        } for r in rows]
    except Exception as e:
        # If there's an error (like no documents), return empty list
        print(f"Search error: {e}")
        return []
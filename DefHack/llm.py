from openai import OpenAI
client = OpenAI()

SYSTEM = """You are a staff officer. Draft clear, concise military orders or reports.
- Only use the provided CONTEXT (sensor reports + intel document chunks).
- Keep all locations in MGRS (do not convert).
- Cite sources inline:
  - [R:<report_uuid>] for reports
  - [D:<doc_id> p<page> ¶<para>#<step_id?>] for PDFs
  - [D:<doc_id> lines <line_start>–<line_end>] for text docs
- If information is insufficient, say so plainly."""

def _cite(c):
    if c.get("page"):
        return f"[D:{c['doc_id']} p{c['page']} ¶{c['para']}" + (f"#{c['step_id']}]" if c.get("step_id") else "]")
    if c.get("line_start"):
        return f"[D:{c['doc_id']} lines {c['line_start']}–{c['line_end']}]"
    return f"[D:{c['doc_id']}]"

def build_prompt(query: str, ctx: list[dict]):
    bullets = []
    for c in ctx:
        bullets.append(f"- ({_cite(c)}) {c['text'][:1000]}")
    return f"QUERY: {query}\nCONTEXT:\n" + "\n".join(bullets) + "\n\nWrite the order/report with citations."

async def generate_order_from_context(query: str, ctx: list[dict]):
    prompt = build_prompt(query, ctx)
    # Using chat completions instead of responses API for broader compatibility
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":SYSTEM},
            {"role":"user","content":prompt}
        ],
        temperature=0.2
    )
    return resp.choices[0].message.content, []  # you can parse citations if you want a structured list
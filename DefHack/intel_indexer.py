import io, hashlib, re
from pypdf import PdfReader
from sqlalchemy import text as sql
from .storage import put_object
from .embeddings import embed_texts

STEP_RE = re.compile(r"^\s*(?:Step|STEP)\s*[:\-]?\s*([A-Z0-9.\-]+)", re.I)
SECTION_TAGS = {
    "condition": re.compile(r"^\s*(?:if|condition)\b[:\-]?", re.I),
    "action":    re.compile(r"^\s*(?:then|action)\b[:\-]?", re.I),
    "notes":     re.compile(r"^\s*(?:note|warning|caution)\b[:\-]?", re.I),
}

def txt_blocks_with_lines(raw: str, max_chars=1200):
    lines = raw.splitlines()
    out, buf, start = [], "", None
    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if not s and buf:
            out.append((buf, start, i-1)); buf=""; start=None; continue
        if not s:
            continue
        if start is None: start = i
        if len(buf)+len(s)+1 > max_chars:
            out.append((buf, start, i-1)); buf=s; start=i
        else:
            buf = (buf + " " + s).strip() if buf else s
    if buf: out.append((buf, start, len(lines)))
    return out

def pdf_blocks(text: str, max_chars=1200):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    blocks, cur = [], {"step_id": None, "section": None, "buf": ""}
    def flush():
        if cur["buf"]:
            blocks.append(cur.copy()); cur["buf"]=""
    for line in lines:
        m = STEP_RE.match(line)
        if m: flush(); cur={"step_id": m.group(1), "section": "Step", "buf": line}; continue
        hit = next((n for n,rx in SECTION_TAGS.items() if rx.match(line)), None)
        if hit: flush(); cur={"step_id": cur.get("step_id"), "section": hit.title(), "buf": line}; continue
        if len(cur["buf"])+len(line)+1 > max_chars:
            flush(); cur["buf"]=line
        else:
            cur["buf"] = (cur["buf"] + " " + line).strip()
    flush()
    return blocks

async def upload_and_index_intel(db, file, title, version=None, lang=None, origin=None, adversary=None, published_at=None):
    data = await file.read()
    checksum = hashlib.sha256(data).hexdigest()
    source_type = "pdf" if file.filename.lower().endswith(".pdf") else "text"
    key = f"intel/{checksum[:12]}_{file.filename}"
    put_object(key, data)
    
    # Parse published_at string to date if provided
    if published_at:
        from datetime import datetime
        try:
            published_at = datetime.fromisoformat(published_at).date()
        except ValueError:
            published_at = None

    await db.execute(sql("""
      INSERT INTO intel_doc(title,version,object_key,checksum,source_type,lang,origin,adversary,published_at)
      VALUES (:t,:v,:k,:c,:st,:lg,:or,:ad,:pa)
    """), {"t":title,"v":version,"k":key,"c":checksum,"st":source_type,"lg":lang,"or":origin,"ad":adversary,"pa":published_at})
    doc_id = (await db.execute(sql("SELECT id FROM intel_doc WHERE checksum=:c"), {"c":checksum})).scalar()

    rows, texts, idx = [], [], 0
    if source_type == "pdf":
        reader = PdfReader(io.BytesIO(data))
        for p, page in enumerate(reader.pages, start=1):
            raw = page.extract_text() or ""
            blocks = pdf_blocks(raw) or [{"buf": raw, "step_id": None, "section": None}]
            para = 0
            for b in blocks:
                t = (b["buf"] or "").strip()
                if not t: continue
                para += 1
                rows.append((doc_id, idx, t, p, para, None, None, b["step_id"], b["section"]))
                texts.append(t); idx += 1
    else:
        raw = data.decode(errors="ignore")
        for (t, ls, le) in txt_blocks_with_lines(raw):
            rows.append((doc_id, idx, t, None, None, ls, le, None, None))
            texts.append(t); idx += 1

    if texts:
        embs = await embed_texts(texts)
        # Store embeddings as JSON strings for now
        import json
        embs_json = [json.dumps(emb) for emb in embs]
        
        # Insert chunks one by one to avoid complex array syntax issues
        for i, (doc_id_val, idx_val, text_val, page_val, para_val, lstart_val, lend_val, step_val, sect_val) in enumerate(rows):
            await db.execute(sql("""
              INSERT INTO doc_chunk(doc_id,chunk_idx,text,page,para,line_start,line_end,step_id,section,embedding)
              VALUES (:doc_id,:idx,:text,:page,:para,:lstart,:lend,:step,:sect,:emb)
            """), {
              "doc_id": doc_id_val, "idx": idx_val, "text": text_val,
              "page": page_val, "para": para_val, "lstart": lstart_val, "lend": lend_val,
              "step": step_val, "sect": sect_val, "emb": embs_json[i]
            })
        await db.commit()

    return {"doc_id": str(doc_id), "chunks": len(rows), "source_type": source_type}
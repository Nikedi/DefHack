from fastapi import FastAPI, UploadFile, File, Form, Depends, Header, HTTPException
from datetime import datetime
from .db import SessionLocal
from .config import settings
from .schemas import SensorObservationIn
from .ingest_sensor import save_sensor
from .intel_indexer import upload_and_index_intel
from .retriever import hybrid_search
from .llm import generate_order_from_context

app = FastAPI(title="Intel DB")

# API now uses database polling for notifications - no direct notification code needed

async def get_db():
    async with SessionLocal() as s:
        yield s

def enforce_write_key(x_api_key: str | None):
    if x_api_key != settings.API_WRITE_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# Notification functions removed - using database polling approach instead

@app.post("/ingest/sensor")
async def ingest_sensor(payload: SensorObservationIn, db=Depends(get_db), x_api_key: str | None = Header(None)):
    enforce_write_key(x_api_key)
    
    # Modify payload to mark for leader notification polling
    payload_dict = payload.model_dump()
    
    # Mark sensor_id as 'UNSENT' to trigger Telegram bot polling
    if payload_dict.get('sensor_id'):
        payload_dict['sensor_id'] = 'UNSENT'
    else:
        payload_dict['sensor_id'] = 'UNSENT'
    
    # Save observation to database - it will be picked up by Telegram bot polling
    result = await save_sensor(db, payload_dict)
    
    # Add notification status to response
    result['notification_status'] = 'queued_for_polling'
    
    return result

@app.post("/intel/upload")
async def intel_upload(
    file: UploadFile = File(...),
    title: str = Form(...),
    version: str | None = Form(None),
    lang: str | None = Form(None),
    origin: str | None = Form(None),
    adversary: str | None = Form(None),
    published_at: str | None = Form(None),
    db=Depends(get_db),
    x_api_key: str | None = Header(None)
):
    enforce_write_key(x_api_key)
    return await upload_and_index_intel(
        db=db, file=file, title=title, version=version,
        lang=lang, origin=origin, adversary=adversary, published_at=published_at
    )

@app.get("/search")
async def search(q: str, k: int = 8, db=Depends(get_db)):
    return await hybrid_search(db, q, k)

@app.post("/orders/draft")
async def draft_order(query: str, k: int = 10, db=Depends(get_db)):
    ctx = await hybrid_search(db, query, k)
    text, citations = await generate_order_from_context(query, ctx)
    return {"body": text, "citations": citations}
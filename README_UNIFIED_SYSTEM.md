# DefHack Unified Data Input System

## Overview
The DefHack intelligence system now has a **consistent, unified interface** for adding both tactical sensor observations and strategic intelligence documents. This eliminates previous inconsistencies and provides multiple easy-to-use input methods.

## 📡 Data Types

### 1. Tactical Sensor Observations
**Purpose**: Real-time field reports, tactical sightings, operational data
**Storage**: `sensor_reading` database table
**Schema**: `SensorObservationIn` → `SensorObservation`

**Required Fields**:
- `time`: When observed (ISO 8601 format)
- `mgrs`: Location in MGRS format (e.g., "35VLG8472571866") 
- `what`: What was observed (e.g., "T-72 Tank", "Infantry Squad")
- `confidence`: Observer confidence (0-100)
- `sensor_id`: Sensor/equipment identifier
- `observer_signature`: Observer identification

**Optional Fields**:
- `amount`: Quantity observed
- `unit`: Observing unit/team

### 2. Intelligence Documents  
**Purpose**: Strategic reports, PDFs, doctrinal materials, analysis documents
**Storage**: `intel_doc` + `doc_chunk` tables (searchable)
**Schema**: `IntelligenceDocumentMetadata`

**Required Fields**:
- `title`: Document title
- `file`: PDF/TXT file to upload

**Optional Fields**:
- `version`, `lang`, `origin`, `adversary`, `published_at`, `classification`, `document_type`

## 🚀 Input Methods

### Method 1: Python Client (Recommended)
```python
from defhack_unified_input import DefHackClient

client = DefHackClient()

# Add tactical observation
observation = {
    "time": "2025-10-04T15:30:00+00:00",
    "mgrs": "35VLG8476572200", 
    "what": "Infantry Squad",
    "amount": 8,
    "confidence": 92,
    "sensor_id": "OPTIC_001",
    "observer_signature": "MikeAlpha"
}
result = client.add_sensor_observation(observation)

# Upload intelligence document
result = client.upload_intelligence_document(
    "report.pdf",
    title="Tactical Analysis Report",
    document_type="doctrinal",
    origin="US Army"
)

# Search database
results = client.search("BTG tactics", k=5)
```

### Method 2: Command Line Interface
```bash
# Add observation
python defhack_cli.py obs --what "T-72 Tank" --amount 2 --mgrs "35VLG8472571866" --observer "Alpha6" --confidence 95

# Upload document
python defhack_cli.py doc --file "report.pdf" --title "Tactical Analysis" --type "doctrinal"

# Search
python defhack_cli.py search --query "BTG tactics" --limit 5
```

### Method 3: Direct API Calls
```bash
# Tactical observation
curl -X POST "http://localhost:8080/ingest/sensor" \
  -H "X-API-Key: 583C55345736D7218355BCB51AA47" \
  -H "Content-Type: application/json" \
  -d '{
    "time": "2025-10-04T15:30:00+00:00",
    "mgrs": "35VLG8476572200",
    "what": "Infantry Squad", 
    "amount": 8,
    "confidence": 92,
    "sensor_id": "OPTIC_001",
    "observer_signature": "MikeAlpha"
  }'

# Intelligence document (multipart form)
curl -X POST "http://localhost:8080/intel/upload" \
  -H "X-API-Key: 583C55345736D7218355BCB51AA47" \
  -F "file=@report.pdf" \
  -F "title=Tactical Analysis Report" \
  -F "document_type=doctrinal"
```

## 📊 Current System Status

### Data Successfully Loaded:
**Tactical Observations** (7 total):
1. Report ID 1: 7 Soldiers w/ Rifle (JackJames)
2. Report ID 2: 2 MT-LBs (JimBean)  
3. Report ID 3: 3 T-72 Tanks (SarahConnor)
4. Report ID 4: 8 Infantry Squad (MikeAlpha)
5. Report ID 5: 1 BMP-2 IFV (EchoSix)
6. Report ID 6: 3 Supply Trucks (SkyWatcher)
7. Report ID 7: 4 Reconnaissance Team (Delta7)

**Intelligence Documents** (2 total):
1. Doc ID 5: Russian BTG Analysis - Fiore 2017 (46 chunks)
2. Doc ID 6: BTG Employment Study - Baez 2022 (30 chunks)

### API Endpoints:
- `POST /ingest/sensor` - Add tactical observations
- `POST /intel/upload` - Upload intelligence documents  
- `GET /search` - Search all intelligence data
- `POST /orders/draft` - Generate AI reports

## 🎯 Key Improvements

✅ **Consistent Terminology**: "Sensor Observations" vs "Intelligence Documents"
✅ **Unified Client**: Single DefHackClient class for all operations  
✅ **Multiple Interfaces**: Python, CLI, and direct API access
✅ **Better Documentation**: Clear schemas with field descriptions
✅ **Type Safety**: Proper Pydantic validation for all inputs
✅ **Error Handling**: Comprehensive error reporting and validation

## 🔍 Search & Analysis

The system now clearly distinguishes:
- **Tactical data** goes to `sensor_reading` table (operational tracking)
- **Strategic data** goes to `doc_chunk` table (searchable intelligence)
- **Search queries** find relevant document chunks
- **AI analysis** can combine both data types for comprehensive reports

The DefHack system is now **production-ready** with consistent, easy-to-use interfaces for all intelligence data input! 🎉
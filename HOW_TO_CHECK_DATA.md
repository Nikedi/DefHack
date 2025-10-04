# How to Check Observations and Documents in DefHack

## Quick Overview
```bash
python quick_summary.py
```
This shows system stats and recent data.

## Detailed Methods

### 1. 📡 Sensor Observations (Tactical Data)
**Location**: PostgreSQL `sensor_reading` table  
**Why not in search?**: Sensor data is structured tactical data, not searchable text

#### View All Observations:
```bash
python database_inspector.py
```

#### Add New Observation:
```bash
python defhack_cli.py obs --what "T-72 Tank" --amount 3 --mgrs "35VLG8472571866" --observer "Alpha6" --confidence 95
```

#### Current Observations (7 total):
1. Reconnaissance Team (4 units, 93% confidence) - Delta7
2. Supply Truck (3 units, 88% confidence) - SkyWatcher  
3. BMP-2 IFV (1 unit, 95% confidence) - EchoSix
4. Infantry Squad (8 units, 92% confidence) - MikeAlpha
5. T-72 Tank (3 units, 95% confidence) - SarahConnor
6. MT-LB (2 units, 85% confidence) - JimBean
7. Soldier w/ Rifle (7 units, 90% confidence) - JackJames

### 2. 📚 Intelligence Documents (Strategic Data)
**Location**: PostgreSQL `intel_doc` + `doc_chunk` tables  
**Searchable**: Yes, via full-text search and embeddings

#### Search Documents:
```bash
python defhack_cli.py search --query "BTG tactics"
python defhack_cli.py search --query "Russian analysis"
```

#### Upload New Document:
```bash
python defhack_cli.py doc --file "report.pdf" --title "Military Analysis" --type "doctrinal"
```

#### Current Documents (4 total, 152 chunks):
1. **BTG Tactical Employment Study - Baez 2022** (30 chunks)
2. **Russian Battalion Tactical Group Analysis - Fiore 2017** (46 chunks) 
3. **Intelligence Report - Baez 2022** (30 chunks)
4. **Intelligence Report - Fiore 2017** (46 chunks)

## 3. 🔍 Search Interface

### Python Client:
```python
from defhack_unified_input import DefHackClient

client = DefHackClient()

# Search intelligence documents
results = client.search("BTG tactics", k=5)
for result in results:
    print(f"Doc {result['doc_id']}, Page {result['page']}: {result['text'][:100]}...")
```

### API Direct:
```bash
curl "http://localhost:8080/search?q=tactical&k=3"
```

## 4. 🗄️ Database Direct Access

### Connection Info:
- **Host**: localhost:5432
- **Database**: defhack  
- **User**: postgres
- **Password**: postgres

### Key Tables:
- `sensor_reading` - Tactical observations
- `intel_doc` - Document metadata
- `doc_chunk` - Searchable document chunks

### Sample Queries:
```sql
-- View all observations
SELECT * FROM sensor_reading ORDER BY received_at DESC;

-- View all documents  
SELECT id, title, source_type, created_at FROM intel_doc;

-- View document chunks
SELECT doc_id, page, text FROM doc_chunk WHERE doc_id = 5 LIMIT 5;

-- Search specific content
SELECT doc_id, page, text FROM doc_chunk WHERE text ILIKE '%BTG%' LIMIT 3;
```

## 5. 📊 System Status

### Current Status:
- ✅ **7 tactical observations** stored and retrievable
- ✅ **4 intelligence documents** uploaded and indexed  
- ✅ **152 document chunks** searchable
- ✅ **Search API** working
- ✅ **Upload APIs** working

### Data Flow:
1. **Sensor Observations** → `sensor_reading` table → Database queries only
2. **Intelligence Documents** → `intel_doc` + `doc_chunk` tables → Searchable via API

## 6. 🛠️ Tools Available

| Tool | Purpose | Usage |
|------|---------|--------|
| `quick_summary.py` | System overview | `python quick_summary.py` |
| `database_inspector.py` | Full database view | `python database_inspector.py` |
| `defhack_cli.py` | Add/search data | `python defhack_cli.py [obs/doc/search]` |  
| `defhack_unified_input.py` | Python client | Import DefHackClient class |

The key distinction is:
- **Sensor observations** = Tactical field data (database only)
- **Intelligence documents** = Strategic analysis (searchable text)

Both are fully functional and ready for intelligence analysis!
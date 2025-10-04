# DefHack - Intel Database System

A Dockerized intelligence database system with sensor data ingestion, document indexing, and AI-powered retrieval and report generation.

## Features

- **Sensor Data Ingestion**: Accepts normalized sensor observations with MGRS coordinates and observer signatures
- **Document Intelligence**: Uploads and indexes PDF/TXT intel documents with vector embeddings
- **Hybrid Search**: Combines vector similarity and full-text search for optimal retrieval
- **AI Report Generation**: Uses OpenAI GPT models to draft military orders/reports with proper citations
- **Database**: PostgreSQL 16 + TimescaleDB (time-series) + pgvector (vector search) + pg_trgm (fuzzy search)
- **Storage**: MinIO S3-compatible object storage for documents
- **Security**: API key authentication for write operations

## Tech Stack

- **Backend**: FastAPI (Python 3.11), SQLAlchemy (async), Alembic migrations
- **Database**: PostgreSQL 16 + TimescaleDB + pgvector + pg_trgm
- **Storage**: MinIO (S3 API) for PDFs/TXT files
- **AI**: OpenAI text-embedding-3-large (3072-d) + GPT-4o-mini
- **Deployment**: Docker Compose

## Quick Start

### 1. Clone and Setup Environment

```bash
git clone <your-repo>
cd DefHack
cp .env.example .env
```

Edit `.env` with your OpenAI API key and desired API write key:
```env
OPENAI_API_KEY=your_openai_api_key_here
API_WRITE_KEY=your_secure_write_key_here
```

### 2. Start the Stack

```bash
docker-compose up --build -d
```

This starts:
- PostgreSQL database on port 5432
- MinIO on ports 9000 (API) and 9001 (console)
- FastAPI application on port 8080

### 3. Create MinIO Bucket (One-time)

Visit http://localhost:9001 (MinIO console)
- Login: `minio` / `minio123`
- Create bucket named `intel`

### 4. Run Database Migrations

```bash
# Install alembic locally or use docker exec
docker-compose exec api alembic upgrade head
```

## API Endpoints

### POST /ingest/sensor
Ingest sensor observations with MGRS coordinates.

**Headers**: `X-API-Key: your_write_key`

**Body** (JSON):
```json
{
  "time": "2025-10-03T09:40:00Z",
  "mgrs": "35VKH12345678",
  "what": "Vehicular movement N->S",
  "amount": 3,
  "confidence": 80,
  "sensor_id": "uav-17",
  "unit": "Coy A",
  "observer_signature": "Sensor 1, Team A"
}
```

### POST /intel/upload
Upload and index PDF or TXT intel documents.

**Headers**: `X-API-Key: your_write_key`

**Body** (multipart/form-data):
- `file`: PDF or TXT file
- `title`: Document title (required)
- `version`: Version string (optional)
- `lang`: Language code (optional)
- `origin`: Source type, e.g., "OSINT" (optional)
- `adversary`: Adversary code, e.g., "RU" (optional)
- `published_at`: Publication date (optional)

### GET /search
Search indexed documents with hybrid vector + keyword search.

**Parameters**:
- `q`: Search query (required)
- `k`: Number of results to return (default: 8)

**Example**: `GET /search?q=btg%20logistics&k=5`

### POST /orders/draft
Generate AI-powered military orders/reports with citations.

**Body** (JSON):
```json
{
  "query": "Prepare hasty defense based on latest BTG approach near 35VKH12345678",
  "k": 10
}
```

## Testing Examples

### 1. Ingest Sensor Data

```bash
curl -X POST "http://localhost:8080/ingest/sensor" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 583C55345736D7218355BCB51AA47" \
  -d '{
    "time":"2025-10-03T09:40:00Z",
    "mgrs":"35VKH12345678",
    "what":"Vehicular movement N->S",
    "amount":3,
    "confidence":80,
    "sensor_id":"uav-17",
    "unit":"Coy A",
    "observer_signature":"Sensor 1, Team A"
  }'
```

### 2. Upload Intel Document

```bash
# Upload PDF
curl -X POST "http://localhost:8080/intel/upload" \
  -H "X-API-Key: 583C55345736D7218355BCB51AA47" \
  -F "title=Enemy BTG TTPs" \
  -F "version=v1" \
  -F "origin=OSINT" \
  -F "adversary=RU" \
  -F "file=@./Documents/3Baez22.pdf"

# Upload text file
curl -X POST "http://localhost:8080/intel/upload" \
  -H "X-API-Key: 583C55345736D7218355BCB51AA47" \
  -F "title=Tactical Procedures Manual" \
  -F "version=v2" \
  -F "lang=en" \
  -F "file=@./Documents/tactics.txt;type=text/plain"
```

### 3. Search Documents

```bash
curl "http://localhost:8080/search?q=btg%20logistics&k=5"
```

### 4. Generate Report

```bash
curl -X POST "http://localhost:8080/orders/draft" \
  -H "Content-Type: application/json" \
  -d '{"query":"Prepare hasty defense based on latest BTG approach near 35VKH12345678"}'
```

## Data Schemas

### Sensor Reading Schema
- `time`: ISO-8601 timestamp (required)
- `mgrs`: MGRS coordinate string, uppercase, no spaces (required)
- `what`: Description of observation (required) 
- `amount`: Numeric quantity (optional)
- `confidence`: Confidence level 0-100 (required)
- `sensor_id`: Sensor identifier (required)
- `unit`: Military unit (optional)
- `observer_signature`: Observer identification (required, min 3 chars)

### MGRS Format
Valid MGRS format: `^[0-9]{1,2}[C-HJ-NP-X][A-HJ-NP-Z]{2}[0-9]{2,10}$`

Examples:
- `35VKH12` (2-digit precision)
- `35VKH1234` (4-digit precision)  
- `35VKH12345678` (8-digit precision)

## Database Schema

### Tables
- `sensor_reading`: TimescaleDB hypertable for sensor observations
- `report`: Normalized reports (auto-created from sensor data)
- `intel_doc`: Document metadata
- `doc_chunk`: Text chunks with embeddings and full-text search

### Key Features
- MGRS validation constraints
- Vector embeddings (3072 dimensions)
- Full-text search with PostgreSQL tsvector
- Trigram indexes for fuzzy MGRS matching
- Time-series partitioning with TimescaleDB

## Citation Format

Generated reports include inline citations:
- PDF documents: `[D:<doc_id> p<page> ¶<para>#<step_id?>]`
- Text documents: `[D:<doc_id> lines <line_start>–<line_end>]`
- Reports: `[R:<report_uuid>]`

## Security Notes

- Write endpoints require `X-API-Key` header
- MinIO bucket should be kept private
- No latitude/longitude stored - MGRS is authoritative
- Use TLS termination (nginx/caddy) for production

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (with .env file)
python -m DefHack
```

### Database Operations
```bash
# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Check migration status
docker-compose exec api alembic current
```

## Performance Optimization

After loading documents, create HNSW index for faster vector search:
```sql
CREATE INDEX idx_doc_chunk_emb_hnsw 
ON doc_chunk USING hnsw (embedding vector_cosine_ops);
```

## Troubleshooting

### Common Issues
1. **401 Unauthorized**: Check `X-API-Key` header matches `API_WRITE_KEY` in `.env`
2. **422 Validation Error**: Verify MGRS format and required fields
3. **Connection Refused**: Ensure all services are running with `docker-compose ps`
4. **MinIO Access**: Create the `intel` bucket via MinIO console

### Service Health
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs api
docker-compose logs db
docker-compose logs minio

# Database health check
docker-compose exec db pg_isready -U postgres
``` project


## Development with uv

This project uses [uv](https://github.com/astral-sh/uv) for Python package management and development workflow. uv is a fast Python package manager and build tool that replaces pip and virtualenv for most tasks.

### Getting Started

1. **Install uv** (if you don't have it):
	```pwsh
	pip install uv
	```

2. **Install dependencies:**
	```pwsh
	uv pip install -r requirements.txt
	```
	Or, if using `pyproject.toml`:
	```pwsh
	uv pip install -r pyproject.toml
	```

3. **Add a new dependency:**
	```pwsh
	uv pip install <package>
	```
	This will update your lockfile automatically.

4. **Update dependencies:**
	```pwsh
	uv pip update
	```

### Development Workflow

- Make all changes in a feature branch.
- Use `uv` to manage dependencies and environments.
- Run your code and tests using the uv-managed environment.
- Keep `pyproject.toml` and `uv.lock` up to date.
- Before pushing, ensure all dependencies are locked and documented.

For more details, see the [uv documentation](https://github.com/astral-sh/uv).



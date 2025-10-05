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

### Debugging ingestion payloads

When running the live ingestion loop (`uv run python -m DefHack.sensors.images.ingest`), pass
`--debug-payloads` to print each JSON payload before it is sent to the API.
Backlog retries respect the flag as well, making it easy to confirm the exact
request body when diagnosing 4xx responses.

## Configuring sensor backends

The sensor pipeline ships with lightweight heuristics by default so it works
out-of-the-box.  To enable stronger models such as TinyYOLO (detection) or
FastSeg (segmentation), edit `DefHack/sensors/settings.py` and change the
`detection_backend` and `segmentation_backend` values.  Remember to install the
corresponding dependencies before switching backends.

### YOLOv8 image pipeline

The image sensor module includes a YOLOv8 + CLIP retrieval pipeline that can be
invoked directly from the command line:

```pwsh
uv run python -m DefHack.sensors.images path/to/image_or_folder --readings-json output.json
```

The command accepts one or more image paths or directories, applies the YOLOv8
detector, and (optionally) generates captions for each detection. Passing
`--readings-json` writes the structured results to a JSON file. You can also use
`--caption-top-k`, `--weights`, `--confidence`, and related flags to customise
the inference run. Run `uv run python -m DefHack.sensors.images --help` to see
the full option list.

### Output schema

Pipeline outputs are serialised as `SensorObservationIn` objects (defined in
`DefHack/sensors/SensorSchema.py`). Each observation captures a *class-level*
summary for an image:

| Field | Description |
| --- | --- |
| `time` | UTC timestamp when the image was analysed |
| `mgrs` | MGRS string supplied to the pipeline (defaults to `UNKNOWN`) |
| `what` | Target label (e.g. `person`, `car`, `airplane`) |
| `amount` | Number of detections for that label in the image |
| `confidence` | Average confidence (0-100) across detections of that label |
| `sensor_id` | Identifier reported via `--sensor-id` (defaults to `YOLOv8-Pipeline`) |
| `unit` | Measurement unit (currently `count`) |
| `observer_signature` | Observer value provided via `--observer` |
| `original_message` | Reserved for future text payloads (currently `null`) |

Because detections are grouped per label, you'll see at most one
`SensorObservationIn` entry for each class in a single image.

### Configuring YOLOv8 defaults

The `BackendSettings` dataclass in `DefHack/sensors/settings.py` exposes
configuration hooks for the YOLOv8 pipeline:

- `yolov8_weights`: override the Ultralytics weights identifier or path.
- `yolov8_caption_model`: change the CLIP retrieval model used for captions.
- `yolov8_device`: force the computation device (`"cuda"`, `"cpu"`, etc.).

These attributes can also be specified in the existing `extra` dictionary for
backward compatibility. After editing the settings module, subsequent pipeline
runs will transparently pick up the new defaults.

### Acoustic drone detection pipeline

The acoustic sensor module analyses either recorded WAV files or synthetic
rotor simulations to detect blade-pass frequency (BPF) signatures. Importing
`DefHack.sensors.audio` automatically registers the `acoustic_drone_bpf`
algorithm with the shared `SensorSchema` factory.

- **Simulated capture** (generates an observation from physics-based rotor noise):

```pwsh
uv run python -m DefHack.sensors.audio --report
```

- **Analyse an existing recording**:

```pwsh
uv run python -m DefHack.sensors.audio path/to/recording.wav --place 35VLG8472571866 --report
```

Each run prints the derived `SensorObservationIn` payload and, when
`--report` is used, writes a human-readable text summary to
`DefHack/sensors/audio/data/processed/`. The pipeline is configurable via
`DefHack/sensors/audio/config.yaml`; override keys (sampling rate, FFT window,
harmonic count, etc.) or pass runtime flags such as `--rpm` and `--blades`
to tune the physics model for different rotorcraft.

Just like the image pipeline, the CLI forwards results as
`SensorObservationIn` records. By default they are written to
`DefHack/sensors/audio/predictions.json`; pass `--readings-json` to choose a
different destination or `--no-summary` to suppress console output when
running in batch mode. Forwarded readings carry the unit `"Alpha Company"`
and their `what` field is automatically prefixed with `"TACTICAL:"`, leading
with an FPV/NO-FPV prediction and the detector confidence (for example:
`TACTICAL: FPV DETECTED (confidence 92%) - …`). Use `--api-url`/`--api-key` to stream the
payload to the same ingest endpoint as the image pipeline (default:
`http://172.20.10.5:8080/ingest/sensor`). HTTP retries and the backlog file
(`--backlog-file`, defaults to `DefHack/sensors/audio/backlog.json`) reuse the
image pipeline’s delivery helpers; add `--debug-payloads` to inspect the JSON
or `--no-send` when you only need local artifacts.

#### Evaluating the UAV Propeller Anomaly dataset

Download the [UAV Propeller Anomaly Audio Dataset](https://github.com/tiiuae/UAV-Propeller-Anomaly-Audio-Dataset)
and extract it locally. Then run the evaluator to batch-process the WAV files:

```pwsh
uv run python -m DefHack.sensors.audio.evaluate_dataset C:/path/to/UAV-Propeller-Anomaly-Audio-Dataset --output reports/propeller_eval.csv
```

The command prints aggregate detection statistics per class and writes a CSV
with per-file fundamentals, harmonic counts, SNR, and textual descriptions. Use
`--format json` or `--max-files` to switch formats or sample subsets, and add
`--reports` to keep individual text summaries alongside the dataset. Inputs are
shuffled in a label-balanced order so capped runs still include every category;
set `--seed` for deterministic shuffling. A progress bar is displayed by
default; pass `--no-progress` when running in non-TTY environments.

To quickly review the results visually, run the helper script (requires
`matplotlib`):

```pwsh
uv run python tests/visualize_propeller_eval.py --show
```

This loads `reports/propeller_eval.csv`, generates a summary PNG at
`reports/propeller_eval_summary.png`, and plots detection rate and confidence
per class alongside a scatter of detected blade-pass frequencies.

#### Sweeping detector parameters with ESC-50 and MLSP

Use the parameter sweep utility to benchmark multiple acoustic tuning presets
against a positive (MLSP) and negative (ESC-50) dataset in one pass:

```pwsh
uv run python -m DefHack.sensors.audio.parameter_sweep --max-positive 500 --max-negative 500 --quiet
```

By default the script searches for `MLSP_2022_Real_Data/real_data` and
`ESC-50/audio` relative to the repository, iterating across a grid of
`prominence_ratio`, `min_bpf_hz`, `max_bpf_hz`, `num_harmonics`, and
`noise_floor_db` values. Results are written to `reports/parameter_sweep.csv`
and summarised in the console.

Add `--prominence-ratio`, `--min-bpf`, `--max-bpf`, `--harmonics`,
`--noise-floor`, or repeated `--override KEY=VALUE` flags to expand the grid or
force constant overrides. The evaluator reuses the balanced shuffling logic
from `evaluate_dataset`, so capped runs remain representative and reproducible
with `--seed`.


## Clarity Opsbot Telegram Bot

The `DefHack.clarity_opsbot` package contains a Telegram bot that can operate in unit group chats and private messages.

- **Group chats:** the bot listens for text and location posts, enriches them with MGRS coordinates, and queues the content for optional Gemini analysis.
- **Direct messages:** use `/frago` to launch a short dialogue that assembles a FRAGO order scaffold from the latest subordinate observations (dummy data for now). Finish with `/cancel` to abort.

To run the bot locally, provide the `TELEGRAM_BOT_TOKEN` (and optional Gemini credentials) and start the application:

```bash
export TELEGRAM_BOT_TOKEN=your_bot_token
python -m DefHack.clarity_opsbot
```



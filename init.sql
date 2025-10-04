CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- We'll start without TimescaleDB and pgvector for now
-- and focus on getting the basic system working
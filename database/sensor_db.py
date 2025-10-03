import psycopg2
import datetime
import psycopg2.extras



DSN = "dbname=sensor_db user=sensor_user password=strong_password host=localhost port=5432"

def create_schema():
    conn = psycopg2.connect(DSN)
    with conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id BIGSERIAL PRIMARY KEY,
                time TIMESTAMPTZ NOT NULL,
                mgrs TEXT NOT NULL,
                what TEXT NOT NULL,
                amount NUMERIC,
                confidence INTEGER NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
                sensor_id TEXT NOT NULL,
                unit TEXT,
                observer_signature TEXT NOT NULL CHECK (char_length(observer_signature) >= 3),
                embedding VECTOR(8)
            );
            """)
    conn.close()
    print("Schema created.")

def insert_observation(time, mgrs, what, amount, confidence, sensor_id, unit, observer_signature, embedding):
    conn = psycopg2.connect(DSN)
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO observations (time, mgrs, what, amount, confidence, sensor_id, unit, observer_signature, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (time, mgrs, what, amount, confidence, sensor_id, unit, observer_signature, embedding))
            obs_id = cur.fetchone()[0]
    conn.close()
    return obs_id

def print_all_observations():
    conn = psycopg2.connect(DSN)
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM observations;")
            rows = cur.fetchall()
            for row in rows:
                print(dict(row))
    conn.close()

if __name__ == "__main__":
    create_schema()
    obs_id = insert_observation(
        datetime.datetime.now(datetime.timezone.utc),
        "35VLG1234567890",
        "vehicle",
        2.0,
        95,
        "A1",
        "units",
        "Sensor 1, Team A",
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    )
    print_all_observations()
    print(f"Inserted observation with id: {obs_id}")
from sqlalchemy import text as sql

async def save_sensor(db, payload: dict):
    await db.execute(sql("""
      INSERT INTO sensor_reading(time, sensor_id, unit, observer_signature, mgrs, what, amount, confidence)
      VALUES (:time,:sensor_id,:unit,:observer_signature,:mgrs,:what,:amount,:confidence)
    """), payload)

    rid = (await db.execute(sql("""
      INSERT INTO report(source, unit, observer_signature, occurred_at, title, body, confidence, mgrs)
      VALUES ('sensor', :unit, :observer_signature, :time, :what, :what, :confidence, :mgrs)
      RETURNING id
    """), payload)).scalar()

    await db.commit()
    return {"report_id": str(rid)}
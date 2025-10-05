#!/usr/bin/env python3
"""
DefHack Data Input Methods - Consolidated Guide
All the ways to add sensor observations to DefHack
"""

print("""
🎯 DefHack Sensor Data Input - Consolidated Methods
==================================================

✅ REDUNDANT FILES REMOVED:
--------------------------
❌ add_new_observation.py (DELETED - was redundant)
❌ add_sensor_data.py (DELETED - was redundant)

These files were doing the same thing with different interfaces.

✅ CURRENT UNIFIED METHODS:
--------------------------

1. 🐍 PYTHON CLIENT (Recommended)
   File: defhack_unified_input.py
   
   from defhack_unified_input import DefHackClient
   
   client = DefHackClient()
   
   # Add single observation
   client.add_sensor_observation(
       time="2025-10-04T14:23:15+00:00",
       mgrs="35VLG8475672108", 
       what="T-72 Tank",
       amount=3,
       confidence=95,
       sensor_id="SENSOR_003",
       unit="Recon Team Alpha",
       observer_signature="SarahConnor"
   )

2. 🖥️ COMMAND LINE INTERFACE
   File: defhack_cli.py
   
   # Single observation
   python defhack_cli.py obs --time "2025-10-04T14:23:15+00:00" --mgrs "35VLG8475672108" --what "T-72 Tank" --amount 3 --confidence 95 --observer "SarahConnor"
   
   # Interactive mode
   python defhack_cli.py obs --interactive

3. 🌐 DIRECT API CALLS
   
   curl -X POST "http://localhost:8080/ingest/sensor" \\
        -H "X-API-Key: 583C55345736D7218355BCB51AA47" \\
        -H "Content-Type: application/json" \\
        -d '{
          "time": "2025-10-04T14:23:15+00:00",
          "mgrs": "35VLG8475672108",
          "what": "T-72 Tank", 
          "amount": 3,
          "confidence": 95,
          "sensor_id": "SENSOR_003",
          "unit": "Recon Team Alpha",
          "observer_signature": "SarahConnor"
        }'

4. 🤖 AUTOMATIC LLM INTEGRATION
   File: military_operations_integration.py
   
   from military_operations_integration import auto_process_observation
   
   # This automatically generates Telegram messages and FRAGOs
   results = await auto_process_observation()

📊 BULK DATA METHODS:
--------------------

1. 📋 BULK UPLOAD (Python Client)
   
   observations = [
       {"time": "...", "mgrs": "...", "what": "...", ...},
       {"time": "...", "mgrs": "...", "what": "...", ...}
   ]
   
   for obs in observations:
       client.add_sensor_observation(**obs)

2. 📁 CSV/JSON IMPORT (Create if needed)
   
   # You could create a CSV importer using the DefHackClient
   
🔍 DATA VERIFICATION:
--------------------

1. 🗄️ DATABASE INSPECTOR
   File: database_inspector.py
   
   python database_inspector.py

2. 🔎 SEARCH INTERFACE
   
   client.search("T-72 Tank")

📱 INTEGRATION READY:
--------------------

✅ Telegram Bot Integration: Use military_operations_integration.py
✅ LLM Processing: Automatic FRAGO and intelligence report generation  
✅ Document Citations: Intelligence documents support analysis
✅ Unified Interface: Single client for all operations

🎉 CLEAN AND CONSOLIDATED!
No more duplicate files - everything uses the unified system.
""")

if __name__ == "__main__":
    print("\n🚀 Use defhack_unified_input.py or defhack_cli.py for all sensor data operations!")
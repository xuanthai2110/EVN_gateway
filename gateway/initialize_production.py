import asyncio
import aiosqlite
import os

async def initialize_production():
    db_path = "e:/datalogger_renew_2026/gateway/storage/gateway.db"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    async with aiosqlite.connect(db_path) as db:
        # 1. Create Project (Mock for now, normally from server)
        await db.execute("""
            INSERT OR IGNORE INTO projects (id, name, capacity_kwp, ac_capacity_kw, inverter_count, server_id)
            VALUES (1, 'Huawei Real Plant', 400.0, 360.0, 8, 5)
        """)
        
        # 2. Clear old devices
        await db.execute("DELETE FROM devices")
        
        # 3. Add SmartLogger (Unit ID 0)
        await db.execute("""
            INSERT INTO devices (project_id, device_id, name, vendor, type)
            VALUES (1, '0', 'SmartLogger 3000', 'Huawei', 'LOGGER')
        """)
        
        # 4. Add Inverters (Unit IDs 1, 3, 4, 5, 6, 7, 8, 9)
        inverter_ids = [1, 3, 4, 5, 6, 7, 8, 9]
        for uid in inverter_ids:
            await db.execute("""
                INSERT INTO devices (project_id, device_id, name, vendor, type)
                VALUES (1, ?, ?, ?, ?)
            """, (str(uid), f"Inverter_{uid}", "Huawei", "INVERTER"))
            
        await db.commit()
    print(f"✅ Production database initialized at {db_path}")
    print(f"Devices added: SmartLogger (0) and Inverters {inverter_ids}")

if __name__ == "__main__":
    asyncio.run(initialize_production())

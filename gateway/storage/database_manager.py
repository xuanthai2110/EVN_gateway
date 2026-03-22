import aiosqlite
import asyncio
import os
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="e:/datalogger_renew_2026/gateway/storage/gateway.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    elec_meter_no TEXT,
                    elec_price_per_kwh REAL,
                    name TEXT,
                    location TEXT,
                    lat REAL,
                    lon REAL,
                    capacity_kwp REAL,
                    ac_capacity_kw REAL,
                    inverter_count INTEGER,
                    server_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    device_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    vendor TEXT,
                    type TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    EVN_connect INTEGER,
                    Logger_connect INTEGER,
                    p_out REAL,
                    q_out REAL,
                    p_inv_out REAL,
                    e_dayly REAL,
                    e_total REAL,
                    enable_set_p INTEGER,
                    set_p_pct REAL,
                    set_p_kw REAL,
                    enable_set_q INTEGER,
                    set_q_pct REAL,
                    set_q_kvar REAL,
                    ua REAL, ub REAL, uc REAL,
                    ia REAL, ib REAL, ic REAL,
                    frequency REAL,
                    pf REAL,
                    invs_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_project_time ON telemetry(project_id, timestamp DESC)")
            await db.commit()

    async def save_telemetry(self, data: dict):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO telemetry (
                    project_id, timestamp, EVN_connect, Logger_connect,
                    p_out, q_out, p_inv_out, e_dayly, e_total,
                    enable_set_p, set_p_pct, set_p_kw,
                    enable_set_q, set_q_pct, set_q_kvar,
                    ua, ub, uc, ia, ib, ic, frequency, pf, invs_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("project_id"), data.get("created_at"), 1 if data.get("EVN_connect") else 0, 1 if data.get("Logger_connect") else 0,
                data.get("P_out"), data.get("Q_out"), data.get("P_inv_out"), data.get("E_dayly"), data.get("E_total"),
                1 if data.get("Enable_Set_P") else 0, data.get("Set_P_pct"), data.get("Set_P_kW"),
                1 if data.get("Enable_Set_Q") else 0, data.get("Set_Q_pct"), data.get("Set_Q_kVAr"),
                data.get("U_a"), data.get("U_b"), data.get("U_c"),
                data.get("I_a"), data.get("I_b"), data.get("I_c"),
                data.get("F"), data.get("PF"), json.dumps(data.get("Invs_Data", []))
            ))
            await db.commit()

    async def get_devices(self, project_id=1):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM devices WHERE project_id = ?", (project_id,)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]

    async def get_unsent_telemetry(self, limit=100):
        # Placeholder for unsent logic if we add a 'sent' flag
        pass

import asyncio
from datetime import datetime

class CacheManager:
    def __init__(self):
        self._cache = {
            "EVN_connect": False,
            "Logger_connect": False,
            "P_out": 0.0,
            "Q_out": 0.0,
            "P_inv_out": 0.0,
            "E_yday": 0.0,
            "E_dayly": 0.0,
            "E_total": 0.0,
            "F": 0.0,
            "PF": 0.0,
            "I_a": 0.0,
            "I_b": 0.0,
            "I_c": 0.0,
            "U_a": 0.0,
            "U_b": 0.0,
            "U_c": 0.0,
            "Enable_Set_P": False,
            "Set_P_pct": 0.0,
            "Set_P_kW": 0.0,
            "Enable_Set_Q": False,
            "Set_Q_pct": 0.0,
            "Set_Q_kVAr": 0.0,
            "Invs_Data": [],
            "created_at": None,
            "status": "INIT"
        }
        self._lock = asyncio.Lock()
        self.stale_timeout = 5.0

    async def update(self, data: dict):
        async with self._lock:
            self._cache.update(data)
            self._cache["created_at"] = datetime.now().isoformat()
            self._cache["status"] = "OK"

    async def mark_error(self):
        async with self._lock:
            self._cache["status"] = "ERROR"

    async def get_all(self):
        async with self._lock:
            # Check for stale data
            if self._cache["created_at"]:
                dt = datetime.fromisoformat(self._cache["created_at"])
                if (datetime.now() - dt).total_seconds() > self.stale_timeout:
                    self._cache["status"] = "STALE"
            return self._cache.copy()

    async def get_value(self, key):
        async with self._lock:
            return self._cache.get(key)

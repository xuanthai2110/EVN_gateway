    from __future__ import annotations

from typing import Any, Dict, List

try:
    from .base import BaseDriver
except ImportError:
    from base import BaseDriver


RegisterDef = Dict[str, Any]


class HuaweiSmartLoggerDriver(BaseDriver):
    SMARTLOGGER_UNIT_ID = 0

    def __init__(self, transport, slave_id: int):
        self.transport = transport
        self.slave_id = slave_id
        self.smartlogger_id = self.SMARTLOGGER_UNIT_ID

    def register_map(self) -> Dict[str, Any]:
        return {
            "smartlogger": {
                "unit_id": self.smartlogger_id,
                "grid": [
                    {"name": "p_inv_total_kw", "address": 40525, "length": 2, "type": "sint32", "scale": 0.001, "access": "ro"},
                    {"name": "q_inv_total_kvar", "address": 40544, "length": 2, "type": "sint32", "scale": 0.001, "access": "ro"},
                    {"name": "v_a", "address": 40575, "length": 1, "type": "uint16", "scale": 0.1, "access": "ro"},
                    {"name": "v_b", "address": 40576, "length": 1, "type": "uint16", "scale": 0.1, "access": "ro"},
                    {"name": "v_c", "address": 40577, "length": 1, "type": "uint16", "scale": 0.1, "access": "ro"},
                    {"name": "i_a", "address": 40572, "length": 1, "type": "uint16", "scale": 1, "access": "ro"},
                    {"name": "i_b", "address": 40573, "length": 1, "type": "uint16", "scale": 1, "access": "ro"},
                    {"name": "i_c", "address": 40574, "length": 1, "type": "uint16", "scale": 1, "access": "ro"},
                    {"name": "pf", "address": 40532, "length": 1, "type": "sint16", "scale": 0.001, "access": "ro"},
                    {"name": "freq", "address": 37118, "length": 1, "type": "sint16", "scale": 0.01, "access": "ro"},
                ],
                "energy": [
                    {"name": "e_day_kwh", "address": 40562, "length": 2, "type": "uint32", "scale": 0.1, "access": "ro"},
                    {"name": "e_total_kwh", "address": 40560, "length": 2, "type": "uint32", "scale": 0.1, "access": "ro"},
                ],
                "control": [
                    {"name": "q_set_kvar", "address": 40422, "length": 2, "type": "sint32", "scale": 0.1, "access": "rw"},
                    {"name": "p_set_kw", "address": 40424, "length": 2, "type": "uint32", "scale": 0.1, "access": "rw"},
                    {"name": "p_set_percent", "address": 40428, "length": 1, "type": "uint16", "scale": 0.1, "access": "rw"},
                    {"name": "pf_set", "address": 40429, "length": 1, "type": "sint16", "scale": 0.001, "access": "rw"},
                ],
            },
            "inverter": {
                "unit_id": self.slave_id,
                "telemetry": [
                    {"name": "status", "address": 32009, "length": 1, "type": "uint16", "scale": 1, "access": "ro"},
                    {"name": "p_inv_out_kw", "address": 32080, "length": 2, "type": "sint32", "scale": 0.001, "access": "ro"},
                    {"name": "freq", "address": 32085, "length": 1, "type": "uint16", "scale": 0.01, "access": "ro"},
                    {"name": "q_inv_kvar", "address": 32106, "length": 2, "type": "sint32", "scale": 0.001, "access": "ro"},
                    {"name": "e_day_kwh", "address": 32114, "length": 2, "type": "uint32", "scale": 0.01, "access": "ro"},
                ],
            },
        }

    def register_map_inverter(self) -> Dict[str, Any]:
        return self.register_map()["inverter"]

    def _read_registers(self, address: int, count: int, unit_id: int) -> List[int]:
        response = self.transport.read_holding_registers(address=address, count=count, slave=unit_id)
        if response is None:
            raise IOError(f"No response for address={address}, count={count}, unit={unit_id}")
        if hasattr(response, "isError") and response.isError():
            raise IOError(f"Modbus exception for address={address}, count={count}, unit={unit_id}: {response!r}")
        return list(response.registers)

    def _decode_value(self, registers: List[int], value_type: str) -> int:
        normalized_type = value_type.lower()
        if normalized_type == "i32":
            normalized_type = "sint32"

        if normalized_type == "uint16":
            return registers[0] & 0xFFFF

        if normalized_type == "sint16":
            value = registers[0] & 0xFFFF
            return value - 0x10000 if value & 0x8000 else value

        if normalized_type == "uint32":
            return ((registers[0] & 0xFFFF) << 16) | (registers[1] & 0xFFFF)

        if normalized_type == "sint32":
            value = ((registers[0] & 0xFFFF) << 16) | (registers[1] & 0xFFFF)
            return value - 0x100000000 if value & 0x80000000 else value

        raise ValueError(f"Unsupported register type: {value_type}")

    def _apply_scale(self, value: int, scale: float) -> float | int:
        if scale in (None, 1):
            return value
        return value * scale

    def _read_definition(self, definition: RegisterDef, unit_id: int) -> Dict[str, Any]:
        registers = self._read_registers(definition["address"], definition["length"], unit_id)
        raw_value = self._decode_value(registers, definition["type"])
        value = self._apply_scale(raw_value, definition.get("scale", 1))
        return {
            "name": definition["name"],
            "address": definition["address"],
            "unit_id": unit_id,
            "registers": registers,
            "raw": raw_value,
            "value": value,
            "access": definition.get("access", "ro"),
            "type": definition["type"],
            "scale": definition.get("scale", 1),
        }

    def parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        parsed: Dict[str, Any] = {}
        for key, value in raw_data.items():
            if isinstance(value, dict) and "value" in value:
                parsed[key] = value["value"]
            elif isinstance(value, dict):
                parsed[key] = self.parse(value)
            else:
                parsed[key] = value
        return parsed

    def _read_group(self, definitions: List[RegisterDef], unit_id: int) -> Dict[str, Any]:
        raw_group: Dict[str, Any] = {}
        for definition in definitions:
            raw_group[definition["name"]] = self._read_definition(definition, unit_id)
        return raw_group

    def read_smartlogger(self) -> Dict[str, Any]:
        config = self.register_map()["smartlogger"]
        unit_id = config["unit_id"]
        raw = {
            "grid": self._read_group(config["grid"], unit_id),
            "energy": self._read_group(config["energy"], unit_id),
            "control": self._read_group(config["control"], unit_id),
        }
        return {
            "unit_id": unit_id,
            "raw": raw,
            "parsed": self.parse(raw),
        }

    def read_inverter(self) -> Dict[str, Any]:
        config = self.register_map_inverter()
        unit_id = config["unit_id"]
        raw = {
            "telemetry": self._read_group(config["telemetry"], unit_id),
        }
        return {
            "unit_id": unit_id,
            "raw": raw,
            "parsed": self.parse(raw),
        }

    def _encode_value(self, value: float, definition: RegisterDef) -> List[int]:
        scale = definition.get("scale", 1) or 1
        raw_value = int(round(value / scale))
        value_type = definition["type"].lower()

        if value_type == "i32":
            value_type = "sint32"

        if value_type == "uint16":
            return [raw_value & 0xFFFF]

        if value_type == "sint16":
            return [raw_value & 0xFFFF]

        if value_type in {"uint32", "sint32"}:
            raw_value &= 0xFFFFFFFF
            return [(raw_value >> 16) & 0xFFFF, raw_value & 0xFFFF]

        raise ValueError(f"Unsupported register type for write: {definition['type']}")

    def _write_definition_value(self, definition: RegisterDef, value: float) -> bool:
        registers = self._encode_value(value, definition)
        if len(registers) == 1:
            response = self.transport.write_register(address=definition["address"], value=registers[0], slave=self.smartlogger_id)
        else:
            response = self.transport.write_registers(address=definition["address"], values=registers, slave=self.smartlogger_id)
        return not (hasattr(response, "isError") and response.isError())

    def _control_definition(self, name: str) -> RegisterDef:
        controls = self.register_map()["smartlogger"]["control"]
        for definition in controls:
            if definition["name"] == name:
                return definition
        raise KeyError(f"Control register not found: {name}")

    def enable_power_limit(self, enable: bool) -> bool:
        # Current register map does not expose a dedicated enable coil/register.
        # Keep the method concrete for the driver interface and signal unsupported control.
        return False

    def write_power_limit_kw(self, kw: float) -> bool:
        definition = self._control_definition("p_set_kw")
        return self._write_definition_value(definition, kw)

    def write_power_limit_percent(self, percent: float) -> bool:
        definition = self._control_definition("p_set_percent")
        return self._write_definition_value(definition, percent)

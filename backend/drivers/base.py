# drivers/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseDriver(ABC):
    # =========================================================
    # ===================== INIT ===============================
    # =========================================================

    @abstractmethod
    def __init__(self, transport, slave_id: int): #Khởi tạo driver với transport (Modbus RTU/TCP) và slave ID của inverter.
        pass

    #============khai báo registor của inverter================================

    @abstractmethod
    def register_map(self) -> Dict[str, Any]: #Trả về một dict chứa thông tin về các register của inverter, bao gồm địa chỉ, kiểu dữ liệu, v.v.
        pass
    def register_map_inverter(self) -> Dict[str, Any]: #Trả về một dict chứa thông tin về các register của inverter, bao gồm địa chỉ, kiểu dữ liệu, v.v.
        pass   
    #================ hàm parse dữ liệu từ raw register sang engineering value =========================
    @abstractmethod
    def parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    # =============Các hàm đọc dữ liệu từ inverter =========================

    @abstractmethod
    def read_smartlogger(self) -> Dict[str, Any]: #Đọc tất cả dữ liệu (AC, DC, info, string) trong một lần gọi.
        pass
    @abstractmethod
    def read_inverter(self) -> Dict[str, Any]: #Đọc tất cả dữ liệu (AC, DC, info, string) trong một lần gọi.
        pass
        
    #================ Điều khiển inverter =========================

    @abstractmethod
    def enable_power_limit(self, enable: bool) -> bool: #Bật / tắt chế độ power limit.
        pass

    @abstractmethod
    def write_power_limit_kw(self, kw: float) -> bool: #Ghi giá trị giới hạn công suất (kW).
        pass

    def write_power_limit_percent(self, percent: float) -> bool: #Ghi giá trị giới hạn công suất (%).
        pass
    
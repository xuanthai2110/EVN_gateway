from pymodbus.client import ModbusTcpClient

SMARTLOGGER_IP = "192.168.1.8"
PORT = 502
UNIT_ID = 0   # SmartLogger tổng site

client = ModbusTcpClient(SMARTLOGGER_IP, port=PORT)
client.connect()

# Ví dụ: đặt công suất tác dụng 50 kW
set_kw = int(200 / 0.1)   # scale 0.1 → raw value
client.write_registers(40424, [set_kw >> 16, set_kw & 0xFFFF], slave=UNIT_ID)

# Ví dụ: đặt công suất theo % = 80%
#set_pct = int(80 / 0.1)  # scale 0.1 → raw value
#client.write_register(40428, set_pct, slave=UNIT_ID)

client.close()

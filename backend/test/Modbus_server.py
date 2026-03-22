import asyncio
from pymodbus.server.async_io import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification

# Giả lập driver đọc dữ liệu từ inverter/SmartLogger
def read_driver_data():
    return {
        "P_out": 5200,       # W
        "Q_out": 1100,       # var
        "E_yday": 32500,     # Wh
        "F": 50.01,          # Hz
        "PF": 0.95,
        "Ua": 230.1,
        "Ub": 229.8,
        "Uc": 230.5,
        "Ia": 12.3,
        "Ib": 12.1,
        "Ic": 12.4
    }

# Khởi tạo datastore
store = ModbusSlaveContext(
    di = {},   # Discrete Inputs
    co = {},   # Coils (Enable P/Q)
    hr = {},   # Holding Registers (SetPoint P/Q)
    ir = {}    # Input Registers (Telemetry)
)
context = ModbusServerContext(slaves=store, single=True)

# Cập nhật dữ liệu telemetry vào Input Registers
def update_context():
    data = read_driver_data()
    # Input Registers (function code 4)
    context[0].setValues(3, 1, [int(data["P_out"]/1000)])   # kW
    context[0].setValues(3, 7, [int(data["Q_out"]/1000)])   # kvar
    context[0].setValues(3, 5, [int(data["E_yday"]/100)])  # kWh
    context[0].setValues(3, 21, [int(data["F"]/0.01)])     # Hz
    context[0].setValues(3, 23, [int(data["PF"]/0.001)])   # PF
    context[0].setValues(3, 9, [int(data["Ua"]/0.1)])      # V
    context[0].setValues(3, 11, [int(data["Ub"]/0.1)])
    context[0].setValues(3, 13, [int(data["Uc"]/0.1)])
    context[0].setValues(3, 15, [int(data["Ia"]/1)])
    context[0].setValues(3, 17, [int(data["Ib"]/1)])
    context[0].setValues(3, 19, [int(data["Ic"]/1)])

# Task định kỳ cập nhật dữ liệu
async def updating_task():
    while True:
        update_context()
        await asyncio.sleep(5)

# Thông tin thiết bị
identity = ModbusDeviceIdentification()
identity.VendorName = 'EVN Gateway'
identity.ProductCode = 'EG01'
identity.ProductName = 'EVN Modbus Server'
identity.ModelName = 'EVN Gateway Model'
identity.MajorMinorRevision = '1.0'

# Hàm xử lý ghi lệnh điều khiển
def handle_control():
    # Đọc coil và holding register từ context
    enable_p = context[0].getValues(1, 11, 1)[0]  # Coil 11
    set_p_pct = context[0].getValues(3, 13, 1)[0] # Holding 13
    set_p_kw = context[0].getValues(3, 15, 2)     # Holding 15-16

    enable_q = context[0].getValues(1, 12, 1)[0]  # Coil 12
    set_q_pct = context[0].getValues(3, 17, 1)[0] # Holding 17
    set_q_kvar = context[0].getValues(3, 19, 2)   # Holding 19-20

    # TODO: gọi driver để gửi lệnh xuống inverter
    print("Điều khiển P:", enable_p, set_p_pct, set_p_kw)
    print("Điều khiển Q:", enable_q, set_q_pct, set_q_kvar)

async def control_task():
    while True:
        handle_control()
        await asyncio.sleep(2)

async def run_server():
    asyncio.create_task(updating_task())
    asyncio.create_task(control_task())
    await StartTcpServer(context, identity=identity, address=("0.0.0.0", 502))

if __name__ == "__main__":
    asyncio.run(run_server())

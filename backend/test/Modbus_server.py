import asyncio
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification

# ================= DRIVER GIẢ LẬP =================
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

# ================= DATASTORE =================
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0]*100),
    co=ModbusSequentialDataBlock(0, [0]*100),
    hr=ModbusSequentialDataBlock(0, [0]*100),
    ir=ModbusSequentialDataBlock(0, [0]*100),
)

context = ModbusServerContext(slaves=store, single=True)

# ================= UPDATE TELEMETRY =================
def update_context():
    data = read_driver_data()

    # Input Registers (FC = 4)
    context[0].setValues(4, 1, [int(data["P_out"] / 1000)])   # kW
    context[0].setValues(4, 7, [int(data["Q_out"] / 1000)])   # kvar
    context[0].setValues(4, 5, [int(data["E_yday"] / 100)])   # kWh
    context[0].setValues(4, 21, [int(data["F"] / 0.01)])      # Hz
    context[0].setValues(4, 23, [int(data["PF"] / 0.001)])    # PF

    context[0].setValues(4, 9, [int(data["Ua"] / 0.1)])       # V
    context[0].setValues(4, 11, [int(data["Ub"] / 0.1)])
    context[0].setValues(4, 13, [int(data["Uc"] / 0.1)])

    context[0].setValues(4, 15, [int(data["Ia"])])
    context[0].setValues(4, 17, [int(data["Ib"])])
    context[0].setValues(4, 19, [int(data["Ic"])])

# ================= TASK UPDATE =================
async def updating_task():
    while True:
        update_context()
        await asyncio.sleep(5)

# ================= CONTROL =================
def handle_control():
    # Coil (FC = 1)
    enable_p = context[0].getValues(1, 11, count=1)[0]
    enable_q = context[0].getValues(1, 12, count=1)[0]

    # Holding Register (FC = 3)
    set_p_pct = context[0].getValues(3, 13, count=1)[0]
    set_p_kw = context[0].getValues(3, 15, count=2)

    set_q_pct = context[0].getValues(3, 17, count=1)[0]
    set_q_kvar = context[0].getValues(3, 19, count=2)

    print("Điều khiển P:", enable_p, set_p_pct, set_p_kw)
    print("Điều khiển Q:", enable_q, set_q_pct, set_q_kvar)

async def control_task():
    while True:
        handle_control()
        await asyncio.sleep(2)

# ================= DEVICE INFO =================
identity = ModbusDeviceIdentification()
identity.VendorName = 'EVN Gateway'
identity.ProductCode = 'EG01'
identity.ProductName = 'EVN Modbus Server'
identity.ModelName = 'EVN Gateway Model'
identity.MajorMinorRevision = '1.0'

# ================= MAIN =================
async def run_server():
    asyncio.create_task(updating_task())
    asyncio.create_task(control_task())

    await StartAsyncTcpServer(
        context=context,
        identity=identity,
        address=("0.0.0.0", 502)
    )

if __name__ == "__main__":
    asyncio.run(run_server())
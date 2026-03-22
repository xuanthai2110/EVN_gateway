import asyncio
from pymodbus.server.async_io import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification

def read_driver_data():
    return {
        "P_out": 5200,
        "Q_out": 1100,
        "E_yday": 32500,
        "F": 50.01,
        "PF": 0.95,
        "Ua": 230.1,
        "Ub": 229.8,
        "Uc": 230.5,
        "Ia": 12.3,
        "Ib": 12.1,
        "Ic": 12.4
    }

store = ModbusSlaveContext(
    di = ModbusSequentialDataBlock(0, [0]*100),
    co = ModbusSequentialDataBlock(0, [0]*100),
    hr = ModbusSequentialDataBlock(0, [0]*100),
    ir = ModbusSequentialDataBlock(0, [0]*100)
)
context = ModbusServerContext(slaves=store, single=True)

def update_context():
    data = read_driver_data()
    context[0].setValues(3, 1, [int(data["P_out"]/1000)])
    context[0].setValues(3, 7, [int(data["Q_out"]/1000)])
    context[0].setValues(3, 5, [int(data["E_yday"]/100)])
    context[0].setValues(3, 21, [int(data["F"]/0.01)])
    context[0].setValues(3, 23, [int(data["PF"]/0.001)])
    context[0].setValues(3, 9, [int(data["Ua"]/0.1)])
    context[0].setValues(3, 11, [int(data["Ub"]/0.1)])
    context[0].setValues(3, 13, [int(data["Uc"]/0.1)])
    context[0].setValues(3, 15, [int(data["Ia"])])
    context[0].setValues(3, 17, [int(data["Ib"])])
    context[0].setValues(3, 19, [int(data["Ic"])])

async def updating_task():
    while True:
        update_context()
        await asyncio.sleep(5)

def handle_control():
    enable_p = context[0].getValues(1, 11, 1)[0]
    set_p_pct = context[0].getValues(3, 13, 1)[0]
    set_p_kw = context[0].getValues(3, 15, 2)
    enable_q = context[0].getValues(1, 12, 1)[0]
    set_q_pct = context[0].getValues(3, 17, 1)[0]
    set_q_kvar = context[0].getValues(3, 19, 2)
    print("Điều khiển P:", enable_p, set_p_pct, set_p_kw)
    print("Điều khiển Q:", enable_q, set_q_pct, set_q_kvar)

async def control_task():
    while True:
        handle_control()
        await asyncio.sleep(2)

identity = ModbusDeviceIdentification()
identity.VendorName = 'EVN Gateway'
identity.ProductCode = 'EG01'
identity.ProductName = 'EVN Modbus Server'
identity.ModelName = 'EVN Gateway Model'
identity.MajorMinorRevision = '1.0'

async def run_server():
    asyncio.create_task(updating_task())
    asyncio.create_task(control_task())
    await StartTcpServer(context=context, identity=identity, address=("0.0.0.0", 502))

if __name__ == "__main__":
    asyncio.run(run_server())

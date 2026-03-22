
import sys,time
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
from drivers.huawei_smartlogger import SmartLogger,Inverter,HuaweiModbusDriver
def main():
    huawei = HuaweiModbusDriver(host="192.168.1.8")
    smart = SmartLogger(driver=huawei, unit_id=0)
    inverter = Inverter(driver=huawei, unit_ids=[1,3,4,5,6,7,8,9])

    while True:
        smart_data = smart.read()
        print("Smart Logger Data:", smart_data)

        inverter_data = inverter.read()
        print("Inverter Data:", inverter_data)
        time.sleep(5)


if __name__ == "__main__":
    main()
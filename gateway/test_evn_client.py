import asyncio
import struct
import logging
from pymodbus.client import AsyncModbusTcpClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [EVN] - %(levelname)s - %(message)s')

def decode_f32(registers):
    """Decodes two 16-bit registers to float32 (Big Endian)."""
    packed = struct.pack('>HH', *registers)
    return struct.unpack('>f', packed)[0]

def encode_f32(value):
    """Encodes float32 to two 16-bit registers (Big Endian)."""
    packed = struct.pack('>f', value)
    return struct.unpack('>HH', packed)

async def evn_simulation():
    logging.info("Connecting to Solar Gateway at localhost:5020...")
    
    # Use port 5020 for local testing to avoid permission issues
    client = AsyncModbusTcpClient("192.168.1.8", port=5020)
    
    if not await client.connect():
        logging.error("Failed to connect to Gateway (Port 502). Make sure main.py is running as Admin or port is available.")
        return

    try:
        # 1. READ MONITORING DATA (FC04)
        logging.info("--- READING MONITORING DATA (FC04) ---")
        
        # Read P_out (30001)
        rr = await client.read_input_registers(0, count=2, device_id=1)
        if rr.isError():
            logging.error(f"Error reading P_out (Address 0): {rr}")
        else:
            p_out = decode_f32(rr.registers)
            logging.info(f"✅ [Address 30001] P_out: {p_out:.2f} kW")
        
        # Read P_inv_total (30003)
        rr = await client.read_input_registers(2, count=2, device_id=1)
        if rr.isError():
            logging.error(f"Error reading P_inv_total (Address 2): {rr}")
        else:
            p_inv = decode_f32(rr.registers)
            logging.info(f"✅ [Address 30003] P_inv_total: {p_inv:.2f} kW")

        # Read E_dayly (30005)
        rr = await client.read_input_registers(4, count=2, device_id=1)
        if rr.isError():
            logging.error(f"Error reading E_dayly (Address 4): {rr}")
        else:
            e_day = decode_f32(rr.registers)
            logging.info(f"✅ [Address 30005] E_dayly: {e_day:.2f} kWh")

        # 2. WRITE CONTROL COMMAND (FC16)
        logging.info("--- SENDING CONTROL COMMAND (FC16) ---")
        target_pct = 75.0
        registers = encode_f32(target_pct)
        
        logging.info(f"Setting Power Limit to {target_pct}% at address 40013...")
        wr = await client.write_registers(12, registers, device_id=1)
        if wr.isError():
            logging.error(f"❌ Control command failed: {wr}")
        else:
            logging.info("✅ Control command accepted by Gateway.")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        client.close()
        logging.info("EVN session closed.")

if __name__ == "__main__":
    asyncio.run(evn_simulation())

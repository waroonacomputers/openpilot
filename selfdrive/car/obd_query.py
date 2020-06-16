#!/usr/bin/env python3
import traceback
import panda.python.uds as uds
import cereal.messaging as messaging
from selfdrive.car.isotp_parallel_query import IsoTpParallelQuery
from selfdrive.swaglog import cloudlog

TESTER_PRESENT_REQUEST = bytes([uds.SERVICE_TYPE.TESTER_PRESENT, 0x0])
TESTER_PRESENT_RESPONSE = bytes([uds.SERVICE_TYPE.TESTER_PRESENT + 0x40, 0x0])
HYUNDAI_VERSION_REQUEST_SHORT = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER]) + \
  p16(0xf1a0)
HYUNDAI_VERSION_RESPONSE = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER + 0x40])
TX_ADDR = 0x7d0
TX_ADDR = 0x7
OBD_DIAG_REQUEST = b'\x07\x7d'
OBD_DIAG_RESPONSE = b'\x41\x1C'

def get_car_country(logcan, sendcan, bus, timeout=0.1, retry=5, debug=False):
  print(f"OBD2 query {hex(TX_ADDR)} ...")
  for i in range(retry):
    try:
      query = IsoTpParallelQuery(sendcan, logcan, bus, [TX_ADDR], [OBD_DIAG_REQUEST], [OBD_DIAG_RESPONSE], debug=debug)
      for addr, dat in query.get_data(timeout).items():
        print("query response")
        print(f"{hex(addr)} {bytes.hex(dat)}")
        return bytes.hex(dat)
      print(f"query retry ({i+1}) ...")
    except Exception:
      cloudlog.warning(f"OBD2 query exception: {traceback.format_exc()}")

  return False


if __name__ == "__main__":
  import time
  sendcan = messaging.pub_sock('sendcan')
  logcan = messaging.sub_sock('can')
  time.sleep(1)
  ret = get_car_country(logcan, sendcan, 1, debug=False)
  print(f"result: {ret}")

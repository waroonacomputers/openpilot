#!/usr/bin/env python3
import os
import time
from cereal import car
from opendbc.can.parser import CANParser
from selfdrive.car.interfaces import RadarInterfaceBase
from selfdrive.car.hyundai.values import DBC, FEATURES

def get_radar_can_parser(CP, bus):
  signals = [
    # sig_name, sig_address, default
    ("ACC_ObjStatus", "SCC11", 0),
    ("ACC_ObjLatPos", "SCC11", 0),
    ("ACC_ObjDist", "SCC11", 0),
    ("ACC_ObjRelSpd", "SCC11", 0),
  ]
  checks = []
  return CANParser(DBC[CP.carFingerprint]['pt'], signals, checks, bus)


class RadarInterface(RadarInterfaceBase):
  def __init__(self, CP):
    # radar
    self.pts = {}
    self.delay = 0  # Delay of radar
    self.rcp = get_radar_can_parser(CP, 0)
    self.rcp1 = get_radar_can_parser(CP, 1)
    self.rcp2 = get_radar_can_parser(CP, 2)
    self.updated_messages = set()
    self.trigger_msg = 0x420
    self.track_id = 0
    self.no_radar = CP.carFingerprint in FEATURES["non_scc"]

  def update(self, can_strings):
    if self.no_radar:
      if 'NO_RADAR_SLEEP' not in os.environ:
        time.sleep(0.05)  # radard runs on RI updates

      return car.RadarData.new_message()

    if not self.track_id:
      for i in range(3):
        vls = self.rcp1.update_strings(can_strings) if i == 1 else self.rcp2.update_strings(can_strings) if i = 2 \
        else self.rcp.update_strings(can_strings)
        self.updated_messages.update(vls)
        if self.rcp.vl["SCC11"]['TauGapSet'] and i == 0 or self.rcp1.vl["SCC11"]['TauGapSet'] and i == 1 \
                                                                     or self.rcp2.vl["SCC11"]['TauGapSet'] and i == 2 :
          break
    else:
      self.updated_messages.update(vls)

    if self.trigger_msg not in self.updated_messages:
      return None

    rr =  self._update(self.updated_messages)
    self.updated_messages.clear()

    return rr


  def _update(self, updated_messages):
    ret = car.RadarData.new_message()
    cpt = self.rcp.vl
    errors = []
    if not self.rcp.can_valid:
      errors.append("canError")
    ret.errors = errors

    valid = cpt["SCC11"]['ACC_ObjStatus']
    if valid:
      for ii in range(2):
        if ii not in self.pts:
          self.pts[ii] = car.RadarData.RadarPoint.new_message()
          self.pts[ii].trackId = self.track_id
          self.track_id += 1
        self.pts[ii].dRel = cpt["SCC11"]['ACC_ObjDist']  # from front of car
        self.pts[ii].yRel = -cpt["SCC11"]['ACC_ObjLatPos']  # in car frame's y axis, left is negative
        self.pts[ii].vRel = cpt["SCC11"]['ACC_ObjRelSpd']
        self.pts[ii].aRel = float('nan')
        self.pts[ii].yvRel = float('nan')
        self.pts[ii].measured = True

    ret.points = list(self.pts.values())
    return ret

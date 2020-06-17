#!/usr/bin/env python3
import os
import time
from cereal import car
from opendbc.can.parser import CANParser
from selfdrive.car.interfaces import RadarInterfaceBase
from selfdrive.car.hyundai.values import DBC


def get_radar_can_parser(CP):
  signals = [
    # sig_name, sig_address, default
    # ("ACC_ObjStatus", "SCC11", 0),
    # ("ACC_ObjLatPos", "SCC11", 0),
    # ("ACC_ObjDist", "SCC11", 0),
    # ("ACC_ObjRelSpd", "SCC11", 0),

    ("Target_Info","738LCAN",0),

    ("Vision_ObjLatPos","V_OptData_73b",0),
    ("Vision_ObjDist_2_High","V_OptData_739",0),
    ("Vision_ObjDist_High","V_OptData_739",0),
    ("Vision_ObjDist_Low","V_OptData_739",0),
    ("Vision_ObjRelSpd","V_OptData_739",0),
  ]
  checks = [
    # address, frequency
    #("SCC11", 50),
    # ("V_OptData_739", 25),
  ]
  return CANParser(DBC[CP.carFingerprint]['pt'], signals, checks, 0)


class RadarInterface(RadarInterfaceBase):
  def __init__(self, CP):
    super().__init__(CP)
    self.rcp = get_radar_can_parser(CP)
    self.updated_messages = set()
    self.trigger_msg = 0x420
    self.track_id = 0
    self.radar_off_can = CP.radarOffCan

  def update(self, can_strings):
    if self.radar_off_can:
      if 'NO_RADAR_SLEEP' not in os.environ:
        time.sleep(0.05)  # radard runs on RI updates

      return car.RadarData.new_message()

    vls = self.rcp.update_strings(can_strings)
    self.updated_messages.update(vls)

    if self.trigger_msg not in self.updated_messages:
      return None

    rr = self._update(self.updated_messages)
    self.updated_messages.clear()

    return rr

  def _update(self, updated_messages):
    ret = car.RadarData.new_message()
    cpt = self.rcp.vl
    errors = []
    if not self.rcp.can_valid:
      errors.append("canError")
    ret.errors = errors

    valid = cpt["738LCAN"]["Target_Info"] > 1
    if valid:
      for ii in range(2):
        if ii not in self.pts:
          self.pts[ii] = car.RadarData.RadarPoint.new_message()
          self.pts[ii].trackId = self.track_id
          self.track_id += 1
        self.pts[ii].dRel = cpt["V_OptData_739"]['Vision_ObjDist_High']  # from front of car
        self.pts[ii].yRel = -cpt["V_OptData_73b"]['Vision_ObjLatPos']  # in car frame's y axis, left is negative
        self.pts[ii].vRel =  cpt["V_OptData_739"]['Vision_ObjRelSpd']
        self.pts[ii].aRel = float('nan')
        self.pts[ii].yvRel = float('nan')
        self.pts[ii].measured = True

    ret.points = list(self.pts.values())
    return ret

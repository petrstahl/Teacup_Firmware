import os

from configtool.data import reSensorData
from createTemperatureLookup import Thermistor

class ThermistorTableFile:
  def __init__(self, folder):
    self.error = False
    fn = os.path.join(folder, "ThermistorTable.h")
    try:
      self.fp = open(fn, "wb")
    except:
      self.error = True

  def close(self):
    self.fp.close()

  def output(self, text):
    self.fp.write(text + "\n")

def generateTempTables(tl, settings):
  ofp = ThermistorTableFile(settings.folder)
  if ofp.error:
    return False
 
  mult = 4
  minadc = int(settings.minAdc)
  N = int(settings.numTemps)

  ofp.output("#define NUMTABLES %d" % len(tl.keys()))
  tnbr = 0
  for tnm in tl.keys():
    ofp.output("#define THERMISTOR_%s %d" % (tnm, tnbr))
    tnbr += 1
  ofp.output("#define NUMTEMPS %d" % N)

  if len(tl.keys()) == 0 or N == 0:
    ofp.close();
    return True

  ofp.output("const uint16_t PROGMEM temptable[NUMTABLES][NUMTEMPS][2] = {")

  tcount = 0
  for tn in tl.keys():
    tcount += 1
    m = reSensorData.match(tl[tn])
    if m is None:
      continue
    t = m.groups()
    if len(t) != 4:
      continue
    r0 = t[0]
    beta = t[1]
    r2 = t[2]
    vadc = t[3]
    ofp.output("// %s temp table parameters: R0: %s  T0: %s  R1: %s  R2: %s  beta: %s  maxadc: %s" %
                  (tn, r0, settings.t0, settings.r1, r2, beta, settings.maxAdc))
    ofp.output(" {")
    thm = Thermistor(int(r0),
                     int(settings.t0),
                     int(beta),
                     int(settings.r1),
                     int(r2),
                     float(vadc),
                     float(vadc))
    maxadc = int(settings.maxAdc)
    zadc = int(thm.setting(0))
    if zadc < maxadc:
      maxadc = zadc
    
    increment = float(maxadc - minadc)/float(N-1);
    ct = 1.0
    adcs = []
    for i in range(N):
      adcs.append(int(ct))
      ct += increment

    counter = 0
    for adc in adcs:
      counter = counter +1
      degC=thm.temp(adc)
      resistance=thm.resistance(thm.temp(adc))
      vTherm= adc*thm.vadc/1024
      ptherm= vTherm*vTherm/resistance
      resolution = ( thm.temp(adc-1)-thm.temp(adc) if adc>1 else thm.temp(adc) -thm.temp(adc+1))
      sep = (',' if counter != len(adcs) else ' ')
      ostr = "   {%4s, %6s}%s // %7.2f C,  %7.0f Ohm, %0.3f V, %0.2f C/count, %0.2fmW" % (adc, int(thm.temp(adc)*mult), sep,degC, resistance,vTherm,resolution,ptherm*1000)
      ofp.output(ostr)
    if tcount == len(tl.keys()):
      ofp.output(" }")
    else:
      ofp.output(" },")
  ofp.output("};")
  ofp.close()
  return True

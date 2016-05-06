#!/usr/bin/env python
from __future__ import division
import spidev
import time
import RPi.GPIO as GPIO

spi = spidev.SpiDev(0, 0)
#spi.max_speed_hz = 500000 # 1.2 MHz
spi.max_speed_hz = 1200000 # 1.2 MHz

def read_spi():
    spidata = spi.xfer2([96,0])
    #print("Raw ADC:      {}".format(spidata))
    data = ((spidata[0] & 3) << 8) + spidata[1]
    return data

class Scale:
    v_prev = 0
    v_curr = 0
    v_last_reading = 0
    tick_count = 0
    READING_THRESHOLD = .1

    def get_v_diff(self):
        return abs(self.v_prev - self.v_curr)

    def tick(self):
        self.tick_count += 1
        v = read_spi()
        self.v_curr = v
        if abs(self.v_last_reading -v) > self.READING_THRESHOLD:
            self.v_last_reading = v
            return (v, True)
        return (v, False)

    def tick_done(self):
        self.v_prev = self.v_curr

scale = Scale()
if __name__ == '__main__':
    while True:
        (v, new_reading) = scale.tick()
        if v == 0:
            continue

        #if new_reading:
        #    print scale.v_curr

        equals = '='*int(v)
        if scale.tick_count % 100 == 0:
            print("%s, %s" % (v, equals))
        

        scale.tick_done()


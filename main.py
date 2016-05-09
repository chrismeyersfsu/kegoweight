#!/usr/bin/env python
from __future__ import division
import spidev
import time
import requests
import sys
import RPi.GPIO as GPIO
from datetime import datetime
from datetime import timedelta
from collections import deque
from requests.exceptions import ConnectionError
from requests.auth import HTTPBasicAuth
import json
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('kegometer.cfg')

username = config.get('tower', 'username', None)
password = config.get('tower', 'password', None)
job_template_id = config.get('tower', 'job_template_id', None)
if not username or not password or not job_template_id:
    print("Tower username and password not found")
    sys.exit(0)

spi = spidev.SpiDev(0, 0)
#spi.max_speed_hz = 500000 # 1.2 MHz
spi.max_speed_hz = 1200000 # 1.2 MHz

def read_spi():
    spidata = spi.xfer2([96,0])
    #print("Raw ADC:      {}".format(spidata))
    data = ((spidata[0] & 3) << 8) + spidata[1]
    return data

class Scale:
    v_history = None
    v_average = 0
    v_prev = 0
    v_curr = 0
    v_last_reading = 0
    tick_count = 0
    READING_THRESHOLD = .1

    def __init__(self):
        self.v_history = deque(maxlen=20000)

    def get_v_diff(self):
        return abs(self.v_prev - self.v_curr)

    def tick(self):
        self.tick_count += 1
        v = read_spi()
        self.v_curr = v
        if abs(self.v_last_reading -v) > self.READING_THRESHOLD:
            self.v_last_reading = v
            self.v_history.append(v)
            return (v, True)
        return (v, False)

    def tick_done(self):
        self.v_prev = self.v_curr

    def calc_average(self):
        return (float(sum(self.v_history)) / len(self.v_history))

scale = Scale()
if __name__ == '__main__':
    next_time = datetime.now()
    while True:
        (v, new_reading) = scale.tick()
        if v == 0:
            continue

        #if new_reading:
        #    print scale.v_curr

        equals = '='*int(v)
        if scale.tick_count % 100 == 0:
            print("%s, %s" % (v, equals))

        
        if datetime.now() >= next_time:
            payload = {
                'extra_vars': {
                    'beer_weight': v
                }
            }
            try:
                headers = {'content-type': 'application/json'}
                r = requests.post('https://tower.testing.ansible.com/api/v1/job_templates/%s/launch/' % job_template_id, data=json.dumps(payload), auth=HTTPBasicAuth(username, password), verify=False, headers=headers)
                print("%s" % r)
            except ConnectionError as e:
                print("Error %s" % e)

            next_time = datetime.now() + timedelta(hours=1)

        scale.tick_done()


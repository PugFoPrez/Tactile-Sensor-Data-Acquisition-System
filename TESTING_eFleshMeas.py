#!usr/bin/env python3

# Below is adapted from the viz_eflesh.py codes

import time
import numpy as np
import os

import sys
from datetime import datetime
from anyskin import AnySkinProcess
import argparse

defaultPort = "/dev/ttyACM0"

def getData(port=defaultPort):
    # Begin streaming with sensor
    sensor_stream = AnySkinProcess(
        num_mags=5,
        port=port,
    )
    sensor_stream.start()
    time.sleep(1.0)

    def sampleSensor(numSamples=5):
        data = sensor_stream.get_data(num_samples=numSamples)
        data = np.array(data)[:, 1:]
        data = np.mean(data, axis=0)

        data = data.reshape(-1, 3)
        data[:, :2] *= -1 # Flip x and y axes
        data_mag = np.linalg.norm(data, axis=1)
        data_flat = data.flatten()
        norm = np.linalg.norm(data_flat)

        return data_mag

    time.sleep(0.1)
    baseline = sampleSensor(numSamples=20)

    running = True
    data = []
    while running:
        sensor_data = sampleSensor(numSamples=3)
        data.append(sensor_data - baseline)
        print(data[-1])
        time.sleep(1)
    sensor_stream.pause_streaming()
    sensor_stream.join()
    data = np.array(data)

if __name__ == "__main__":
    getData()
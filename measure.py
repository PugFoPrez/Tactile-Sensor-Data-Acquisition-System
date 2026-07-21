#!/usr/bin/env python3

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

sensorStream = None

class measurement:
    def __init__(self, position=[0,0,0], loadCell=[0], eFlesh=[0,0,0,0,0]):
        self.position = position
        self.loadCell = loadCell
        self.eFlesh = eFlesh

measurements = []

class eFleshMeasure:
    def initStreaming(port=defaultPort):
        # Begin streaming with sensor
        sensorStream = AnySkinProcess(
            num_mags=5,
            port=port,
        )
        sensorStream.start()
        time.sleep(0.5)

    def stopStreaming():
        if sensorStream is not None:
            sensorStream.pause_streaming()
            sensorStream.join()

    def sampleSensor(numSamples=5):
        if sensorStream is None:
            eFleshMeasure.initStreaming()

        data = sensorStream.get_data(num_samples=numSamples)
        data = np.array(data)[:, 1:]
        data = np.mean(data, axis=0)

        data = data.reshape(-1, 3)
        data[:, :2] *= -1 # Flip x and y axes
        data_mag = np.linalg.norm(data, axis=1)
        # data_flat = data.flatten()
        # norm = np.linalg.norm(data_flat)

        return data_mag

def saveData(pos, measEFlesh=True, measLoadCell=True):
    # Get eFlesh measurements
    if measEFlesh:
        ef_baseline = eFleshMeasure.sampleSensor(numSamples=20)
        ef_sensorData = eFleshMeasure.sampleSensor(numSamples=3)
        ef_val = ef_sensorData - ef_baseline

    # Save measurements
    measurements.append(measurement(position=pos, eFlesh=ef_val))
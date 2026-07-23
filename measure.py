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

class measurement:
    def __init__(self, position=[0,0,0], loadCell=[0], eFlesh=[0,0,0,0,0]):
        self.position = position
        self.loadCell = loadCell
        self.eFlesh = eFlesh

measurements = []

class eFleshMeasure:
    sensorStream = None
    ef_baseline = None

    @classmethod
    def initStreaming(cls, port=defaultPort):
        # Begin streaming with sensor
        cls.sensorStream = AnySkinProcess(
            num_mags=5,
            port=port,
        )
        cls.sensorStream.start()
        time.sleep(0.5)

    @classmethod
    def stopStreaming(cls):
        if cls.sensorStream is not None:
            cls.sensorStream.pause_streaming()
            cls.sensorStream.join()

    @classmethod
    def sampleSensor(cls, numSamples=5):
        if cls.sensorStream is None:
            eFleshMeasure.initStreaming()

        data = cls.sensorStream.get_data(num_samples=numSamples)
        data = np.array(data)[:, 1:]
        data = np.mean(data, axis=0)

        data = data.reshape(-1, 3)
        data[:, :2] *= -1 # Flip x and y axes
        data_mag = np.linalg.norm(data, axis=1)
        # data_flat = data.flatten()
        # norm = np.linalg.norm(data_flat)

        return data_mag

    @classmethod
    def setBaseline(cls, numSamples=20):
        cls.ef_baseline = eFleshMeasure.sampleSensor(numSamples=numSamples)

def saveData(pos):
    # Get eFlesh measurements
    ef_sensorData = eFleshMeasure.sampleSensor(numSamples=3)
    ef_val = ef_sensorData - eFleshMeasure.ef_baseline
    print(f"Measured EF: {ef_val}")

    # Save measurements
    measurements.append(measurement(position=pos, eFlesh=ef_val))
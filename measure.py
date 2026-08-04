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

import serial

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

class loadCellMeasure:
    srl = None
    reading_tare = 0
    reading_ref = float('inf')
    mass_ref = float('inf')

    @classmethod
    def initSensor(cls, port=defaultPort):
        cls.srl = serial.Serial(port, 9600, timeout=1)
        time.sleep(0.1)
        cls.srl.reset_input_buffer()

    @classmethod
    def tareSensor(cls, numSamples=20):
        cls.reading_tare = cls.sampleRawVal(numSamples)

    @classmethod
    def calibrate(cls, knownMass, numSamples=20):
        cls.mass_ref = knownMass
        cls.reading_ref = cls.sampleRawVal(numSamples)

    @classmethod
    def sampleRawVal(cls, numSamples=5):
        #TODO num samples - below is Claude generated - TODO verify
        cls.srl.reset_input_buffer()  # discard stale backlog first
        # Throw away one line, since it may have been mid-transmission when we flushed
        cls.srl.readline()

        values = []
        while len(values) < numSamples:
            raw = cls.srl.readline()
            line = raw.decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            try:
                values.append(int(float(line)))
            except ValueError:
                continue

        return sum(values) / len(values)

    @classmethod
    def sampleSensor(cls, numSamples=5):
        raw = cls.sampleRawVal()

        fraction_of_ref_mass = (raw - cls.reading_tare) / (cls.reading_ref - cls.reading_tare)
        mass = fraction_of_ref_mass * cls.mass_ref
        return mass

def saveData(pos):
    # Get eFlesh measurements
    ef_sensorData = eFleshMeasure.sampleSensor(numSamples=3)
    ef_val = ef_sensorData - eFleshMeasure.ef_baseline
    print(f"Measured EF: {ef_val}")

    # Get load cell measurements
    lc_sensorData = loadCellMeasure.sampleSensor(numSamples=3)
    print(f"Measured LC: {lc_sensorData}")

    # Save measurements
    measurements.append(measurement(position=pos, eFlesh=ef_val, loadCell=lc_sensorData))

def main():
    loadCellMeasure.initSensor("/dev/ttyACM0")

    print("Tare")
    loadCellMeasure.tareSensor()
    print(f"Tare {loadCellMeasure.reading_tare:0.3f}")

    print("Calibrating in 3 seconds")
    time.sleep(3)
    loadCellMeasure.calibrate(0.377)
    print(f"Ref {loadCellMeasure.reading_ref:0.3f}")

    time.sleep(1)
    while True:
        print(f"Read value of {loadCellMeasure.sampleSensor():0.3f} kg")
        time.sleep(0.5)

if __name__ == "__main__":
    # Standard check to ensure script is run directly
    main()
#!/usr/bin/env python3
#
# Created by Bruce Davidson - Curtin University ID: 20796033
#
# Created:       21th July 2026
# Last Modified: 3rd Sep 2026 (Bruce Davidson)
#
# measure.py
# This script handles the zeroing, calibration, and measurement of the eFlesh sensor and load cell.

# Below is adapted from the viz_eflesh.py codes

import time
import numpy as np
import os

import sys
from anyskin import AnySkinProcess
import argparse

import serial
import csv
from datetime import datetime
import configuration as conf

data_prefix = conf.param("output.measFilePrefix")
data_filename = "measurements/" + data_prefix + "_" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ".csv"

class measurement:
    """Measurement class for 3D printer positioning, load cell value, and eFlesh magnetometer values
    """
    def __init__(self, position=[0,0,0], loadCell=[0], eFlesh=[0,0,0,0,0]):
        """Initialises a new measurement object

        Args:
            position (list, optional): The X,Y,Z position of the printer toolhead. Defaults to [0,0,0].
            loadCell (list, optional): The load cell measured value. Defaults to [0].
            eFlesh (list, optional): The eFlesh magnetometer sensors measured values. Defaults to [0,0,0,0,0].
        """
        self.position = position
        self.loadCell = loadCell
        self.eFlesh = eFlesh

    def flatten(self, fieldnames):
        """Converts the variable structure of the measurement class into a single one-dimensional dictionary.

        Args:
            fieldnames (string list): Field names of each column in the dictionary

        Returns:
            Dictionary: Flattened variable structure
        """
        values = list(self.position) + [self.loadCell] + list(self.eFlesh)
        return dict(zip(fieldnames, values))

class eFleshMeasure:
    """Class of eFlesh measuring related functions.
    """
    sensorStream = None
    ef_baseline = None

    @classmethod
    def initStreaming(cls, port):
        """Configure streaming to the eFlesh AnySkin board.

        Args:
            port (string): The USB port the eFlesh board is connected to.
        """
        # Begin streaming with sensor
        cls.sensorStream = AnySkinProcess(
            num_mags=5,
            port=port,
        )
        cls.sensorStream.start()
        time.sleep(0.5)

    @classmethod
    def stopStreaming(cls):
        """Close the serial stream with the eFlesh board.
        """
        if cls.sensorStream is not None:
            cls.sensorStream.pause_streaming()
            cls.sensorStream.join()

    @classmethod
    def sampleSensor(cls, numSamples=5):
        """Read the current values of the eFlesh sensor.

        Args:
            numSamples (int, optional): Number of samples to average over. Defaults to 5.

        Returns:
            float list: eFlesh board measurements for each magnetometer
        """
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
        """Set the zero reading of the board.
        Note that this does not impact the following readings, and so ef_baseline must be used when determining the read value

        Args:
            numSamples (int, optional): The number of samples to average over. Defaults to 20.
        """
        cls.ef_baseline = eFleshMeasure.sampleSensor(numSamples=numSamples)

class loadCellMeasure:
    """Class of load cell measuring functions
    """
    srl = None
    reading_tare = 0
    reading_ref = float('inf')
    mass_ref = float('inf')

    @classmethod
    def initSensor(cls, port):
        """Initialise the serial communication with the specified USB port.

        Args:
            port (string): Which USB port to set up serial communication on.
        """
        cls.srl = serial.Serial(port, 9600, timeout=1)
        time.sleep(0.1)
        cls.srl.reset_input_buffer()

    @classmethod
    def tareSensor(cls, numSamples=20):
        """Set the zero value of the sensor.
        Note that unlike the eFlesh sensor, this tare value is accounted for when using sampleSensor().

        Args:
            numSamples (int, optional): The number of samples to average over. Defaults to 20.
        """
        cls.reading_tare = cls.sampleRawVal(numSamples)

    @classmethod
    def calibrate(cls, knownMass, numSamples=20, overrideRefVal=None):
        """Calibrate the sensor using the tare and reference readings.

        Args:
            knownMass (_type_): The reference mass reading (in kg) that was recorded during calibration.
            numSamples (int, optional): How many samples to average over. Defaults to 20.
        """
        cls.mass_ref = knownMass
        if overrideRefVal is None:
            cls.reading_ref = cls.sampleRawVal(numSamples)
        else:
            cls.reading_ref = overrideRefVal

        # Check for errors in reference value reading
        # if cls.reading_ref == 0:
            # raise ValueError("Reference reading for the load cell was 0 which is not allowed.")

    @classmethod
    def sampleRawVal(cls, numSamples=5):
        """Read the raw ADC values from the load cell sensor.

        Args:
            numSamples (int, optional): The number of samples to average over. Defaults to 5.

        Returns:
            _type_: _description_
        """
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
        """Get the mass reading from the sensor (in kg)

        Args:
            numSamples (int, optional): The number of samples to average over. Defaults to 5.

        Returns:
            _type_: _description_
        """
        raw = cls.sampleRawVal(numSamples=numSamples)

        fraction_of_ref_mass = (raw - cls.reading_tare) / (cls.reading_ref - cls.reading_tare)
        mass = fraction_of_ref_mass * cls.mass_ref
        return mass

def saveData(pos):
    """Saves the current readings from the eFlesh sensor and load cell sensor, as well as the provided position to the measurements file.

    Args:
        pos (Tuple of (X, Y, Z)): Position of the tool head
    """
    # Get eFlesh measurements
    ef_sensorData = eFleshMeasure.sampleSensor(numSamples=3)
    ef_val = ef_sensorData - eFleshMeasure.ef_baseline

    # Get load cell measurements
    lc_sensorData = loadCellMeasure.sampleSensor(numSamples=3)

    # Save measurements
    appendData(measurement(position=pos, eFlesh=ef_val, loadCell=lc_sensorData))

def appendData(measurement, filename=data_filename):
    """Writes the stored measurement data to the specified file in CSV format.

    Args:
        measurements (measurement object): The readings to append to the measurements file.
        filename (string, optional): The name of the file to save the sensor measurements to. Defaults to data_filename.
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    fieldnames = ["X", "Y", "Z", "LoadCell(kg)", "eFlesh1", "eFlesh2", "eFlesh3", "eFlesh4", "eFlesh5"]

    if not os.path.isfile(filename):
        data_file = open(filename, "+w", newline="")
        writer = csv.DictWriter(data_file, fieldnames=fieldnames)
        writer.writeheader() # New set of measurements, requires header
    else:
        data_file = open(filename, "+a", newline="")
        writer = csv.DictWriter(data_file, fieldnames=fieldnames)

    writer.writerow(measurement.flatten(fieldnames))

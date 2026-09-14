# eFlesh Data Acquisition System

Developed by Bruce Davidson (Student ID: 20796033), Curtin University for undergraduate final year project.
Below is a guide for use on Linux systems (Tested on Ubuntu 25.10). It covers how to install and setup the repository, and how to run the data acquisition code.

#todo Update to include codes for Windows based computers

Acknowledgements:
- The 3D printer control code is based off of user XDGFX's Coordinate Measuring Machine repository on [Github](https://github.com/XDGFX/gcode-cmm).
- The ReSkin sensor library for installation guides for the eFlesh sensor, which can be found on [Github](https://github.com/raunaqbhirangi/reskin_sensor).
- The Adafruit Arduino IDE setup for flashing code onto the QT Py board, which can be found [here](https://learn.adafruit.com/adafruit-qt-py/arduino-ide-setup).
- The eFlesh sensor data code is based off of the codes found in the eFlesh repository on [Github](https://github.com/notvenky/eFlesh). The eFlesh publication can be found [here](https://arxiv.org/pdf/2506.09994).
- The CircuitPython script for the load cell is based off of the codes provided in [Adafruit ADC Development Guides](https://cdn-learn.adafruit.com/downloads/pdf/adafruit-hx711-24-bit-adc.pdf).

## Setup

### Installing the repository

The repository can be downloaded from Github using: `git clone https://github.com/PugFoPrez/EEET4000-DataAcquisition.git`

### Setting up the python environment

Install the required python packages using `pip install -r requirements.txt`. This will install generic packages as well as ones for terminal and device communication.

### Setting up the sensors

#### 3D Printer

The 3D printer needs to be connected to the computer through its serial interface. On the Ender 3 V2 this will be the front panel Micro-USB connection. Note that this will turn the LCD on, but the printer still needs to be connected to mains power through its power supply connection.

The USB device location will need to be found using `ls /dev/ | grep -e ACM -e USB`. For example, the device would be listed as `ttyUSB0`. This will then need to be entered into the Python script as `/dev/ttyUSB0`.

The printer's hotend needs to be removed from the printhead and replaced with the load cell holder. The design for the load cell holder can be found #todo [here]().

A holder for the eFlesh sensor has also been designed to keep the eFlesh board in place during probing. The design for the holder can be found #todo [here](). Note that this has been designed for one implementation of an eFlesh/magnetometer board holder and may need redesign for other implementations.

#### eFlesh

The `reskin-sensor` and `anyskin` packages are required to get data from the eFlesh board. Please make sure these are installed using `pip install reskin-sensor anyskin`.

The eFlesh magnetometer board will first need to be connected to the supported microcontroller board. In this project, an Adafruit QT Py board was used and connected to the eFlesh magnetometer board using the provided QWIIC cable. Once connected to the computer through the board's USB connection the USB device needs to be located again which is once again done using the `ls /dev/ | grep -e ACM -e USB` command. It may be the case where insufficient permissions are granted for device access, which can be rectified using `sudo chmod a+rw /dev/<portName>`.

#todo image of sensor configuration

The microcontroller code must now be uploaded to the QT Py board which is done following the process described by the [ReSkin Arduino Guide](https://github.com/raunaqbhirangi/reskin_sensor/tree/main/arduino). The ReSkin-Arduino Git repository will need to be downloaded. Note that this will require the Arduino IDE to be installed. Please follow steps on [this page](https://learn.adafruit.com/adafruit-qt-py/arduino-ide-setup) for installation of the Arduino IDE, and steps on [this page](https://learn.adafruit.com/adafruit-qt-py/using-with-arduino-ide) for flashing code onto the QT Py board. One point of note is that the "TinyUSB" option needed to be selected under Tools > USB Stack menu in the Arduino IDE for compilation to work.

#todo note down what codes were used from the repo and the issues with getting the MLX90393 library working.

#### Load Cell

The load cell requires a more complex physical setup to be able to connect to a computer which has been based off of the Adafruit guide provided [here](https://cdn-learn.adafruit.com/downloads/pdf/adafruit-hx711-24-bit-adc.pdf). The load cell must first be connected to an ADC board, which must then be connected to an appropriate microcontroller to send the ADC readings to the computer's serial interface. In this project a DYHW-108 load cell was connected through an HX711 ADC to an Adafruit Feather RP2040 microcontroller. The wiring is done as follows:

Load cell to ADC:
- Red wire (Excitation +) to the `E+` terminal
- Green wire (Signal +) to the `A+` terminal
- White wire (Signal -) to the `A-` terminal
- Black wire (Excitation -) to the `E-` terminal
- Note that the load cell came with a yellow wire (assumed to be a shielding wire) which was left disconnected. #todo figure out yellow wire

ADC to Microcontroller:
- `Vin` terminal to the `3.3V` terminal
- `GND` terminal to the `GND` terminal
- `SCK` terminal to the `6` terminal
- `DATA` terminal to the `5` terminal

Note that the ADC to microcontroller connections did not have a terminal block provided and required soldering to make the connections.

#todo image of sensor configuration

CircuitPython was then used to configure the microcontroller for serial communication. Please follow the previously mentioned Adafruit guide for steps on how to do this. The code that must be uploaded to the microcontroller's `code.py` file is as follows:

```python
# SPDX-FileCopyrightText: Copyright (c) 2024 Liz Clark for Adafruit Industries
#
# SPDX-License-Identifier: MIT
# 
# Modified by Bruce Davidson July 2026
# For Curtin University, Final Year Project of EEET4000/4001.

import time
import board
import digitalio
from adafruit_hx711.hx711 import HX711
from adafruit_hx711.analog_in import AnalogIn

data = digitalio.DigitalInOut(board.D5)
data.direction = digitalio.Direction.INPUT
clock = digitalio.DigitalInOut(board.D6)
clock.direction = digitalio.Direction.OUTPUT
hx711 = HX711(data, clock)
channel_a = AnalogIn(hx711, HX711.CHAN_A_GAIN_128)
# channel_b = AnalogIn(hx711, HX711.CHAN_B_GAIN_32)

while True:
    print(f"{channel_a.value}")
    time.sleep(0.1)
```

The primary setup of the load cell has now been completed. The following steps briefly describe additions made to the load cell for probing of the eFlesh sensor.

A 3D printed probing tip needs to be attached to the load cell so that it can properly interact with the eFlesh sensor and excite the load cell. The load cell is to be placed into the previously mentioned load cell holder 'upside down', i.e., with the small dimple facing upwards and flat side facing downwards. The 3D printed tip was then attached using Blu-Tack to the flat face. This setup provides a good interface for adhering the tip to the load cell while allowing the load cell dimple to press onto the printed holder for accurate force measurement. To ensure the load cell remains inside the holder, some sticky tape was applied over the exposed load cell side/load cell holder #todo better way to hold it in?

#todo something something load cell probe tip

The final load cell configuration is shown below.

#todo image of load cell configuration

## Running the script
Configuring the script is subject to change as it is developed.

Most settings for the data acquisition script are stored in the `settings.json` file and should be self explanatory. Probing related settings are kept in the `generator.py` file as they are are subject to change depending on the probing implementation programmed by the user. Explanations of the settings file are given in the [settings file](#the-settings-file)

In `generator.py` the main function will be were different probing method should be written as code - a grid based approach as well as a single normal force approach has been provided to be used as a template.

The position of the sensor relative to the machine's home position will also need to be set. This can be accomplished by using the machine's control panel to move the probing head to the top, south-western most (left of, and closest to the user) point of the sensor. Note for the eFlesh sensor that some margin was used in the original paper's design for the 'active' area of the sensor.

Once the script has been properly set up, it can be run by simply executing `python3 generator.py` on the command line.

The script will then prompt to keep any objects clear of the sensors to allow for a zero point to be established for each sensor.

The load cell will then need to be calibrated. This will require that the eFlesh sensor and holder be removed from the CNC machine's working area and replaced with a scale (ideally with a maximum range approximately equal to the load cell's full scale specification). Using the controls as listed, the load cell needs to be pushed onto the scale to provide a reference value. Once a reference value is recorded the calibration step should be completed using the prompted button ("F") immediately - the reading changes with time due flex and springiness of the platform. Then enter the reading in kilograms. This will complete the calibration process.

The script will now continue on to probe the sensor as specified in the main function. The outputs will be saved in the `measurements/` folder.

## Overview of the codes
Python scripts:
- `communication.py`: This script handles serial communication with the CNC machine using gcode.
- `export.py`: This script handles exporting gcode to both the CNC machine's serial line and to the `testing.gcode` file for checking.
- `generator.py`: This is the main script used to configure the probing behaviour of the script.
- `manipulation.py`: This script handles formatting of CNC machine behaviours into appropriate gcode commands.
- `measure.py`: This script handles the zeroing, calibration, and measurement of the eFlesh sensor and load cell.
- `terminal.py`: This script handles getting user input from the terminal and changing terminal behaviour. Note that the behaviours in this script may cause the user's terminal to not display anything (If the display mode is never reset). This can be fixed by running `reset` in the terminal.

Configuration:
- `settings.json`: User defined settings to be used to configure communication and probing behaviour.

Other files:
- `requirements.txt`: Listing of all required packages for the script.

### The Settings File
#### Communications Settings
The communications settings related to the serial communication between the eFlesh sensor, load cell, and the CNC machine.

The port related settings should be entered as `"/dev/<PORTNAME>"`, where the port name can be found using the process described in the [sensor setup](#setting-up-the-sensors) section.

The baud rate should not need to be changed from the set value of 115,200.

The `disableCncComms` parameter is useful for development purposes where the CNC machine is not physically available. For actual data acquisition, it MUST be set to `false`, otherwise no actual probing will occur.

#### CNC Settings
The min XYZ and max XYZ parameters should correspond to the CNC machines minimum and maximum bounds.

The hop height sets how far the machine head should 'hop' upwards between movements (if a hop is required).

The feedrate XY and Z parameters describe how quickly the CNC machine can move in each axis direction. The values of XY at 10,000 and Z at 600 have been set based on an Ender 3 V2 machine.

#### Output Settings
The gcode file is where a copy of the gcode commands get stored for later reference.

The measurement file prefix will be used to prefix all measurement files and should be changed if the user wants to differentiate measurements. All measurement files will be placed in the measurements folder, and will be named like: `<PREFIX>_2026-08-04 16:11:58.csv`

## Tricks and Tips
- The order of connection determines whether a USB device appears as `ACM0` or `ACM1`, connecting devices in the same order each time will prevent having to change settings on every iteration.
- The eFlesh sensor's status can be confirmed by using the visualiser script available from the eFlesh repository. This takes some set up to get running.
- The load cell's status can be confirmed by checking the serial output using a tool like `minicom` on Linux.
- The use of the script and it's user input functions may cause the terminal to not return to its normal state, causing characters to not appear on the screen. This can be fixed by typing `reset` into the terminal, or closing and re-opening the terminal.
- If the output measurements data seems to not be coming in properly (e.g., constant values or all zeroes), unplugging the USB cables from the computer as well as from the microcontroller and plugging them back in may resolve it.
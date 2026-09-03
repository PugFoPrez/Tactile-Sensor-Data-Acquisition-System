#!/usr/bin/env python3

# Created by Bruce Davidson - Curtin University ID: 20796033
#
# Created:       3rd September 2026
# Last Modified: 3rd Sep 2026 (Bruce Davidson)
#
# configuration.py
# This script configures loads the settings from the settings.json file

import json

# Below function is adapted from XDGFX
def readSettings():
    """This function reads settings from the settings.json file which are used in configuring parameters associated with the serial communication.

    Returns:
        JSON Object: Stored settings as a JSON object
    """
    with open("settings.json") as settings_json:
        settings = json.load(settings_json)
        return settings

def param(paramName):
    """This functions returns the value for the specified parameter from the "settings.json" file.
    
    Returns:
        String: Value of specified JSON parameter
    """
    value = readSettings()
    # Recursively step through all keys in paramName (Nested JSON objects)
    for key in paramName.split("."):
        value = value[key]
    return value
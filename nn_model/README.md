# eFlesh Data Acquisition System - Neural Network Model

Developed by Bruce Davidson (Student ID: 20796033), Curtin University for undergraduate final year project.
    
Below is a guide for use on Linux systems (Tested on Ubuntu 25.10). It covers how the data is expected to be structured, the general structure of the neural network model, as well as the output. For general setup and installation of the repository, please look through the main README documentation in the parent folder.

Acknowledgements:
- The eFlesh characterisation code is based off of the codes found in the eFlesh repository on [Github](https://github.com/notvenky/eFlesh). The eFlesh publication can be found [here](https://arxiv.org/pdf/2506.09994).
- Claude AI has been used in the development of this code as the Neural Network development is not of core concern for this project.


## Setup

### Installing required packages

Install the required python packages using `pip install -r requirements.txt`. This will install generic packages as well as ones for terminal and device communication. Ensure that this is the requirements file from the `nn_model/` folder as this contains different packages to the core requirements file.

## Running the script
The script has variables at the top of the file for modifying the parameters of training. The IO parameters will need to point towards the directory where the measurements are stored as well as the prefix used in the filename (assuming these have been generated using the `generator.py` script). The output directory can also be set here.

## Overview of the codes
`training.py` is used to train the machine learning model based on data collected by the data acquisition system.
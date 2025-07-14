import ctypes
import os
import numpy as np
from math import trunc
from time import sleep
import sys
from pylablib.devices import Thorlabs

#get list of devices and serial numbers, index into serial number of first device
serial=Thorlabs.list_kinesis_devices()[0][0]

#define stage
stage=Thorlabs.KinesisMotor(serial)

#get stage position
position=stage.get_position()

#get unit scale
#print(stage.get_scale())

#move stage
print(position)
stage.home()
print(stage.get_velocity_parameters())
# stage.setup_velocity(max_velocity=stage.get_velocity_parameters()[2])
stage.move_by(1000)
stage.wait_move()
print(stage.get_position())
stage.close()
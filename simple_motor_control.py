import motor_control.pico_motor_control_NP as mc
from pylablib.devices import Newport
import sys

# NOTES:
# > Always close motor, if you dont you may get connection error. In that case
#   just restart the device (sitch off and on).
# > Make sure that stage is not completely backed in or out, and make sure that the collet aroung the 
#   motor fixture is torqued down enough (this wil present slipping).
# > Fatal errors such as failure to connect to the motor will terminate the program.

if __name__ == "__main__":
    # Check for motor controller connection
    mc.check_controller_connection()

    # Connect to motor
    motor = mc.connect_to_motor()

    # Manual motor jog through terminal
    mc.manual_jog_NP(motor, speed = 2)
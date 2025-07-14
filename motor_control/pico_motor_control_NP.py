from time import sleep
from pylablib.devices import Newport

# Here I make a python module for interacting with the Newport pico motor. It builds on top of pylablib and is tailored
# specifically to automate an experiment I am running (see readme) but it does provide insight into how to
# interact with pylablib and gives some tools for automating your experiments


def check_controller_connection():
    """
    Checks to see whether or not there a motor controller connected
    
    Returns:
        bool: True if at least one controller is found, raises error if not
    """
    # Check for NP controller
    num_controllers_NP = Newport.get_usb_devices_number_picomotor()
    num_controllers_TL = 0  # TODO: (no TL function yet)

    if num_controllers_NP:
        print(f'{num_controllers_NP} Newport motor controller(s) connected')
    if num_controllers_TL:
        print(f'{num_controllers_TL} ThorLabs motor controller(s) connected')
    if not (num_controllers_TL or num_controllers_NP):
        raise ConnectionError("No motor controllers found")
    
    return True
        
def connect_to_motor(index = 0):
    """
    Attempts to instantiate a motor object. By default chooses the first device.
    If you have more than one device may need to test which index corresponds to which device.

    Args:
        index (int): Index of target device, number given by check_controller_connection()
    Returns:
        Newport.Picomotor8742: Motor object
    """
    
    print("Attempting motor connection...")
    motor = Newport.Picomotor8742(index)
    print("Motor connection successful...")
    print("Controller type: " + str(motor.get_device_info()) + "...")
    print("Motor type: " + str(motor.get_motor_type()) + "...")
    print("Current motor position: " + str(motor.get_position()) + "...")
    return motor
        
def manual_jog_NP(motor, axis=1, speed=50):
    stop = 0
    motor.setup_velocity(speed=speed)
    print("Entering manual jog mode...")
    while not stop:
        steps = input("Enter number of steps (or 'q' to quit): ")

        if steps.lower() == 'q':
            stop = 1
            break

        try:
            steps = int(steps)
            motor.move_by(axis, steps)
            motor.wait_move()
            position = motor.get_position(axis)
            print("Moved " + str(steps) + " steps, current position: " + str(position))
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
        except Exception as e:
            print("Motor error: " + str(e))

def move_motor(motor, steps, axis=1, speed=50, repeat=1, delay=2):
    """
    Moves motor some amount of steps at some speed for some amount of times with a delay inbetween
    
    Args:
        motor: NP pico motor object
        steps: the amount of steps to move
        axis: motor axis to move along
        speed: (steps/s)
        repeat: how many times to repeat the movement
        delay: delay between movements (s)
    """
    # Check motor object
    if not isinstance(motor, Newport.Picomotor8742):
        raise TypeError(f"Expected Newport.Picomotor8742 object, got {type(motor).__name__}")
    
    # Set motor speed
    motor.setup_velocity(speed=speed)

    # Move motor
    counter = 0
    while counter < repeat:
        motor.move_by(axis, steps)
        motor.wait_move()
        counter += 1
        sleep(delay)

    return True

import util.motor_control.pico_motor_control_NP as mc
import util.picoscope_control.picoscope_3205D_control as pico_scope
from pylablib.devices import Newport
import numpy as np
import matplotlib.pyplot as plt
import json
import os

dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "DLL"))
os.environ["PATH"] = dll_path + os.pathsep + os.environ.get("PATH", "")


def connect_devices(scope_config):
    # Create scope
    scope = pico_scope.PicoScope3205D(**scope_config)

    # Verify sampling interval
    dt = scope.get_timebase_conversion() / 2
    print(f'Sampling interval: {dt * 1e9} (ns)')

    # Connect to motor
    mc.check_controller_connection()
    motor = mc.connect_to_motor(0)

    return scope, motor

def ftir_scan(scope, motor, scan_config):

    data = []
    positions = []

    for i in range(0, scan_config["totalSteps"], scan_config["stepIntervals"]):
        # Move motor
        mc.move_motor(motor, scan_config["stepIntervals"], axis = 1,
                      speed = scan_config["speed"], repeat = 1, delay = scan_config["delay"])
        
        # Collect signal from scope
        time, signal = scope.collect_data_block() # (ns), (mV)
        data.append((time.tolist(), signal))
        current_position = motor.get_position(1)
        if current_position == 0 or (current_position%5) == 0:
            print(f'Current motor position: {current_position} steps')
        positions.append(current_position)

    return positions, data

def process_data(data, scope_config):

    spectrogram = []

    for i in range(0, len(data), 1):

        length = len(data[i][1])
        # dt = scope.get_timebase_conversion() / 2 # (ns)
        # width = gate_width // dt
        width = 40

        # Create gate function
        trigger_index = -1
        trigger_found = 0
        while not trigger_found and trigger_index < length - 1:
            trigger_index += 1
            if data[i][1][trigger_index] >= scope_config["trigLvl"]:
                trigger_found = 1

        if not trigger_found:
            # if no trigger found assume no signal
            gate = np.zeros(length)
        else:
            gate = np.zeros(length)
            gate[int(trigger_index):int(trigger_index + width)] = 1

        # Apply gate function to signal
        gated_signal = np.array(data[i][1]) * gate
        
        # Average the gated signal
        total = 0
        for value in gated_signal:
            total += value
        avg = total / width

        # Add average to dataset
        spectrogram.append(avg)
    
    return spectrogram

if __name__ == "__main__":
    scope_config = {
        "configA": {'enabled': 1, 'range': 4, 'coupling': 1, 'offset': 0},
        "configB": {'enabled': 0, 'range': 7, 'coupling': 1, 'offset': 0},
        "trigEnable": 1,
        "trigLvl": 60,
        "trigChannel": "PS3000A_CHANNEL_A",
        "trigMode": "PS3000A_LEVEL",
        "trigDirection": "RISING",
        "postTriggerSamples": 100,
        "preTriggerSamples": 15,
        "timeBase": 0
    }

    scan_config = {
        "totalSteps": 1000,
        "stepIntervals": 1,
        "speed": 5,
        "delay": 0.5
    }
    
    # Collect Data
    scope, motor = connect_devices(scope_config)
    motor_positions, pulse_signals = ftir_scan(scope, motor, scan_config)

    ftir_scan = {
        "motor positions": motor_positions, 
        "pulse signals": pulse_signals,
        }
    
    with open("scan_70att_0.1kHz_7-25-25.json", "w") as json_file:
        json.dump(ftir_scan, json_file, indent=4)

    # Process Data

    dt = scope.get_timebase_conversion() / 2
    gate_width = 40 * dt
    spectrogram = process_data(pulse_signals, scope_config)

    # Plot Data
    plt.figure(figsize=(10,5))
    plt.plot(motor_positions, spectrogram, color='r', linewidth=2)
    plt.xlabel("Motor Position (steps)")
    plt.ylabel("Time averaged signal value")
    plt.title("FTIR Spectrogram")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

    ftir_scan = {
        "motor positions": motor_positions, 
        "pulse signals": pulse_signals,
        "spectrogram": spectrogram
        }
    with open("scan_70att_0.1kHz_7-25-25.json", "w") as json_file:
        json.dump(ftir_scan, json_file, indent=4)



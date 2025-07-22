import util.motor_control.pico_motor_control_NP as mc
import util.picoscope_control.picoscope_3205D_control as pico
from pylablib.devices import Newport
import numpy as np
import matplotlib.pyplot as plt


def connect_devices(scope_config):
    # Create scope
    scope = scope.PicoScope3250D(**scope_config)

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
        data.append((time, signal))
        current_position = motor.get_position(1)
        if current_position == 0 or (current_position%5) == 0:
            print(f'Current motor position: {current_position} steps')
        positions.append(current_position)

    return positions, data

def process_data(data, scope, scope_config, gate_width):

    spectrogram = []

    for i in range(0, len(data), 1):

        # Create gate function
        trigger_index = -1
        trigger_found = 0
        while not trigger_found and trigger_index < len(data[i][1]):
            trigger_index += 1
            if data[i][1][trigger_index] >= scope_config["triggerLvl"]:
                trigger_found = 1

        if not trigger_found:
            gate = np.zeros(len(data[i][1]))
        else:
            dt = scope.get_timebase_conversion() / 2 # (ns)
            width = gate_width // dt
            length = len(data[i][1])

            gate = np.zeros(length)
            gate[trigger_index:trigger_index + width] = 1

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
        "configA": {'enabled': 1, 'range': 9, 'coupling': 1, 'offset': 0},
        "configB": {'enabled': 0, 'range': 7, 'coupling': 1, 'offset': 0},
        "trigEnable": 1,
        "trigLvl": 0,
        "trigChannel": "PS3000A_CHANNEL_A",
        "trigMode": "PS3000A_LEVEL",
        "trigDirection": "RISING",
        "postTriggerSamples": 110000,
        "preTriggerSamples": 5000,
        "timeBase": 10
    }

    scan_config = {
        "totalSteps": 50000,
        "stepIntervals": 5,
        "speed": 10,
        "delay": 0.5
    }
    
    # Collect Data
    scope, motor = connect_devices(**scope_config)
    motor_positions, pulse_signals = ftir_scan(scope, motor, **scan_config)

    # Process Data
    dt = scope.get_timebase_conversion() / 2
    gate_width = 5000 * dt
    spectrogram = process_data(pulse_signals, scope, scope_config, gate_width)

    # Plot Data
    plt.figure(figsize=(10,5))
    plt.plot(motor_positions, spectrogram, color='r', linewidth=16)
    plt.xtitle("Motor Position (steps)")
    plt.ytitle("Time averaged signal value")
    plt.title("FTIR Spectrogram")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

    




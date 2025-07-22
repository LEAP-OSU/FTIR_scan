import numpy as np
import matplotlib.pyplot as plt
import util.picoscope_control.picoscope_3205D_control as scope


if __name__ == "__main__":
    # NOTES:
    # > The time interval returned from get_timebase_conversion() is double the actual sampling interval

    scope = scope.PicoScope3205D(
        configA = {'enabled': 1, 'range': 9, 'coupling': 1, 'offset': 0},
        configB = {'enabled': 0, 'range': 7, 'coupling': 1, 'offset': 0},
        trigEnable=1,
        trigLvl=0,
        trigChannel="PS3000A_CHANNEL_A",
        trigMode="PS3000A_LEVEL",
        trigDirection="RISING",
        postTriggerSamples=110000,
        preTriggerSamples=0,
        timeBase=10
        )
    
    # Verify Sampling Interval
    dt = scope.get_timebase_conversion() / 2
    print(f'Sampling Interval: {dt * 1e9} (ns)')

    # Collect Block of data
    time, data = scope.collect_data_block()
    
    # Plot Data
    plt.figure(figsize=(10,5))
    plt.plot(time, data[:], color='r', linewidth=2, label="Channel A")
    plt.xlabel("Time (ns)")
    plt.ylabel("Voltage (mV)")
    plt.title("Voltage vs. Time")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.show()




import numpy as np
import matplotlib.pyplot as plt
import picoscope_control.picoscope_3205D_control as scope


if __name__ == "__main__":
    
    scope = scope.PicoScope3205D(
        configA = {'enabled': 1, 'range': 9, 'coupling': 1, 'offset': 5},
        configB = {'enabled': 0, 'range': 7, 'coupling': 1, 'offset': 0},
        trigEnable=1,
        trigLvl=500,
        trigChannel="PS3000A_CHANNEL_A",
        trigMode="PS3000A_LEVEL",
        trigDirection="RISING",
        postTriggerSamples=50000,
        preTriggerSamples=50000,
        timeBase=20,
        )
    scope.collect_data_block()
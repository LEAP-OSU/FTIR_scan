import ctypes
import os
from picosdk.ps3000a import ps3000a as ps
import numpy as np
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, mV2adc, assert_pico_ok

# NOTES:
# > Run connect() to configure system, use other methods to change settings
# > I reccomend figuring out you scope setting in the GUI first and then configuring here for experiments

class PicoScope3205D:
    model_name = "PicoScope 3205D"
    #TODO: consolidate all strings and enumertion (in c parameters) to use a common scheme, either all string or all enumerations. should be all string as they are human readable.
    #TODO: make conversions between the offset, range, and timeBase integers to actual unit values so that the config for users is more intuitive 
    def __init__(self,
                 configA = {'enabled': 1, 'range': 7, 'coupling': 1, 'offset': 0},
                 configB = {'enabled': 0, 'range': 7, 'coupling': 1, 'offset': 0},
                 trigEnable = 1,
                 trigLvl = 500,
                 trigChannel = "PS3000A_CHANNEL_A",
                 trigMode = "PS3000A_LEVEL",
                 trigDirection = "RISING",
                 preTriggerSamples = 0,
                 postTriggerSamples = 50000,
                 timeBase = 2
                 ):
        """
        Initialize PicoScop Instance

        Args:
            configA / configB:
                enabled: 0 no, 1 yes
                range: look at ps3000aSetChannel Args in Picoscope docs
                coupling: 1 DC, 0 AC
                offset: DC offset
            trigLvl: Trigger level in mV
            trigChannel: A or B for this model, see docs for more info
            trigMode: Level by default see docs for options
            trigDirections: Rising edge by default see docs for options
            preTriggerSamples: 0 by defult
            postTriggerSamples: 50000 by default
            timeBase: determines time window for block data collection, see docs for how this is calculated
        """

        # Private Properties
        # TODO: Make decorators for reading 
        self._status = {}
        self._chandle = ctypes.c_int16()
        self._is_connected = False
        self._maxADC = ctypes.c_int16()

        # Config Properties
        self.channel_config = {
            0 : configA,
            1 : configB
        }

        if trigChannel == "PS3000A_CHANNEL_A":
            trigChannelIdx = 0
        elif trigChannel == "PS3000A_CHANNEL_B":
            trigChannelIdx = 1
        else:
            raise ValueError("trigger channel must be an appropriate key (see docs)")
        
        self.trigger_config = {
            'trigLvl': trigLvl,
            'trigChannel': trigChannel,
            'trigIdx': trigChannelIdx,
            'trigMode': trigMode,
            'nChannelTrig': 1,
            'trigDirection': trigDirection,
            'trigEnable': trigEnable
        }
        
        self.sampling_config = {
            'preTriggerSamples': preTriggerSamples,
            'postTriggerSamples': postTriggerSamples,
            'timeBase': timeBase,
            'maxADC': None
        }

        self._connect()


    # Private Functions
    def _connect(self):
        """
        Thid function performs the following tasks:
        > Opens the picoscope unit
        > Configures the picoscop channels based on the attributes given at instantiation
        > Calculates the maxADC for the device
        > Sets up a simple trigger based on the instantiated attributes
        > All function calls handle C level code and will raise error if they fail (here atleast)
        """
        try:
            # Open picoscope device
            self._open_picoscope()

            # Attempt PicoScope Channel Config based of instantiated attributes
            self._configure_channels()

            # Finds the max ADC count
            self._calc_maxADC()
            
            # Setup Simple Trigger
            self._setup_simple_trigger()

            self._is_connected = True

            return True
            
        except Exception as e:
            print(f"PicoScope connection failed: {e}")
            self._cleanup_failed_connection()
            raise
        
    def _open_picoscope(self):
        print("Attempting to open picoscope device...")
        try:
            self._status["openunit"] = ps.ps3000aOpenUnit(ctypes.byref(self._chandle), None)
            assert_pico_ok(self._status["openunit"])
            print("Picoscope device opened...")
            return True
        except Exception as e:
            print(f'Error opening picoscope device: {e}')
            self._cleanup_failed_connection()
            raise

    def _cleanup_failed_connection(self):
        """
        Clean up after failed connection/configuration attempt, this is used when a c level assert throws an exception.
        These exception will end the program as an internal status code is not "PICO_OK" and the funciton calls are invalid.
        """
        if self._chandle.value != 0:
            try:
                ps.ps3000aCloseUnit(self._chandle)
            except:
                pass  # Ignore cleanup errors
        self._chandle = ctypes.c_int16()
        self._is_connected = False

    def _configure_channels(self):
        print("Attempting to configure device channels...")
        try:
            self._status["setChA"] = ps.ps3000aSetChannel(self._chandle, 0,
                                                    self.channel_config[0]['enabled'],
                                                    self.channel_config[0]['coupling'],
                                                    self.channel_config[0]['range'],
                                                    self.channel_config[0]['offset'])
            self._status["setChB"] = ps.ps3000aSetChannel(self._chandle, 1,
                                                    self.channel_config[1]['enabled'],
                                                    self.channel_config[1]['coupling'],
                                                    self.channel_config[1]['range'],
                                                    self.channel_config[1]['offset'])
            assert_pico_ok(self._status["setChA"])
            assert_pico_ok(self._status["setChB"])
            print("Channels configured (see PicoScope docs for enumerations):")
            print("Channel A: " + str(self.channel_config[0]))
            print("Channel B: " + str(self.channel_config[1]))
        except Exception as e:
            print(f'Error configuring channels: {e}')
            self._cleanup_failed_connection()
            raise

    def _calc_maxADC(self):
        # TODO: remove maxADC from sampling config and make sure the other function use the object property
        print("Determining maxADC...")
        try:
            maxADC = ctypes.c_int16()
            self._status["maximumValue"] = ps.ps3000aMaximumValue(self._chandle, ctypes.byref(maxADC))
            assert_pico_ok(self._status["maximumValue"])
            self._maxADC = maxADC
            self.sampling_config['maxADC'] = maxADC
            print(f'maxADC = {maxADC}')
        except Exception as e:
            print(f'Error determing maxADC: {e}')
            self._cleanup_failed_connection()
            raise

    def _direction_to_bool(self, value):
            if value == "RISING":
                return 2
            else:
                raise ValueError("Currently only supports rising, can change this though")

    def _setup_simple_trigger(self):
        print("Setting up simple trigger...")
        try:
            channel = self.channel_to_bool(self.trigger_config['trigChannel'])
            threshold = mV2adc(self.trigger_config['trigLvl'], self.channel_config[channel]['range'], self.sampling_config['maxADC'])
            direction = self._direction_to_bool(self.trigger_config['trigDirection'])

            self._status["trigger"] = ps.ps3000aSetSimpleTrigger(self._chandle,
                                                             self.trigger_config['trigEnable'],
                                                             channel,
                                                             threshold,
                                                             direction,
                                                             0,
                                                             1000
                                                             )
            assert_pico_ok(self._status["trigger"])
            print("Simple Trigger setup complete...")
            print("Simple trigger settings: " + str(self.trigger_config))
            return True
        
        except Exception as e:
            print(f"Error setting up simple trigger: {e}")
            self._cleanup_failed_connection()
            raise
        
    def channel_to_bool(self, value):
        if value == "PS3000A_CHANNEL_A":
            return 0
        elif value == "PS3000A_CHANNEL_B":
            return 1
        else:  # None or anything else
            raise ValueError("Incompatiable trigger channel (must be A or B, see docs for key)")

    def get_timebase_conversion(self):
        """
        Calculates the sampling interval based on the current timebase. Throws an error if an invalid timbase is used
        Args:
            self: picoscope object
        returns:
            time: sampling interval
        """
        def formula1(timebase):
            time = (2**timebase)/500000000
            return time
        def formula2(timebase):
            time = (timebase-2) / 62500000
            return time
        
        timeBase = self.sampling_config['timeBase']
        if timeBase <= 2 and timeBase >= 0:
            time = formula1(timeBase)
        elif timeBase > 2 and timeBase <= (2**32 - 1):
            time = formula2(timeBase)
        else:
            raise ValueError("Time base must be >= 0 and <= 2^32 - 1")

        return time

    def setup_advanced_trigger(self):
        """
        Setup advanced trigger
        """

        try:
            # Set trigger conditions
            trigger_channel = self.trigger_config['trigIdx']
            if trigger_channel == 0:  # Channel A
                self.setup_trigger_conditions(channel_a=True, channel_b=None)
                self.setup_trigger_directions(channel_a="RISING", channel_b="NONE")
            elif trigger_channel == 1:  # Channel B
                self.setup_trigger_conditions(channel_a=None, channel_b=True)
                self.setup_trigger_directions(channel_a="NONE", channel_b="RISING")

            # Set trigger properties 
            adc_trigger_level = mV2adc(self.trigger_config['trigLvl'],
                                       self.channel_config[self.trigger_config['trigIdx']]['range'],
                                       self._maxADC
                                       )
            channel_properties = ps.PS3000A_TRIGGER_CHANNEL_PROPERTIES(adc_trigger_level,
                                                                       10,
                                                                       adc_trigger_level,
                                                                       10,
                                                                       ps.PS3000A_CHANNEL[self.trigger_config['trigChannel']],
                                                                       ps.PS3000A_THRESHOLD_MODE[self.trigger_config['trigMode']]
                                                                       )
            n_channel_properties = 1
            auto_trigger_milliseconds = 10000
            self._status["setTrigProp"] = ps.ps3000aSetTriggerChannelProperties(self._chandle, ctypes.byref(channel_properties), n_channel_properties, 0, auto_trigger_milliseconds)
            assert_pico_ok(self._status["setTrigProp"])
            print("Trigger settings: " + str(self.trigger_config))
            print("Trigger setup...")
            return True
        
        except Exception as e:
            print(f"Trigger setup failes: {e}")
            return False

    def setup_trigger_conditions(self, channel_a=True, channel_b=False):
        """
        Set up trigger conditions - which channels must be active for trigger
    
        Args:
            channel_a: True = must trigger, False = must not trigger, None = don't care
            channel_b: True = must trigger, False = must not trigger, None = don't care
        """
        try:
            # Convert boolean to trigger state
            def bool_to_state(value):
                if value is True:
                    return ps.PS3000A_TRIGGER_STATE["PS3000A_CONDITION_TRUE"]
                elif value is False:
                    return ps.PS3000A_TRIGGER_STATE["PS3000A_CONDITION_FALSE"]
                else:  # None or anything else
                    return ps.PS3000A_TRIGGER_STATE["PS3000A_CONDITION_DONT_CARE"]
        
            # Set up conditions for all 8 possible trigger sources
            conditions = ps.PS3000A_TRIGGER_CONDITIONS_V2(
                bool_to_state(channel_a),      # Channel A
                bool_to_state(channel_b),      # Channel B
                bool_to_state(None),           # Channel C (don't care)
                bool_to_state(None),           # Channel D (don't care)
                bool_to_state(None),           # External (don't care)
                bool_to_state(None),           # AUX (don't care)
                bool_to_state(None),           # PWQ (don't care)
                bool_to_state(None)            # Digital (don't care)
            )
        
            n_conditions = 1
            self._status["setTrigCond"] = ps.ps3000aSetTriggerChannelConditionsV2(
                self._chandle, 
                ctypes.byref(conditions), 
                n_conditions
            )
            assert_pico_ok(self._status["setTrigCond"])
        
            print(f"Trigger conditions set: Channel A = {channel_a}, Channel B = {channel_b}")
            return True
        
        except Exception as e:
            print(f"Error setting trigger conditions: {e}")
            return False     

    def setup_trigger_directions(self, channel_a="RISING", channel_b="NONE"):
        """
        Set up trigger directions - what edge/direction triggers each channel
    
        Args:
            channel_a: "RISING", "FALLING", "RISING_OR_FALLING", "ABOVE", "BELOW", "NONE"
            channel_b: "RISING", "FALLING", "RISING_OR_FALLING", "ABOVE", "BELOW", "NONE"
        """
        try:
            # Convert string to trigger direction constant
            def string_to_direction(direction_str):
                direction_map = {
                    "RISING": "PS3000A_RISING",
                    "FALLING": "PS3000A_FALLING", 
                    "RISING_OR_FALLING": "PS3000A_RISING_OR_FALLING",
                    "ABOVE": "PS3000A_ABOVE",
                    "BELOW": "PS3000A_BELOW",
                    "NONE": "PS3000A_NONE",
                    None: "PS3000A_NONE"
                }
            
                direction_key = direction_map.get(direction_str, "PS3000A_NONE")
                return ps.PS3000A_THRESHOLD_DIRECTION[direction_key]
        
            # Set directions for all channels
            channel_a_direction = string_to_direction(channel_a)
            channel_b_direction = string_to_direction(channel_b)
            channel_c_direction = string_to_direction("NONE")  # Not used in 3205D
            channel_d_direction = string_to_direction("NONE")  # Not used in 3205D
            ext_direction = string_to_direction("NONE")        # External trigger
            aux_direction = string_to_direction("NONE")        # AUX trigger
        
            # Apply trigger directions
            self._status["setTrigDir"] = ps.ps3000aSetTriggerChannelDirections(
                self._chandle,
                channel_a_direction,    # Channel A direction
                channel_b_direction,    # Channel B direction  
                channel_c_direction,    # Channel C direction (unused)
                channel_d_direction,    # Channel D direction (unused)
                ext_direction,          # External direction
                aux_direction           # AUX direction
            )
            assert_pico_ok(self._status["setTrigDir"])
        
            print(f"Trigger directions set: Channel A = {channel_a}, Channel B = {channel_b}")
            return True
        
        except Exception as e:
            print(f"Error setting trigger directions: {e}")
            return False

    # TODO: Cleanup this function and abstract the c stuff away into private functions
    def collect_data_block(self):
        """
        Setup PicoScope data collection
        """
        try:
            max_samples = self.sampling_config['preTriggerSamples'] + self.sampling_config['postTriggerSamples']
            time_interval_ns = ctypes.c_float()
            returned_max_samples = ctypes.c_int16()

            self._status["GetTimebase"] = ps.ps3000aGetTimebase2(
                                self._chandle,                          # Device handle
                                self.sampling_config['timeBase'],       # Timebase setting (2 by default)
                                max_samples,                            # Requested number of samples
                                ctypes.byref(time_interval_ns),         # Returns actual time interval
                                1,                                      # Oversample (usually 1)
                                ctypes.byref(returned_max_samples),     # Returns max samples at this rate
                                0                                       # Segment index (0 for single segment)
                            )
            assert_pico_ok(self._status["GetTimebase"])

            max_samples = self.sampling_config['preTriggerSamples'] + self.sampling_config['postTriggerSamples']
            overflow = ctypes.c_int16()
            cmaxSamples = ctypes.c_int32(max_samples)

            self._status['runblock'] = ps.ps3000aRunBlock(self._chandle,
                                                          self.sampling_config['preTriggerSamples'],
                                                          self.sampling_config['postTriggerSamples'],
                                                          self.sampling_config['timeBase'],
                                                          1,
                                                          None,
                                                          0,
                                                          None,
                                                          None)
            assert_pico_ok(self._status["runblock"])

            bufferAMax = (ctypes.c_int16 * max_samples)()
            bufferAMin = (ctypes.c_int16 * max_samples)()
            channel = self.channel_to_bool(self.trigger_config['trigChannel'])

            self._status["SetDataBuffers"] = ps.ps3000aSetDataBuffers(self._chandle,
                                                                    channel,
                                                                    ctypes.byref(bufferAMax),
                                                                    ctypes.byref(bufferAMin),
                                                                    max_samples, 0, 0)
            assert_pico_ok(self._status["SetDataBuffers"])

            # Creates a overlow location for data
            overflow = (ctypes.c_int16 * 10)()
            
            # Creates converted types maxsamples
            cmaxSamples = ctypes.c_int32(max_samples)

            # Checks data collection to finish the capture
            ready = ctypes.c_int16(0)
            check = ctypes.c_int16(0)
            while ready.value == check.value:
                self._status["isReady"] = ps.ps3000aIsReady(self._chandle, ctypes.byref(ready))

            self._status["GetValues"] = ps.ps3000aGetValues(self._chandle,
                                                            0,
                                                            ctypes.byref(cmaxSamples),
                                                            0,
                                                            0,
                                                            0,
                                                            ctypes.byref(overflow))
            assert_pico_ok(self._status["GetValues"])

            # Converts ADC from channel A to mV
            adc2mVChAMax =  adc2mV(bufferAMax, self.channel_config[channel]['range'], self.sampling_config['maxADC'])

            # Creates the time data
            print(f'Sampling interval: {time_interval_ns.value} (ns)')
            print(f'samples: {cmaxSamples.value}')
            time = np.linspace(0, (cmaxSamples.value - 1) * time_interval_ns.value, cmaxSamples.value)

            return (time, adc2mVChAMax)

        except Exception as e:
            print(f"Error: {e}")
            return False

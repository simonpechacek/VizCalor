from labjack import ljm
import threading
import time
from functools import partial
import queue

class TemperatureMeas(threading.Thread):

    def __init__(self, channels:list[str]|int|tuple[int,int]|list[int], config:dict, temperature_q:queue.Queue) -> None:
        threading.Thread.__init__(self)
        
        if type(channels) == list:
            if len(channels) > 0:
                if type(channels[0]) == str:
                    # assumption is -> these are already the channels
                    self.channels = channels
                elif type(channels[0]) == int:
                    self.channels = [f"AIN{i}" for i in channels]
                else:
                    raise ValueError("Got Invalid list of channels, should be {str|int} -> got: ", type(channels[0]))
            else:
                raise ValueError("Got Empty List of Channels")
        elif type(channels) == tuple:
            if len(channels) != 2:
                raise ValueError("Got Channel Range should be (start, stop) -> got: ", channels)
            else:
                self.channels = [f"AIN{i}" for i in range(channels[0], channels[1])]
        elif type(channels) == int:
            self.channels = [f"AIN{i}" for i in range(channels)]
        else:
            raise ValueError("Invalid channels, should be {list[int]|list[str]|tuple[int, int]|int}, got: ", type(channels))
        #print("Channels to sample: ", self.channels)
        self.tool = ljm.openS("T7", "ANY", "ANY")
        info = ljm.getHandleInfo(self.tool)
        print(f"Opened LabJack with Device type: {info[0]}\nConnection type: {info[1]}\nSerial number: {info[2]}")
        # config should be dict:
        # for each "AIN0" : {"T_FUNC": [0, 1, 2] -> polynomial coeffs (voltage to temp conversion)}
        self.config = config
        self.config_channels()
        self.transfer_functions = {}
        # prepare transfer functions
        self.__init_transfer_functions()
        self._q = temperature_q
        self.end = threading.Event()
        self.daemon = True # when main thread exits -> this thread ends too
    
    def config_channels(self):
        # self channels are ["AIN0", "AIN5", "AIN4"] ...
        # -> configure them and the results are gonna be returned in this order (I think? TODO: Test it)
        settle_us_time = self.config["SETTLING_MS"] * 1000
        v_range = 10.0 # TODO: Read the needed range out of the assigned sensor config
        for channel in self.channels:
            # Set the range to 0-10.0V
            ljm.eWriteName(self.tool, f"{channel}_RANGE", v_range)
            # Set the resolution index
            ljm.eWriteName(self.tool, f"{channel}_RESOLUTION_INDEX", self.config["RESOLUTION"])
            # Set settling time
            ljm.eWriteName(self.tool, f"{channel}_SETTLING_US", settle_us_time)
    
    def __init_transfer_functions(self):
        for chan in self.channels:
            # try to find the calib/sensor file inside the config
            if chan in self.config["ain_channels"]:
                calib = self.config["ain_channels"][chan]["assigned_calibration"]
                coefs = self.config["calibrations"][calib]["T_FUNC"]
                self.transfer_functions[chan] = partial(self.__transfer_function, coeffs=coefs)
            else:
                raise ValueError(f"Missing Transfer Function for channel: {chan}")
            
    @staticmethod
    def __transfer_function(voltage, coeffs:None|list[float] = None):
        if coeffs is None:
            return -999.9
        # calculate the temperature -> coeffs from polyfit [1, 2, 3] = 1*x**2 + 2*x**1 + 3*x**0
        max_pow = len(coeffs) - 1
        temp = 0
        for i in range(len(coeffs)):
            temp += coeffs[i] * (voltage**(max_pow - i))
        return temp
    
    def __start_stream(self):
        addresses, _ = ljm.namesToAddresses(len(self.channels), self.channels)
        ljm.eStreamStart(self.tool, 1, len(self.channels), addresses, self.config["SCAN_FREQ"])
    
    def __led_init(self):
        gpio_pins = [0, 1, 2, 3]
        pin_states = [1, 1, 1, 1]
        for pin, state in zip(gpio_pins, pin_states):
            ljm.eWriteName(self.tool, f"DIO{pin}", state)
    
    def __blink_led(self, color, delay=0.1):
        pin = 1
        if color == "RED":
            pin = 2
        elif color == "BLUE":
            pin = 0
        elif color == "GREEN":
            pin = 3
        else: 
            return
        ljm.eWriteName(self.tool, f"DIO{pin}", 0)
        time.sleep(delay)
        ljm.eWriteName(self.tool, f"DIO{pin}", 1)
        
    def run(self):
        """
        Main loop of the thread. Gets called by .start() function 
        Arguments:   
            None  
        Returns:  
            None  
        """
        self.__start_stream()
        # prepare LED for blinking
        self.__led_init()
        
        while not self.end.is_set():
            try:
                ret = ljm.eStreamRead(self.tool)
                data = ret[0]  # First return is the data array
                
                temps = [self.transfer_functions[self.channels[i]](data[i]) for i in range(len(self.channels))]
                print(temps)
                self._q.put(temps)
                self.__blink_led("BLUE", 0.01)

            except Exception as read_error:
                print(f"Read error: {read_error}")
                break
        ljm.eStreamStop(self.tool)
        ljm.close(self.tool)
        
        
    def start(self):
        """
        Starts the thread. Calls .run() function  
        Arguments:  
            None  
        Returns:  
            None  
        """
        self.end.clear()
        super(TemperatureMeas, self).start()
    
    def stop(self):
        """
        Stops thread and should end any longer wainting functions (if they take the 'work' keyword arguments).  
        Arguments:  
            None  
        Returns:  
            None  
        """
        self.end.set()
        self.join()
    
if __name__ == "__main__":
    q = queue.Queue()
    config = {
        "SETTLING_MS": 10,
        "RESOLUTION": 8,
        "SCAN_FREQ": 1,
        "AIN0" : {"T_FUNC": [100, -50]},
        "AIN1" : {"T_FUNC": [100, -50]},
        "AIN2" : {"T_FUNC": [100, -50]},
    }
    t = TemperatureMeas(["AIN0", "AIN1", "AIN2"], config, q)
    print("start sampling")
    t.start()
    t.join()
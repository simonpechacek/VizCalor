import serial
import threading
import queue
from .parser import parse_temperatures

class SerialLoader(threading.Thread):
    bytesizes = {
        "FIVEBITS": serial.FIVEBITS,
        "SIXBITS": serial.SIXBITS,
        "SEVENBITS": serial.SEVENBITS,
        "EIGHTBITS": serial.EIGHTBITS
    }
    parities = {
        "NONE": serial.PARITY_NONE, 
        "EVEN": serial.PARITY_EVEN,
        "ODD": serial.PARITY_ODD, 
        "MARK": serial.PARITY_MARK,
        "SPACE": serial.PARITY_SPACE
    }
    stopbits = {
        "ONE": serial.STOPBITS_ONE, 
        "TWO": serial.STOPBITS_TWO, 
        "ONE_POINT_FIVE": serial.STOPBITS_ONE_POINT_FIVE
    }
    def __init__(self, serial_port:str, config:dict, result_q:queue.Queue):
        threading.Thread.__init__(self)
        self.port = serial.Serial(serial_port,
                                  baudrate=config.get("baudrate", 115200),
                                  bytesize=self.bytesizes[config.get("bytesize", "EIGHTBITS")],
                                  parity=self.parities[config.get("parity", "NONE")],
                                  stopbits=self.stopbits[config.get("stopbits", "ONE")],
                                  timeout=0.5)
        print("port initialised")
        self.result_q = result_q
        self.end = threading.Event()
        self.daemon = True
    
    def start(self):
        self.end.clear()
        super(SerialLoader, self).start()
    
    def stop(self):
        self.end.set()
        self.join()
        
    def run(self):
        
        #self.port.open()
        print("start")
        try:
            while not self.end.is_set():
                #print("try to read line")
                line = self.port.readline()
                if not line or len(line) < 1:
                    #print("timeout")
                    continue
                text = line.decode("utf-8").strip()
                temps = parse_temperatures(text, ",")
                print("Received: ", temps)
                self.result_q.put(temps)
                
        except Exception as e:
            print(e)
        finally:
            self.port.close()
        print("end")
            
        
if __name__ == "__main__":
    q = queue.Queue()
    config = {"baudrate": 9600}
    sl = SerialLoader("/dev/ttys084", config, q)
    sl.start()
    while True:
        inp = input("'q' to quit: ").strip().lower()
        if inp == 'q':
            break
    sl.stop()
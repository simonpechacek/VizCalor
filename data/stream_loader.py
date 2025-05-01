import os
import threading
import queue
from .parser import parse_temperatures
import select
import time

class StreamLoader(threading.Thread):
    def __init__(self, stream_file_path:str,  result_q:queue.Queue):
        threading.Thread.__init__(self)
        self.file_path = stream_file_path
        self.result_q = result_q
        self.end = threading.Event()
        self.daemon = True
    
    def run(self):
        print("start receive")
        try:
            fd = os.open(self.file_path, os.O_RDONLY | os.O_NONBLOCK)
            with os.fdopen(fd, 'r') as fifo:
                buffer = ''
                while not self.end.is_set():
                    rlist, _, _ = select.select([fifo], [], [], 0.5)
                    if rlist:
                        chunk = fifo.read(1)
                        if chunk == '':
                            # Writer disconnected
                            continue
                        if chunk == '\n':
                            if buffer != "":
                                #print("Received:", buffer)
                                self.result_q.put(parse_temperatures(buffer, ","))
                            buffer = ''
                        else:
                            buffer += chunk
        except Exception as e:
            print(f"FIFO error: {e}")
        print("End ")
        
    def start(self):
        self.end.clear()
        super(StreamLoader, self).start()
    
    def stop(self):
        # this should take at most 0.5 sec (timeout)
        self.end.set()
        self.join()
    

if __name__ == "__main__":
    q = queue.Queue()
    sl = StreamLoader("stream_test", q)
    sl.start()
        

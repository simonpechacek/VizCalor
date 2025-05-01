fifo_path = "stream_test"

with open(fifo_path, 'w') as fifo:
    fifo.write("23.5, 24.1, 25.0\n")
    fifo.write("22.0, 23.0, 24.0\n")

# These are loaders for all of the Data Sources in the GUI

The main principle is:

They are reading some time of data source and
they are putting data into gui queue for visualization

## Stream Loader

Reads FIFO file.

Create FIFO file:

```zsh
mkfifo stream_name
```

To test it you can start the reader and do: 


```zsh
echo "25.3,26.4,21.2\n" > stream_name
```

## Serial Loader

Reads Serial COM Port.

To Test you can do (on UNIX) (install socat if you dont have it):
```zsh
socat -d -d pty,raw,echo=0 pty,raw,echo=0
```

This creates two virtual COM ports that are linked together.
Use one to start the SerialLoader.

Use second to send data there:
```zsh
echo "26.5,27.2,28.0" > /dev/ttys091
```


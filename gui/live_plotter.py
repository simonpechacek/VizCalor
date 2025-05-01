import matplotlib.pyplot as plt
import numpy as np
import queue
class RingBuffer(object):
    """
    Ring buffer used by LivePlotter.  
    Not a great implementation with limited functionality.  
    I do not recommend on using in for anything other then the LivePlotter  
    """
    def __init__(self, size):
        """
        Initialize ring buffer  
        Arguments:   
            - size: size of ring buffer  
        """
        self.size = size
        self.buff = [None] * size
        self.first = 0
        self.oldest = -1
    
    def put(self, item):
        """
        Puts item into ring buffer, if the buffer is full overwrites the oldest value.  
        Arguments:  
            - item: can be basically anything  
        Returns:  
            None  
        """
        # After whole round -> the ring buffer is being overwritten
        if self.first == self.oldest:
            self.oldest += 1
        self.buff[self.first] = item
        self.first = (self.first + 1) % self.size 
        # first put
        if self.oldest == -1:
            self.oldest = 0
    
    def get_all(self):
        """
        Gets all elemts in a buffer (!does not empty it - all data stays)  
        Arguments:  
            None  
        Returns:  
            - buffer: array of all elements in a buffer  
        """
        if self.first == self.oldest:
            return self.buff[self.oldest:] + self.buff[:self.first] # when first < oldest -> whole buffer is full return it in correct order
        else:
            return self.buff[:self.first]
        
class FastRingBuffer:
    def __init__(self, size, num_channels):
        self.size = size
        self.num_channels = num_channels
        self.times = np.full(size, np.nan)  # 1D array for times
        self.temps = np.full((size, num_channels), np.nan)  # 2D array for temperatures
        self.index = 0
        self.full = False

    def put(self, t, temps):
        self.times[self.index] = t
        self.temps[self.index] = temps
        self.index = (self.index + 1) % self.size
        if self.index == 0:
            self.full = True

    def get_all(self):
        if self.full:
            times = np.concatenate((self.times[self.index:], self.times[:self.index]))
            temps = np.vstack((self.temps[self.index:], self.temps[:self.index]))
        else:
            times = self.times[:self.index]
            temps = self.temps[:self.index]
        return times, temps
    

class LivePlotter(object):
    """
    Used for Live plotting data during long running tests.  
    Can be configured to plot into multiple axes.  
    Uses data sampled by sample_function. Sample function has to q.put(row) into LivePlotter.q.  
    See 'live_plot_example.py' for more info on usage.  
    The 'update' function !MUST! be called from main thread.  
    """
    def __init__(self, fig, canvas, labels):
        """
        Initializes LivePlotter. Crates axes in the shape of plot_data_columns. See more in 'live_plot_example.py' or 'plotting_example.py'.  
        Arguments:  
            - n_samples: how many samples to plot back in time  
            - plot_data_columns: Specifies what data has to be plotted into which axes  
            - data_header: should be tuple or list corresponding to each entry in the sampled data - gets used for labeling x and y axis  
        """
        # dont use too big n_samples as this is not exactly optimized -> since optimizing it would add more logic to sample_function wich is alreade pretty involved
        #self.__ring = RingBuffer(200)
        self.__ring = FastRingBuffer(100, len(labels))
        self.figure = fig
        self.canvas = canvas
        self.labels = labels
        self.ax = None
        self.t = 0
        self._init_plots()
    
    
    def _init_plots(self):
        self.ax = self.figure.add_subplot(111)
        self.figure.patch.set_facecolor('#1e1e1e')
        self.ax.set_facecolor('#1e1e1e')
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.set_xlabel('Time (s)', color='white')
        self.ax.set_ylabel('Temperature (°C)', color='white')
        self.ax.grid(True, color='white')
        self.lines = []
        
    def update(self, temperatures):
        """
        Redraws plots. !Has to be called from main thread!  
        Arguments:  
            None  
        Returns:  
            None  
        """
        self.__ring.put(self.t, np.copy(temperatures))
        self.t += 1
        t, temps = self.__ring.get_all()
        if len(t) < 1:
            return
        """
        t = [d[0] for d in data]
        temps = data[0][1].reshape(1, -1)
        for i in range(1, len(data)):
            temps = np.vstack((temps,data[i][1].reshape(1, -1)))
        """
        colors = ['#ff6f61', '#6b5b95', '#88b04b', '#f7cac9', '#92a8d1', '#955251', '#b565a7', '#009b77']
        self.ax.clear()
        for i in range(temps.shape[1]): # shape 1 -> number of temperatures
            self.ax.plot(t, temps[:, i], label=self.labels[i], color=colors[i% len(colors)])
        
        self.ax.grid(True, color='white')
        self.ax.legend(
            loc='upper center',      # Put it above the plot
            bbox_to_anchor=(0.5, 1.15),  # Centered horizontally above
            ncol=(temps.shape[1]+1)//2,  # As many columns as sensors
            facecolor='#1e1e1e',     # Match background
            edgecolor='white',
            labelcolor='white',
            frameon=False            # No box around legend (optional, cleaner)
        )
        self.canvas.draw()
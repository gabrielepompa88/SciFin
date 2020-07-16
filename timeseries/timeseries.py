# Created on 2020/7/15

# Packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# CLASS timeseries
class timeseries:
    """
    Class defining a time series and its methods.
    """
    
    def __init__(self, df):
        """
        Initializer. Function that receives a data frame as an argument and initialize the time series class.
        """
        # Making sure it is a single column data frame
        assert(df.shape[1]==1)
        # Extract values
        self.data = df
        self.start = df.index[0]
        self.end = df.index[-1]
        self.nvalues = df.shape[0]
    
    
    ### PLOTTING INFORMATION ABOUT THE TIME SERIES ###
    
    def simple_plot(self, figsize=(12,5), dpi=100):
        """
        Simple method to plot the time series.

        Arguments:
        - figsize: size of the figure as tuple of 2 integers.
        - dpi: dots-per-inch definition of the figure.
        """
        plt.figure(figsize=figsize, dpi=dpi)
        plt.plot(self.data.index, self.data.value, color='k')
        title = "Time series from " + str(self.start)[:10] + " to " + str(self.end)[:10]
        plt.gca().set(title=title, xlabel="Date", ylabel="Value")
        plt.show()
    
    
    def distribution(self, start=None, end=None, bins=20, figsize=(8,4), dpi=100):
        """
        Method that plots the distribution of values between two dates.
        """
        
        # Preparing data frame
        if start==None and end==None:
            data = self.data
        elif start==None and end!=None:
            data = self.data[:end]
        elif start!=None and end==None:
            data = self.data[start:]
        elif start!=None and end!=None:
            data = self.data[start:end]
            
        # Plotting its distribution of values
        plt.figure(figsize=figsize, dpi=dpi)
        data.hist(bins=bins)
        if start==None:
            s = str(self.start)[:10]
        else:
            s = start
        if end==None:
            e = str(self.end)[:10]
        else:
            e = end
        title = "Distribution of values between " + s + " and " + e
        plt.gca().set(title=title, xlabel="Value", ylabel="Hits")
        plt.show()
        
    
    
    ### SIMPLE DATA EXTRACTION ON THE TIME SERIES ###
    
    def hist_avg(self, start=None, end=None):
        """
        Method that returns the historical average of the time series between two dates.
        Default is for the whole series.
        """
        if start==None and end==None:
            avg = self.data.values.mean()
        elif start==None and end!=None:
            avg = self.data[:end].values.mean()
        elif start!=None and end==None:
            avg = self.data[start:].values.mean()
        elif start!=None and end!=None:
            avg = self.data[start:end].values.mean()
        return avg
    
    
    def hist_std(self, start=None, end=None):
        """
        Method that returns the historical standard deviation of the time series between two dates.
        Default is for the whole series.
        """
        if start==None and end==None:
            std = self.data.values.std()
        elif start==None and end!=None:
            std = self.data[:end].values.std()
        elif start!=None and end==None:
            std = self.data[start:].values.std()
        elif start!=None and end!=None:
            std = self.data[start:end].values.std()
        return std
    
    
    def min(self, start=None, end=None):
        """
        Method that returns the minimum of the series.
        """
        if start==None and end==None:
            ts_min = self.data.values.min()
        elif start==None and end!=None:
            ts_min = self.data[:end].values.min()
        elif start!=None and end==None:
            ts_min = self.data[start:].values.min()
        elif start!=None and end!=None:
            ts_min = self.data[start:end].values.min()
        return ts_min
    
    
    def max(self, start=None, end=None):
        """
        Method that returns the maximum of the series.
        """
        if start==None and end==None:
            ts_max = self.data.values.max()
        elif start==None and end!=None:
            ts_max = self.data[:end].values.max()
        elif start!=None and end==None:
            ts_max = self.data[start:].values.max()
        elif start!=None and end!=None:
            ts_max = self.data[start:end].values.max()
        return ts_max
    
    
    
    ### AUTOCORRELATION COMPUTATION ###
    
    def autocorrelation(self, lag=1, start=None, end=None):
        """
        Method returning the autocorrelation of the time series for a specified lag.
        We use the function $\rho_l = \frac{Cov(x_t, x_{t-l})}{\sqrt(Var[x_t] Var[x_{t-l}])} where $x_t$ is the time series at time t. Cov denotes the covariance and Var the variance. We also use the properties $\rho_0 = 1$ and $\rho_{-l} = \rho_l$ (choosing LaTeX notations here).
        """
        l = abs(lag)
        
        # Trivial case
        if l==0:
            return 1
        
        # Preparing data frame
        if start==None and end==None:
            data = self.data
        elif start==None and end!=None:
            data = self.data[:end]
        elif start!=None and end==None:
            data = self.data[start:]
        elif start!=None and end!=None:
            data = self.data[start:end]
        
        # General case
        assert(l < data.shape[0])
        Numerator = np.mean((data - data.mean()) * (data.shift(l) - data.shift(l).mean()))
        Denominator = data.std() * data.shift(l).std()
        return Numerator / Denominator
    
    
    def plot_autocorrelation(self, lag_min=0, lag_max=25, start=None, end=None, figsize=(8,4), dpi=100):
        """
        Method making use of the autocorrelation method in order to return a plot of the autocorrelation againts the lag values.
        """
        
        assert(lag_max>lag_min)
        x_range = list(range(lag_min, lag_max+1, 1))
        ac = [self.autocorrelation(lag=x, start=start, end=end) for x in x_range]
        
        # Plotting
        plt.figure(figsize=figsize, dpi=dpi)
        plt.bar(x_range, ac, color='k')
        if start==None:
            s = str(self.start)[:10]
        else:
            s = start
        if end==None:
            e = str(self.end)[:10]
        else:
            e = end
        title = "Autocorrelation from " + s + " to " + e + " for lags = [" + str(lag_min) + "," + str(lag_max) + "]"
        plt.gca().set(title=title, xlabel="Lag", ylabel="Autocorrelation Value")
        plt.show()
        
    
    
    ### SIMPLE TRANSFORMATIONS OF THE TIME SERIES TO CREATE A NEW TIME SERIES ###
    
    def trim(self, new_start, new_end):
        """
        Method that trims the time series to the desired dates and send back a new time series.
        """
        new_df = self.data[new_start:new_end]
        new_ts = timeseries(new_df)
        return new_ts
    
    
    def add_cst(self, cst=0):
        """
        Method that adds a constant to the time series.
        """
        new_df = self.data + cst
        new_ts = timeseries(new_df)
        return new_ts
    
    
    def mult_by_cst(self, cst=1):
        """
        Method that multiplies the time series by a constant.
        """
        new_df = self.data * cst
        new_ts = timeseries(new_df)
        return new_ts
    
    
    def linear_combination(self, other_timeseries, factor1=1, factor2=1):
        """
        Method that adds a timeseries to the current one according to linear combination: factor1 * current_ts + factor2 * other_timeseries.
        """
        new_df = factor1 * self.data + factor2 * other_timeseries.data
        new_ts = timeseries(new_df)
        return new_ts
    
    
    
    ### Fitting methods ###
    
    def rolling_avg(self, pts=1):
        """
        Method that transforms the time series into a rolling window average time series.
        """
        new_values = [self.data[x-pts+1:x].mean() for x in range(pts-1, self.nvalues, 1)]
        new_df = pd.DataFrame(index=self.data.index[pts-1:self.nvalues], data=new_values)
        new_ts = timeseries(new_df)
        return new_ts
    
    
    
    
    


def multi_plot(timeseries, figsize=(12,5), dpi=100):
    """
    Function that plots multiple time series together.
    """
    
    plt.figure(figsize=figsize, dpi=dpi)
    for i in range(len(timeseries)):
        plt.plot(timeseries[i].data.index, timeseries[i].data.values)
    plt.plot()
        
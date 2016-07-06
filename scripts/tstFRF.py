# -*- coding: utf-8 -*-
"""
Created on Sun Jan 31 15:48:03 2016

@author: jcugnoni
"""
import wave,scipy,math,os,time,sys
from scipy import *
from matplotlib.pylab import *



def smooth(x,window_len=11,window='hanning'):
    """smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x: the input signal 
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal
        
    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)
    
    see also: 
    
    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter
 
    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """ 
     
    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."
        

    if window_len<3:
        return x
    
    
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
    

    s=scipy.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=scipy.ones(window_len,'d')
    else:
        w=eval('scipy.'+window+'(window_len)')
    
    y=scipy.convolve(w/w.sum(),s,mode='same')
    return y    

def running_mean(x, N):
    cumsum = scipy.cumsum(scipy.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / N 

wav_sweep='../wav/Sweep-32000-16-M-8.0s.wav'
wav_capture='fenderRocPro700-capedge-10cm.wav'

#f=wave.open(wav_sweep,'rb')
#len1=f.getnframes()
#nc1=f.getnchannels()
#bp1=f.getsampwidth()
#data=f.readframes(len1/nc1)
#f.close()
#Y1=scipy.float32(scipy.fromstring(data,dtype='int16'))
#f=wave.open(wav_capture,'rb')
#len2=f.getnframes()
#nc2=f.getnchannels()
#bp2=f.getsampwidth()
#data=f.readframes(len2)
#f.close()
#extract data of 1st channel    
#Y2=scipy.float32(scipy.fromstring(data,dtype='int16'))
#Y2=Y2[0:2:len2-1]

[fs1,data1]=scipy.io.wavfile.read(wav_sweep)
[fs2,data2]=scipy.io.wavfile.read(wav_capture)
len1=len(data1)
len2=len(data2)

# pad and normalize wave file 
#(or we could pad the shortest to the longest... TODO!)
minlen = min([len1,len2])
maxlen = max([len1,len2])
tdata1=scipy.zeros(maxlen)
tdata2=scipy.zeros(maxlen)
tdata1[0:len1]=data1 #/max(abs(data1))
tdata2[0:len2]=data2[:,0] #/max(abs(data2[:,0]))
# acquisition time lag compensation
thr1=max(abs(tdata1)*0.3)
offset1=max(max(scipy.where(abs(tdata1)>thr1)))
thr2=max(abs(tdata2)*0.3)
offset2=max(max(scipy.where(abs(tdata2)>thr2)))
valid_len=min(offset1,offset2)
tstart1=offset1-valid_len
tstart2=offset2-valid_len
tdata1o=tdata1[tstart1:tstart1+valid_len]
tdata2o=tdata2[tstart2:tstart2+valid_len]
s1=scipy.fft(tdata1o)
s2=scipy.fft(tdata2o)
frf=s2/s1
#smoothing of magnitude but not phase
mag=scipy.absolute(frf)
phase=scipy.angle(frf)
mags=scipy.signal.savgol_filter(mag,201,2,mode='nearest')
frfs=mags*scipy.exp(scipy.sqrt(-1)*phase)
#build IR




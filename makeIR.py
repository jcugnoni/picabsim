# -*- coding: utf-8 -*-
"""
Module for capturing impulse response

Requires a Jackd server, ecasound utility and scipy

Created on Sat Jan  9 16:19:22 2016

@author: jcugnoni
"""
import scipy
import wave
import os,time
from struct import pack


def makeIR(wav_in,wav_out,fs,duration,noise=0.025):
    """ measures the response of a speaker (+amp+mic) and build an IR """
    # step 1: full duplex playback and recording. Input: provided sweep wav file
    # output: recorded time response
    ecasound_cmd="ecasound -f:16,1,%i -a:1 -i jack,system,capture " + \
    " -o /tmp/capture.wav -a:2 -i %s -o jack,system -t %i"
    ecasound_cmd=ecasound_cmd%(int(fs),wav_in,int(duration))
    # run capture    
    os.system(ecasound_cmd)
    # load input and capture wave files 
    time.sleep(3)
    f=wave.open(wav_in,'rb')
    len1=f.getnframes()
    #nc1=f.getnchannels()
    #bp1=f.getsampwidth()
    data=f.readframes(len1)
    f.close()
    Y1=scipy.float32(scipy.fromstring(data,dtype='int16'))
    f=wave.open('/tmp/capture.wav','rb')
    len2=f.getnframes()
    #nc1=f.getnchannels()
    #bp1=f.getsampwidth()
    data=f.readframes(len2)
    f.close()    
    Y2=scipy.float32(scipy.fromstring(data,dtype='int16'))
    # truncate and normalize wave file 
    #(or we could pad the shortest to the longest... TODO!)
    minlen = min([len1,len2])
    Y2=Y2[0:minlen]
    Y2=Y2/max(abs(Y2))
    Y1=Y1[0:minlen]
    Y1=Y1/max(abs(Y1))
    # compute frequency response function as ration of both spectra
    FRF=scipy.fft(Y2)/scipy.fft(Y1)
    # compute impulse response as inverse FFT of FRF
    IRraw=scipy.real(scipy.ifft(FRF))
    # get rid of initial lag in IR
    thr=max(abs(IRraw))*noise
    offset=max([0 , min(min(scipy.where(abs(IRraw)>thr)))-5 ])
    IR=IRraw[offset:-1] 
    IRnorm=IR/max(abs(IR))
    # TODO: add post pro options such as low/high pass and decay
    # write output IR
    f = wave.open(wav_out, 'w')
    f.setparams((1, 2, fs, 0, 'NONE', 'not compressed'))
    maxVol=2**15-1.0 #maximum amplitude
    wvData=""
    for i in range(len(IRnorm)):
        wvData+=pack('h', maxVol*IRnorm[i])
    f.writeframes(wvData)
    f.close()
    

def testTone(fs,freq,duration):
    """ measures the response of a speaker (+amp+mic) and build an IR """
    # step 1: full duplex playback and recording. Input: provided sweep wav file
    # output: recorded time response
    ecasound_cmd="ecasound -f:16,1,%i -a:1 -i tone,%i,%i -o jack,system -t %i &"
    ecasound_cmd=ecasound_cmd%(int(fs),int(freq),int(duration),int(duration))
    # run test tone in bkgnd    
    os.system(ecasound_cmd) 
    
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import numpy as np
from numpy import log10, pi, convolve, mean
from scipy.signal.filter_design import bilinear
from scipy.signal import lfilter
from scikits.audiolab import Sndfile, Format

def A_weighting(Fs):
    """Design of an A-weighting filter.
    
    [B,A] = A_weighting(Fs) designs a digital A-weighting filter for 
    sampling frequency Fs. Usage: Y = FILTER(B,A,X). 
    Warning: Fs should normally be higher than 20 kHz. For example, 
    Fs = 48000 yields a class 1-compliant filter.
    
    Originally a MATLAB script. Also included ASPEC, CDSGN, CSPEC.
    
    Author: Christophe Couvreur, Faculte Polytechnique de Mons (Belgium)
            couvreur@thor.fpms.ac.be
    Last modification: Aug. 20, 1997, 10:00am.
    
    Translated from adsgn.m to PyLab 2009-07-14 endolith@gmail.com
    
    References: 
       [1] IEC/CD 1672: Electroacoustics-Sound Level Meters, Nov. 1996.
    
    """
    # Definition of analog A-weighting filter according to IEC/CD 1672.
    f1 = 20.598997
    f2 = 107.65265
    f3 = 737.86223
    f4 = 12194.217
    A1000 = 1.9997
    
    NUMs = [(2 * pi * f4)**2 * (10**(A1000/20)), 0, 0, 0, 0]
    DENs = convolve([1, +4 * pi * f4, (2 * pi * f4)**2], 
                    [1, +4 * pi * f1, (2 * pi * f1)**2], mode='full')
    DENs = convolve(convolve(DENs, [1, 2 * pi * f3], mode='full'), 
                                   [1, 2 * pi * f2], mode='full')
    
    # Use the bilinear transformation to get the digital filter.
    # (Octave, MATLAB, and PyLab disagree about Fs vs 1/Fs)
    return bilinear(NUMs, DENs, Fs)

# From matplotlib.mlab
def rms_flat(a):
    """
    Return the root mean square of all the elements of *a*, flattened out.
    """
    return np.sqrt(np.mean(np.absolute(a)**2))

def rms(signal):
    """Return the RMS level of the signal after removing any DC offset"""
    return rms_flat(signal - mean(signal))

def dB(level):
     """Return a level in decibels.
     
     Decibels are relative to the RMS level of a full-scale square wave (dBFS).

     """
     return 20 * log10(level)

def A_weight(signal, samplerate):
    """Return the given signal after passing through an A-weighting filter"""
    B, A = A_weighting(samplerate)
    print np.shape(signal)
    return lfilter(B, A, signal)

def display(header, results):
    """Display header string and list of result lines"""
    try:
        import easygui
    except ImportError:
        # Print the stuff
        # Message about easygui not installed?
        print header
        print '-----------------'
        print '\n'.join(results)
    else:
        # Pop the stuff up in a text box
        easygui.textbox(header, title, '\n'.join(results))

def analyze(filename):
    f = Sndfile(filename, 'r')
    signal = f.read_frames(f.nframes)
    print np.shape(signal)

    # If 2 channels, check if they are identical.
    # If they are identical, treat it as 1 channel
    # if 1 channel, show just the info for one side
    # If two channels, show left first then right
    # If multiple channels, show in series as numbers (dont worry about this for now)

    header = 'dB values are relative to a full-scale square wave'
    title = 'Waveform properties'

    results = [
    'Properties for "' + filename + '"',
    str(f.format),
    'Channels: %d' % f.channels]
    
    if f.channels == 2:
        if np.array_equal(signal[:,0],signal[:,1]):
            results[-1] += ' (L and R are identical)'

    results += [
    'Sampling rate: %d Hz' % f.samplerate,
    'Frames: %d' % f.nframes,
    'Length: ' + str(f.nframes/f.samplerate) + ' seconds',
    '-----------------',
    ]
    
    for channel in signal.transpose(): #problem
        signal_level = rms(channel)
        peak_level = max(max(channel.flat),-min(channel.flat))
        crest_factor = peak_level/signal_level

        # Apply the A-weighting filter to the signal
        weighted = A_weight(channel, f.samplerate)
        weighted_level = rms(weighted)
        
        results += [
        'DC offset: %f (%.3f%%)' % (mean(channel), mean(channel)*100),
        'Crest factor: %.3f (%.3f dB)' % (crest_factor, dB(crest_factor)),
        'Peak level: %.3f (%.3f dB)' % (peak_level, dB(peak_level)), # Does not take intersample peaks into account!
        'RMS level: %.3f (%.3f dB)' % (signal_level, dB(signal_level)),
        'A-weighted: %.3f (%.3f dB)' % (weighted_level, dB(weighted_level)),
        'A-difference: %.3f dB' % dB(weighted_level/signal_level),
        '-----------------',
        ]

        
        # Could also make a list of property names and their values and format it into a string later?  Still need to consider float formatting, etc. though
    
    display(header, results)
    


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        analyze(filename)
    else:
        print 'needs a filename'

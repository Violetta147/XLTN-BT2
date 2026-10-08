# SPDX-License-Identifier: GPL-3.0-or-later
# Adapted from Thomas Drugman's COVAREP pitch_srh.m and lpcresidual.m.
# Original copyright (c) 2011 University of Mons, FNRS.
from math import gcd
import numpy as np
from scipy.linalg import solve_toeplitz
from scipy.signal import lfilter, resample_poly


def matlab_round(value):
    return np.floor(np.asarray(value)+.5).astype(int)


def residual(audio,fs):
    length=int(matlab_round(.025*fs));shift=int(matlab_round(.005*fs));order=int(matlab_round(.75*fs/1000))
    result=np.zeros(len(audio));window=np.hanning(length+1)
    starts=np.arange(0,len(audio)-length-1,shift)
    coefficients=[];energies=[]
    for start in starts:
        segment=audio[start:start+length+1]*window
        correlation=np.array([np.dot(segment[:len(segment)-lag],segment[lag:]) for lag in range(order+1)])
        if correlation[0]>0:
            a=np.r_[1.,solve_toeplitz(correlation[:-1],-correlation[1:])]
        else:a=np.r_[1.,np.zeros(order)]
        inverse=lfilter(a,1,segment)
        energy=np.dot(inverse,inverse)
        if energy>0:inverse*=np.sqrt(np.dot(segment,segment)/energy)
        result[start:start+length+1]+=inverse
        coefficients.append(a);energies.append((float(correlation[0]),float(energy)))
    maximum=np.max(abs(result)) if len(result) else 0.
    if maximum>0:result/=maximum
    assert np.isfinite(result).all() and np.isfinite(coefficients).all()
    return result,dict(lp_starts=starts,lp_coefficients=np.array(coefficients),lp_energies=np.array(energies),
                       lp_length=length,lp_shift=shift,lp_order=order)


def harmonic_scores(spectrum,lower,upper):
    frequencies=np.arange(lower,upper+1)
    plus=np.arange(1,6)[:,None]*frequencies[None,:]
    minus=matlab_round(np.arange(1.5,5.,1.)[:,None]*frequencies[None,:])
    plus=(plus-1)%spectrum.shape[1];minus=(minus-1)%spectrum.shape[1]
    curves=np.zeros((len(spectrum),upper))
    curves[:,frequencies-1]=np.sum(spectrum[:,plus],axis=1)-np.sum(spectrum[:,minus],axis=1)
    indices=np.argmax(curves,axis=1)
    return indices+1,curves[np.arange(len(curves)),indices],curves


def analyze(audio,fs,window_ms):
    assert len(audio)/fs>=.1 and np.isfinite(audio).all()
    if fs>16000:
        divisor=gcd(int(fs),16000)
        audio=resample_poly(audio,16000//divisor,int(fs)//divisor)
        fs=16000
    filtered,proof=residual(audio,fs)
    length=int(matlab_round(window_ms/1000*fs))-2
    length=int(matlab_round(length/2))*2
    half=length//2;shift=int(matlab_round(.01*fs))
    positions=np.arange(half+1,len(audio)-half+1,shift)
    starts=positions-half-1
    frames=np.array([filtered[start:start+length] for start in starts])*np.blackman(length)
    frames-=np.mean(frames,axis=1,keepdims=True)
    assert fs>=8000
    full_spectrum=abs(np.fft.rfft(frames,n=fs,axis=1))[:,:fs//2]
    norms=np.linalg.norm(full_spectrum,axis=1)
    spectrum=full_spectrum[:,:2000]/np.maximum(norms[:,None],1e-20)
    lower,upper=70,400;no_adjustment=True;passes=[]
    for iteration in range(2):
        raw,score,curves=harmonic_scores(spectrum,lower,upper)
        passes.append((lower,upper))
        if np.max(score)>.1:
            median=np.median(raw[score>.1])
            if int(matlab_round(.5*median))>lower:
                lower=int(matlab_round(.5*median));no_adjustment=False
            if int(matlab_round(2*median))<upper:
                upper=int(matlab_round(2*median));no_adjustment=False
        if no_adjustment:break
    threshold=.085 if np.std(score,ddof=1)>.05 else .07
    voiced=score>threshold
    proof.update(resampled_audio=audio,residual=filtered,spectrum=spectrum,spectrum_norm=norms,
                 native_times=positions/fs,native_positions=positions,native_starts=starts,
                 frame_samples=length,native_fs=fs,raw_f0=raw,score=score,native_pred=voiced,
                 passes=np.array(passes),threshold=threshold,curves=curves)
    return proof

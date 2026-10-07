import numpy as np


def independent_features(audio, fs):
    length, hop = round(fs*.025), round(fs*.01)
    nfft = 1 << (length-1).bit_length()
    frequency = np.arange(nfft) * fs/nfft
    frequency = np.minimum(frequency, fs-frequency)
    mel_points = 700 * (np.power(10, np.linspace(2595*np.log10(1+70/700),2595*np.log10(1+min(8000,fs/2)/700),28)/2595)-1)
    filters = np.array([np.maximum(0,np.minimum((frequency-mel_points[i])/(mel_points[i+1]-mel_points[i]),
                                                (mel_points[i+2]-frequency)/(mel_points[i+2]-mel_points[i+1]))) for i in range(26)])
    cosine = np.sqrt(2/26)*np.cos(np.pi/26*(np.arange(26)+.5)[None,:]*np.arange(1,14)[:,None])
    rows, pitches, rms = [], [], []
    lo, hi = int(np.ceil(fs/400)), min(length-2,int(np.floor(fs/70)))
    for start in range(0, len(audio)-length+1, hop):
        x = audio[start:start+length].copy()
        x -= x.mean()
        rms.append(np.sqrt(np.dot(x,x)/len(x)))
        spectrum = abs(np.fft.fft(x*np.hanning(length),nfft))**2
        spectrum[0] = 0
        total = max(spectrum.sum(),1e-20)
        high = spectrum[frequency >= 1000-1e-8].sum()/total
        cepstrum = cosine @ np.log(np.maximum(filters @ (spectrum/total),1e-12))
        correlation = np.array([np.dot(x[:-lag],x[lag:])/max(np.linalg.norm(x[:-lag])*np.linalg.norm(x[lag:]),1e-20)
                                for lag in range(lo-1,hi+2)])
        candidates = [i for i in range(1,len(correlation)-1) if correlation[i] >= correlation[i-1] and correlation[i] >= correlation[i+1]]
        if candidates and max(correlation[i] for i in candidates)>0:
            strength = max(correlation[i] for i in candidates)
            k = next(i for i in candidates if correlation[i]>=.93*strength)
            a,b,c = correlation[k-1:k+2]
            delta = .5*(a-c)/(a-2*b+c) if abs(a-2*b+c)>1e-12 else 0
            pitch = np.clip(fs/(lo-1+k+np.clip(delta,-.5,.5)),70,400) if strength>0 else np.nan
            strength = max(strength,0)
        else:
            strength,pitch = 0,np.nan
        rows.append([strength,0.,sum(bool(a<0)!=bool(b<0) for a,b in zip(x[:-1],x[1:]))/(length-1)*fs,high,*cepstrum])
        pitches.append(pitch)
    rows = np.array(rows)
    rows[:,1] = np.log(np.maximum(np.array(rms)/max(np.quantile(rms,.95),1e-12),1e-6))
    return rows,np.array(pitches)


def independent_score(item,pred,f0):
    values=f0[np.isfinite(f0)]
    estimates=dict(F0mean=np.mean(values),F0std=np.std(values),F0num=len(values))
    errors={key+'_mape':100*abs(value-item['stats'][key])/item['stats'][key] for key,value in estimates.items()}
    lab=item['labels']; valid=np.isin(lab,['v','uv']); y=lab[valid]=='v'; p=pred[valid]
    tp,tn,fp,fn=sum(y&p),sum(~y&~p),sum(~y&p),sum(y&~p)
    rv,ru=tp/max(tp+fn,1),tn/max(tn+fp,1)
    return dict(**estimates,**errors,average_mape=np.mean(list(errors.values())),TP=tp,TN=tn,FP=fp,FN=fn,
                recall_v=rv,recall_uv=ru,balanced_accuracy=(rv+ru)/2,
                macro_f1=(2*tp/max(2*tp+fp+fn,1)+2*tn/max(2*tn+fp+fn,1))/2,false_voiced_sil=sum((lab=='sil')&pred))

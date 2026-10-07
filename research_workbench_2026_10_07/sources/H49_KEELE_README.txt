







Keele Pitch Database







  Keele Pitch Database - README 
  
SPEECH data


The Keele pitch database is stored in the SAM
  format: Each dataset consists of a binary file, containing the speech data and
  an ASCII text file that contains a description of the data. In our case there
  are two descriptions and two data files, the speech and laryngograph data..






We have collected data for ten speakers, each of
  them read a phonetically balanced text, the north-wind story.





   
  
Here are the file descriptions
 







*.pet: the text transcription 




which we segmented very coarsly, you'll
      find a bunch of labels at the top of the file, which contain details in
      SAM format. The relevant information is:










SRC: f1nw0000.pes  - i.e.
      the transcription is based on the source (SRC) of the first female (f1)
      reading the north wind story (nw), and there on the speech data (pes).






SAM: the sampling rate (20kHz)






BEG: 0 (data starts at sample
      0)






END: 644200 (there are 644k
      samples)








*.pes: this is the speech data file 




The data is sampled at 20kHz, using 16 bit
      signed integers, the byte order is for Intel processors, if you use a Sun
      workstation you'll have to swap bytes. If you have a PC and use something
      like sox or CoolEdit, you should be able to read and play back the data directly.








*.pel: is the laryngograph (lx) signal. 




We partially corrected for the acoustic
      delay between the lx signal and the signal picked up by the microphone,
      but this correction is not perfect since it depends on the vocal
      tract shape. The data format is the same as for the speech signal.








*.pev is a manually checked pitch track. 




The pitch estimates were computed from the
      autocorrelation of the lx signal using a 26.5ms window. This file is
      sampled at 100Hz (i.e. 10 ms time steps between pitch estimates). The only
      peculiarities of this file are that










it is stored in ascii format, and


that the 'pitch estimates' are given as
        the peak position of the ACF peak in samples, you will have to convert
        this into Hz if you want to use it (Fs=20kHz).


where there is no lx signal the data is
        set to 0 (read this as unvoiced)


where we know that there is voiced speech,
        but the lx trace has been corrupted the data is set to -1 (this happens sometimes
        because the measurements are based on two electrodes on the skin, which
        can loose contact as the speakers move around).


for segments where there is a lx trace,
        but no obvious speech signal, we left the values but set them to negative
        values. So a -200 entry means that a 100Hz F0 was measured but that this
        is not reflected in the speech data.








The pitch estimates in the *.pev file are
based on 10 ms steps and 25.6 ms 
ACF windows.
If you use different parameters in your own pitch tracker, the values should not
be used as a ground truth for comparisons, it would be more appropriate to
re-estimate the pitch from the lx signal with parameters that match those of
your pitch tracker. 



   



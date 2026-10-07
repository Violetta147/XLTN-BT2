form ExtractF0
    sentence input_file input.wav
    positive silence_threshold 0.09
endform

Read from file: input_file$
To Pitch (filtered autocorrelation): 0.01, 70, 800, 15, "no", 0.03, silence_threshold, 0.30, 0.055, 0.35, 0.14

writeInfoLine: "# Praat ", praatVersion$
appendInfoLine: "time_s,f0_hz"
count = Get number of frames
for index from 1 to count
    time = Get time from frame number: index
    frequency = Get value in frame: index, "Hertz"
    if frequency = undefined
        frequency = 0
    endif
    appendInfoLine: fixed$ (time, 15), ",", fixed$ (frequency, 15)
endfor

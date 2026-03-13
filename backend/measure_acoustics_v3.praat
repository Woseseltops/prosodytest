#########################################  PRAAT SCRIPT FOR EXTRACTING ACOUSTIC FEATURES FROM AUDIO FILES ##########################
#
# Project: Prosody Proficiency Test Battery (PPTB)
# Script: measure_acoustics_v3.praat
# Date: 10/02/2026
# last update: 05/03/2026
# Author: Ronny Bujok
# Email: ronny.bujok@ru.nl
#
########################################################### Description ############################################################
#
# This script reads a recording (short sentence) and its corresponding TextGrid file,
# and extracts various (acoustic) features related to prosody. It can be run as a standalone script or
# called from a Python Script. The prosodic features are the following:  
#
# GENERAL FEATURES:
# - intensity:              mean intensity of the audio (dB)
# - duration:               duration of the audio (seconds)
# - meanF0:                 mean F0 of the audio (Hz)
# - sdF0:                   standard deviation of F0 (Hz) of the audio
# - mean_st:                mean F0 of the audio (semitones, reference 1Hz)
# - sd_st:                  standard deviation of F0 (semitones, reference 1Hz) 
#
# PHRASE BOUNDARIES:
# - firstwordstart:         start time of the first word in the phrase (seconds)
# - lastwordend:            end time of the last word in the phrase (seconds)
# - speechStart:            start time of the detected speech interval (seconds) 
# - speechEnd:              end time of the detected speech interval (seconds)
#
# Note: firstwordstart and speechStart, and lastwordend and speechEnd measure similar time points in different ways. May be used for debugging
#    
# PITCH CONTOUR:
# - f0_phrase:              vector of F0 values across the phrase (Hz)
# - st_phrase:              vector of F0 values across the phrase (semitones, reference 1Hz)
# - time:                   vector of time points corresponding to the F0/semitone values (seconds)
# - norm_time_phrase:       vector of normalized time points corresponding to the F0/semitone values
#
# LANDMARKS:
# - landmarkindex:          index of the detected landmark (integer)
# - word$:                  label of the detected landmark (i.e., word in the TextGrid)
# - wordStart:              start time of the detected word (seconds)   
# - wordEnd:                end time of the detected word (seconds)
#
#####################################################################################################################################

    


#____________________________________________ Initialize variables ____________________________________________________####


# form can be used to run the script from Praat GUI or to call the script from Python
# The form allows the user to input the name of the audio file and the corresponding TextGrid 
form Acoustics
    sentence input_file
    sentence textgrid_file
endform

# Read input files
txtgrd = Read from file: textgrid_file$
sound = Read from file: input_file$


#______________________________________ Check for anomalous speech activity ____________________________________________####

############################################################################################################################# 
# additional information:
# The following code detects speech activity in the recording if speech is longer than 0.5 seconds, and non-speech activity if it is longer than 0.5 seconds. 
# Ideally each recording should only have one speech interval (i.e., the sentence). If the script detects more than one speech interval it will not process the recording further. 
# This is a conservative approach to detect and skip recordings with "anomalous" speech activity, such as multiple utterances, long pauses, interrupted speech and/or incorrect forced alignment. 
# Improvements for future versions could include better handling of recordings with anomalous speech activity.
############################################################################################################################# 

speech_activity_txtgrd = To TextGrid (speech activity): 0, 0.3, 0.1, 70, 6000, -10, -35, 0.5, 0.5, "", "speech"

# combine original textgrid with speech activity textgrid
Extract one tier: 1
plusObject: txtgrd
Merge: "yes"
Rename: "merged_tg"
mergedtg = selected("TextGrid")

# count number of intervals in word tier
nWordIntervals = Get number of intervals: 1

# count number of intervals in speech activity tier
nIntervals = Get number of intervals: 3
nSpeechIntervals = Count intervals where: 3, "is equal to", "speech"

# Verify that there is exactly 1 speech interval (i.e., no interrupted speech, long pauses, or multiple utterances)
if nSpeechIntervals = 1
    for n to nIntervals
        label$ = Get label of interval: 3, n
        if label$ = "speech"

            # save start and end time of the speech interval
            speechStart = Get start time of interval: 3,n
            speechEnd = Get end time of interval: 3,n

            appendInfoLine: "Speech_Activity;", speechStart, ";", speechEnd
        endif
    endfor
    
    selectObject: mergedtg

    firstwordstart = 0
    lastwordend = 0
    landmarkindex = 1


#________________________________________________ Find landmarks _______________________________________________________####
# (only if no anomalous speech activity has been found)

# find the non-empty intervals (i.e., words) in the word tier and save their start and end times as landmarks
    for m to nWordIntervals
        wordStart = Get start time of interval: 1,m
        wordEnd = Get end time of interval: 1,m
        
        word$ = Get label of interval: 1, m

        if word$ != ""
            appendInfoLine: "Landmarks;", landmarkindex, ";", word$, ";", wordStart, ";", wordEnd
            
            # mark the start time of the first word as speech onset
            if landmarkindex = 1
                firstwordstart = wordStart
            endif
            landmarkindex = landmarkindex + 1

            # mark the end time of the last word as speech offset
            lastwordend = wordEnd
        endif
        
    endfor
    appendInfoLine: "Phrase;", firstwordstart, ";", lastwordend



elif nSpeechIntervals = 0
    appendInfoLine: "ERROR: No speech intervals found."
    exit
elif nSpeechIntervals > 1
    appendInfoLine: "ERROR: More than 1 speech interval found."
    exit

endif

#________________________________ Extract phrase (remove pre- and post-phrase silences)__________________________________#### 

# uses start of first word and end of last word as phrase boundaries
selectObject: sound

# Extract general features
intensity = Get intensity (dB)
duration = Get total duration

To TextGrid: "phrase", ""
Insert boundary: 1, firstwordstart
Insert boundary: 1, lastwordend
Set interval text: 1, 2, "phrase"

plusObject: sound
Extract non-empty intervals: 1, "no"


#------------------------------------------------------------------------------------
# Customized pitch extraction based on the distribution of F0 values in the recording 
#------------------------------------------------------------------------------------

# set pitch floor and ceiling to Praat default values
minPitch = 50
maxPitch = 800

# extract pitch contour using default pitch floor and ceiling values
To Pitch (filtered autocorrelation): 0, minPitch, maxPitch, 15, "no", 0.03, 0.09, 0.5, 0.055, 0.35, 0.14
pitchName$ = selected$("Pitch")

# calculate pitch floor and ceiling based on the distribution of F0 values in the extracted pitch contour (using interquartile range method)
q1 = Get quantile... 0 0 0.25 Hertz
q3 = Get quantile... 0 0 0.75 Hertz

selectObject: "Sound phrase"
floor = q1*0.75
ceiling = q3*2

# re-extract pitch contour using adjusted pitch floor and ceiling values (recording-specific extraction)
myPitch = To Pitch (filtered autocorrelation): 0, floor, ceiling, 15, "no", 0.03, 0.09, 0.5, 0.055, 0.35, 0.14
og_pt = Down to PitchTier
Copy: "pt_copy"

#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------


meanF0 = Get mean (curve): 0, 0
sdF0 = Get standard deviation (curve): 0, 0

# Convert Hz to semitones (reference 1Hz) 
# formula changes the values in the selected object permanently (pt_copy)
Formula: "12* log2(self)"
mean_st = Get mean (curve): 0, 0
sd_st = Get standard deviation (curve): 0, 0

# Output: Append results to info line (labelled "META" for easier parsing in Python)
appendInfoLine: "META;", intensity, ";", duration, ";", meanF0, ";", sdF0, ";" ,mean_st, ";", sd_st


#___________________________________________ Pitch Contour Extraction _______________________________________________####


# select original pitch tier object (with F0 values in Hz)
selectObject: og_pt

# 1. Extract raw phrase-level pitch contour 

# Extract time and F0 value of each pitch point
n_points = Get number of points

for y to n_points
    f0_phrase = Get value at index: y
    norm_f0_phrase = (f0_phrase - meanF0) / sdF0

    #transform to semitones (reference 1Hz)
    st_phrase = 12*log2(f0_phrase)
    norm_st_phrase = (st_phrase - mean_st) / sd_st

    time = Get time from index: y

    # normalize time by phrase duration
    norm_time_phrase = time /duration

    appendInfoLine: "PhrasePitchContour;", f0_phrase, ";", norm_time_phrase, ";", st_phrase, ";", time
endfor




# ============================================================
# Script Name:   PPTB_script.py
# Author:        Ronny Bujok
# Last Updated:  12-03-2026
#
# Description:
# This is the tentative script for the prosodic proficiency test battery (PPTB) data processing pipeline. It includes the following steps:
# - Automatic Speech Recognition (ASR) using Whisper
# - forced alignment with Montreal Forced Aligner (MFA) based on the ASR transcriptions
# - acoustic analysis with Praat based on the aligned TextGrid files
#
# The script can processes both L1 and L2 audio corpora. It is not yet complete as the final step is missing:
# - comparison of pitch contours with L1 reference contours
# - interpretation of the results in terms of prosodic proficiency
# 
# ============================================================


#%%
# # loading necessary libraries
import os
import sys
import torch
import pandas as pd
import shutil
import whisper
import subprocess
import parselmouth
import tempfile
import difflib
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from textgrid import TextGrid, IntervalTier
import glob
import numpy as np
import subprocess
from pathlib import Path



###################################################### INITIALIZATION ######################################################



#----------------- PATHS -----------------

BASE_DIR = Path(".")  # project root

AUDIO_DIR = Path(r"Audio")
#AUDIO_DIR = BASE_DIR / "Audio" / "L1_audio"
TEXTGRID_DIR = Path(r"TextGrids")
#TEXTGRID_DIR = BASE_DIR / "TextGrids" / "L1_TextGrids"
SCRIPT_PATH = BASE_DIR / "Praat_Scripts" / "measure_acoustics_v3.praat"
METADATA_PATH = BASE_DIR / "metadata.csv"

PRAAT_EXE = Path(r"C:\Program Files\Praat\Praat.exe")

OUTPUT_DIR = BASE_DIR / "Output"
OUTPUT_DIR.mkdir(exist_ok=True)

ASR_OUTPUT = OUTPUT_DIR / "output_asr_test.csv"
ACOUSTIC_OUTPUT = OUTPUT_DIR / "acoustics_output_test.csv"
FINAL_OUTPUT = OUTPUT_DIR / "full_output_test.csv"                 # merged ASR + acoustic features


# === Define paths ===
CORPUS_DIR = r"Audio" # define path to audio corpus
OUTPUT_DIR = r"TextGrids" # define path to save TextGrid files from MFA alignment

# define MFA models (requires MFA installation and model downloads)
DICTIONARY = "english_us_arpa"
ACOUSTIC_MODEL = "english_us_arpa"

# define Whisper model (requires Whisper installation and model download)
WHISPER_MODEL_SIZE = "tiny"  # Options: "tiny", "base", "small", "medium", "large"

# === Load Whisper model ===
print("Loading Whisper model...")
model = whisper.load_model(WHISPER_MODEL_SIZE)

# === Prepare folders ===
os.makedirs(CORPUS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Load item metadata ===
metadata_path = "metadata.csv"
metadata_df = pd.read_csv(metadata_path, delimiter=';', encoding='latin1')

# Fix common mis-encoded characters (like non-breaking spaces and curly quotes)
metadata_df["expected_transcription"] = (
    metadata_df["expected_transcription"]
    .str.replace("\xa0", " ", regex=False)  # non-breaking spaces
    .str.replace("Â", "", regex=False)      # stray Â
    .str.replace("’", "'", regex=False)     # curly apostrophes
    .str.replace('‘', "'", regex=False)
    .str.replace('“', '"', regex=False)
    .str.replace('”', '"', regex=False)
)

# === create output dataframe ===
results_ASR = []



# _____________________Function to clean transcriptions before comparison _______________
# This function makes text lowercase and strips punctuation, so two transcriptions can be compared fairly

def clean_text(text):
    import string
    return text.lower().translate(str.maketrans('', '', string.punctuation)).strip()


# _____________________ Function to compare transcriptions __________________________
# This function compares the transcription from the audio file with the one from the corpus.
# Determines if they are an exact match and calculates similarity
# output can later be used to inform on the validity of of the prosody comparison

def compare_transcriptions(expected_output, whisper_output):
    expected_output = clean_text(expected_output)
    whisper_output = clean_text(whisper_output)

    match = expected_output == whisper_output
    similarity = difflib.SequenceMatcher(None, expected_output, whisper_output).ratio()

    return match, similarity, expected_output, whisper_output



# %% 

###################################################### ASR WITH WHISPER ######################################################

# This loop processes each audio file in the CORPUS_DIR and transcribes it with Whisper,

for filename in os.listdir(CORPUS_DIR):
    if filename.lower().endswith(".wav"):
        wav_path = os.path.join(CORPUS_DIR, filename)

        basename = os.path.splitext(filename)[0]  # remove extension
        parts = basename.split("_")
        if len(parts) < 2:
            print(f"⚠️ Unexpected filename format: {filename}")
            continue

        itemnumber = parts[-1] if len(parts) > 1 else "UNKNOWN" # Assuming itemnumber is the last part of the filename

        PP_ID = parts[0] if len(parts) > 1 else "UNKNOWN"  # Assuming PP_ID is the first part of the filename

        # 1. Retrieve corresponding metadata 
        meta_row = metadata_df[metadata_df["filename"] == int(itemnumber)]
        if meta_row.empty:
            #print(f"⚠️ No metadata found for: {itemnumber}")
            continue
        meta_row_dict = meta_row.iloc[0].to_dict()

#------------------------------------------------------------------------------------------
        # 2. Transcribe with Whisper

        try:
            result = model.transcribe(wav_path, verbose=False, language="en", fp16=False)
            transcript = result["text"].strip()
            word_count = len(transcript.split())

        except Exception as e:
            #print(f"❌ Could not read audio file: {wav_path}")
            #print(f"   Reason: {e}")
            result_row = {
                "PP": PP_ID,
                "item": itemnumber,
                "filename": basename,
                "whisper_transcription": "audiofile not read",
                "expected_transcription": None,
                "transcription_match": None,
                "similarity": None,
                "expected_word_count": None,
                "word_count": None,
                "word_count_match": None,
                "word_count_similarity": None
            }
            result_row.update(meta_row_dict)
            results_ASR.append(result_row)
            continue  # skip to next file
#------------------------------------------------------------------------------------------
        
        # 3. Save transcript

        text_path = os.path.join(CORPUS_DIR, f"{os.path.splitext(filename)[0]}.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(transcript)
#--------------------------------------------------------------------------------------------

        # 4. compare Whisper transcription with expected transcription (what speaker was supposed to say)
        if not meta_row.empty and "expected_transcription" in meta_row.columns:
            expected_output = meta_row.iloc[0]["expected_transcription"]
            match, similarity, expected_output, whisper_output = compare_transcriptions(expected_output, transcript)
            #print("  → Comparing Whisper transcription to expected output...")
            if match:
                pass
                #print("✅ Match")
            else:
                pass
                #print("❌ Mismatch")
                #print(f"   ▶ Expected: {expected_output}")
                #print(f"   ▶ Actual:   {whisper_output}")
                #print(f"   💡 Similarity: {similarity:.2f}")
        else:
            pass
            #print(f"⚠️ Missing 'expected_transcription' for: {basename}")

        # Calculate word count and match with expected word count
        expected_word_count = meta_row.iloc[0].get("expected_word_count", None)

        if expected_word_count is not None:
            try:
                expected_word_count = int(expected_word_count)
                word_count_match = word_count == expected_word_count
                word_count_similarity = 1 - abs(word_count - expected_word_count) / max(word_count, expected_word_count)
            except ValueError:
                #print(f"⚠️ Invalid expected_word_count for {basename}: {expected_word_count}")
                word_count_match = None
                word_count_similarity = None
        else:
           #print(f"⚠️ Missing expected_word_count for: {basename}")
            word_count_match = None
            word_count_similarity = None


        # 5. Append to output results
        result_row = {
            "PP": PP_ID,
            "item": itemnumber,
            "filename": basename,
            "whisper_transcription": whisper_output,
            "expected_transcription": expected_output,
            "transcription_match": match,
            "similarity": round(similarity, 2) if similarity is not None else None,
            "expected_word_count": expected_word_count,
            "word_count": word_count,
            "word_count_match": word_count_match,
            "word_count_similarity": round(word_count_similarity, 2) if word_count_similarity is not None else None
        }
        result_row.update(meta_row_dict)
        result_row["filename"] = basename  # overwrite with correct string
        results_ASR.append(result_row)



# Save to CSV
df_asr = pd.DataFrame(results_ASR)
df_asr.to_csv("Output/output_asr_test.csv", index=False)


# %% 

###################################################### FORCED ALIGNMENT WITH MFA ######################################################

# runs forced alignment on the whole corpus using Montreal Forced Aligner (MFA)
# Make sure you have MFA installed and the .wav and .txt files in the corpus directory
# may need to set MFA_HOME environment variable to the path where MFA models are stored, e.g.:
#os.environ["MFA_HOME"] = "/root/Documents/MFA/pretrained_models/dictionary"

try:
    subprocess.run([
        "conda", "run", "-n", "mfa", "mfa", "align",
        CORPUS_DIR,
        DICTIONARY,
        ACOUSTIC_MODEL,
        OUTPUT_DIR,
        "--clean",
        #"--single_speaker",
        "--speaker_characters", "7", 
        "--output_format", "long_textgrid"
    ], check=True)
    print("\n✅ Forced alignment succesful! TextGrid files saved in the 'aligned' folder")
except Exception as e:
    print(f"❌ Error during MFA alignment: {e}")
# %% 


#______________________________________________ Acoustic Analysis with Praat (subprocess) ____________________________________________####


# -------------------- HELPER FUNCTIONS --------------------
def decode_praat_output(b):
    """
    Praat on Windows often outputs UTF-16-LE without BOM,
    sometimes mixed with ASCII. This handles both safely.
    """
    if not b:
        return ""
    try:
        txt = b.decode("utf-16-le")
    except UnicodeError:
        txt = b.decode("utf-8", errors="ignore")
    return txt.replace("\x00", "").strip()

def safe_float(x):
    """
    Convert Praat output to float. If undefined, return np.nan
    """
    try:
        if x in ("--undefined--", "undefined"):
            return np.nan
        return float(x)
    except:
        return np.nan
    


# -------------------- MAIN LOOP --------------------

# create output dataframe
results_acoustic = []

for wav_file in AUDIO_DIR.glob("*.wav"):
    try:
        filename_no_ext = wav_file.stem
        textgrid_file = TEXTGRID_DIR / f"{filename_no_ext}.TextGrid"
        if not textgrid_file.exists():
            print(f"❌ Missing TextGrid: {textgrid_file}")
            continue

        # === Run Praat ===
        cmd = [
            str(PRAAT_EXE),
            "--run",
            str(SCRIPT_PATH),
            str(wav_file.resolve()),
            str(textgrid_file.resolve())
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout_text = decode_praat_output(result.stdout)
        stderr_text = decode_praat_output(result.stderr)

        output_text = stdout_text + "\n" + stderr_text
        lines = [l.strip() for l in output_text.splitlines() if l.strip()]

        if result.returncode != 0:
            print(f"❌ Praat failed on {wav_file}")
            print(stderr_text)
            continue

        # -------------------- PARSE META --------------------
        meta_line = next((l for l in lines if l.startswith("META;")), None)

        if meta_line is None:
            print(f"❌ No META line for {wav_file}")
            print(lines[:5])
            continue

        meta = meta_line.split(";")
        (
            _,
            intensity,
            duration,
            mean_f0,
            sd_f0,
            mean_st,
            sd_st
        ) = meta[:7]


        # -------------------- CONTOURS --------------------
        
        f0_phrase = []
        norm_time_phrase = []
        st_phrase = []
        time = []


        # pitch_contour_f0 = []
        # pitch_contour_time = []
        # norm_pitch_contour_f0 = []
        # norm_pitch_contour_time = []

        # pitch_contour_st = []
        # norm_pitch_contour_st = []

        words = []
        

        landmark_index = []
        landmark_label = []
        landmark_start = []

        for line in lines:
            #complete pitch contour, including pauses etc.
            if line.startswith("PhrasePitchContour;"):
                _, f0, norm_t, st, t = line.split(";")
                f0_phrase.append(safe_float(f0))
                norm_time_phrase.append(safe_float(norm_t))
                st_phrase.append(safe_float(st))
                time.append(safe_float(t))

            # # extracted from word intervals
            # if line.startswith("PitchContourF0;"):
            #     _, f0, t, nf0, nt = line.split(";")
            #     pitch_contour_f0.append(safe_float(f0))
            #     pitch_contour_time.append(safe_float(t))
            #     norm_pitch_contour_f0.append(safe_float(nf0))
            #     norm_pitch_contour_time.append(safe_float(nt))

            # # extracted from word intervals
            # if line.startswith("PitchContourst;"):
            #     _, f0, nf0 = line.split(";")
            #     pitch_contour_st.append(safe_float(f0))
            #     norm_pitch_contour_st.append(safe_float(nf0))

            # elif line.startswith("WORD;"):
            #     parts = line.split(";")
            #     words.append(parts[1])

            elif line.startswith("Landmarks;"):
                parts = line.split(";")
                # Landmarks;index;label;start;end
                landmark_index.append(int(parts[1]))
                landmark_label.append(parts[2])
                landmark_start.append(safe_float(parts[3]))

        row = {
            "filename": filename_no_ext,
            "intensity": intensity,
            "duration": duration,
            "mean_F0": mean_f0,
            "sd_F0": sd_f0,
            "mean_st": mean_st,
            "sd_st": sd_st,
            "words": words,

            "f0_phrase": f0_phrase,
            "norm_time_phrase": norm_time_phrase,
            "st_phrase": st_phrase,
            "time": time,
            
            # "pitch_contour_f0": pitch_contour_f0,
            # "norm_pitch_contour_f0": norm_pitch_contour_f0,

            # "pitch_contour_st": pitch_contour_st,
            # "norm_pitch_contour_st": norm_pitch_contour_st,

            # "pitch_contour_time": pitch_contour_time,
            # "norm_pitch_contour_time": norm_pitch_contour_time,

            "landmark_index": landmark_index,
            "landmark_label": landmark_label,
            "landmark_start": landmark_start
                            }

        results_acoustic.append(pd.DataFrame([row]))
        print(f"✅ Succesfully processed {wav_file}")

    except Exception as e:
        print(f"🔥 Error processing {wav_file}: {e}")


# -------------------- SAVE --------------------
if results_acoustic:
    df_acoustic = pd.concat(results_acoustic, ignore_index=True)
    df_acoustic.to_csv(ACOUSTIC_OUTPUT, index=False)
else:
    print("❌ No valid files processed")



# ________________________________________ merge and save results__________________________________________

# load ASR output
df_asr = pd.read_csv(ASR_OUTPUT, encoding='latin1')

# Ensure all 'filename' columns are strings
df_asr['filename'] = df_asr['filename'].astype(str)
df_acoustic['filename'] = df_acoustic['filename'].astype(str)

df_combined = (df_asr.merge(df_acoustic, on="filename", how="outer"))

# Save final dataset
df_combined.to_csv(FINAL_OUTPUT, index=False)

print(f"✅ All data combined and saved → {FINAL_OUTPUT}")





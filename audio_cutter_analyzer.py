import os
import json
from pathlib import Path
import time
import wave
import struct

import speech_recognition as sr

# --- Configuration Variables (Edit these values) ---
INPUT_FOLDER = "C:\\User\\Path\\To\\source" # <<< Set your input folder path here
OUTPUT_FOLDER = "C:\\User\\Path\\To\\dest" # <<< Set your output segments folder path here
JSON_OUTPUT_FILE = "C:\\Users\\Path\\To\\file.json" # <<< Set your JSON output file path here

MIN_SILENCE_LEN_MS = 700      # Minimum length of silence (ms) to consider for a split
SILENCE_THRESHOLD_AMP = 0.01  # RMS amplitude threshold (0.0 to 1.0, normalized) below which audio is considered silent
KEEP_SILENCE_MS = 200         # Milliseconds of silence to keep at the beginning/end of each segment

def abbreviate_text(text, max_words=30):
    if not text:
        return ""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."

def transcribe_audio_segment(segment_path, log_callback):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(str(segment_path)) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError as e:
        return f"Speech recognition service error; {e}"
    except Exception as e:
        return f"Transcription error: {e}"

def calculate_rms(samples):
    """Calculate RMS for a list of audio samples."""
    if not samples:
        return 0.0
    return (sum(s**2 for s in samples) / len(samples))**0.5

def process_audio_file(audio_file_path, base_output_dir, log_callback,
                        min_silence_len_ms, silence_threshold_amp, keep_silence_ms):
    original_file_path_str = str(audio_file_path.resolve())
    log_callback(f"Processing: {audio_file_path.name}")
    log_callback(f"Attempting to load from: {original_file_path_str}")

    try:
        with wave.open(str(audio_file_path), 'rb') as wf:
            nchannels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            nframes = wf.getnframes()
            raw_frames = wf.readframes(nframes)
    except Exception as e:
        log_callback(f"Error loading WAV file {audio_file_path.name}: {e}")
        return None

    max_amplitude = 2**(sampwidth * 8 - 1) - 1 if sampwidth > 0 else 1

    format_char = {1: 'b', 2: 'h', 4: 'i'}.get(sampwidth)
    
    if format_char is None:
        log_callback(f"Unsupported sample width ({sampwidth} bytes) for {audio_file_path.name}. Only 1, 2, or 4 bytes supported.")
        return None
    
    all_samples = []
    if sampwidth == 3:
        for i in range(0, len(raw_frames), 3 * nchannels):
            for ch in range(nchannels):
                sample_bytes = raw_frames[i + ch * 3 : i + ch * 3 + 3]
                if sample_bytes[2] & 0x80:
                    padded_sample_bytes = sample_bytes + b'\xFF'
                else:
                    padded_sample_bytes = sample_bytes + b'\x00'
                all_samples.extend(struct.unpack('<i', padded_sample_bytes))
    else:
        num_samples = nframes * nchannels
        all_samples = list(struct.unpack('<' + format_char * num_samples, raw_frames))

    absolute_silence_threshold = silence_threshold_amp * max_amplitude

    nonsilent_ranges = []
    current_start = 0
    in_nonsilent_period = False
    
    chunk_size_samples = int(framerate * 0.050) 
    if chunk_size_samples == 0: chunk_size_samples = 1

    for i in range(0, len(all_samples), chunk_size_samples * nchannels):
        chunk_samples = all_samples[i : i + chunk_size_samples * nchannels]
        
        chunk_rms = calculate_rms(chunk_samples)

        is_silent = chunk_rms < absolute_silence_threshold

        current_time_ms = (i // nchannels) * 1000 // framerate

        if not is_silent and not in_nonsilent_period:
            current_start = current_time_ms
            in_nonsilent_period = True
        elif is_silent and in_nonsilent_period:            
            actual_nonsilent_end_ms = current_time_ms
            j = i
            while j < len(all_samples):
                next_chunk = all_samples[j : j + chunk_size_samples * nchannels]
                if not next_chunk:
                    break
                next_chunk_rms = calculate_rms(next_chunk)
                if next_chunk_rms >= absolute_silence_threshold:
                    break
                actual_nonsilent_end_ms = (j // nchannels) * 1000 // framerate
                j += chunk_size_samples * nchannels

            if (actual_nonsilent_end_ms - current_time_ms) >= min_silence_len_ms:
                nonsilent_ranges.append([current_start, current_time_ms])
                in_nonsilent_period = False
            
    if in_nonsilent_period:
        nonsilent_ranges.append([current_start, (nframes * 1000) // framerate])

    if not nonsilent_ranges:
        log_callback(f"No non-silent audio found in {audio_file_path.name} with current settings.")
        return None

    file_stem = audio_file_path.stem
    file_output_dir = base_output_dir / file_stem
    file_output_dir.mkdir(parents=True, exist_ok=True)

    segments_data = []

    for i, (start_ms, end_ms) in enumerate(nonsilent_ranges):
        start_ms_padded = max(0, start_ms - keep_silence_ms)
        end_ms_padded = min((nframes * 1000) // framerate, end_ms + keep_silence_ms)
        
        start_frame = int(start_ms_padded * framerate // 1000)
        end_frame = int(end_ms_padded * framerate // 1000)
        
        start_byte = start_frame * nchannels * sampwidth
        end_byte = end_frame * nchannels * sampwidth
        
        segment_raw_frames = raw_frames[start_byte:end_byte]
        
        segment_duration_ms = end_ms_padded - start_ms_padded

        segment_filename = f"{file_stem}_segment_{i:03d}.wav"
        segment_path = file_output_dir / segment_filename
        
        try:
            with wave.open(str(segment_path), 'wb') as new_wf:
                new_wf.setnchannels(nchannels)
                new_wf.setsampwidth(sampwidth)
                new_wf.setframerate(framerate)
                new_wf.writeframes(segment_raw_frames)
            log_callback(f"  Exported: {segment_path.name} (Duration: {segment_duration_ms}ms)")
        except Exception as e:
            log_callback(f"  Error exporting {segment_path.name}: {e}")
            continue

        transcribed_text = transcribe_audio_segment(segment_path, log_callback)
        log_callback(f"    Transcribed: \"{abbreviate_text(transcribed_text, 10)}...\"")
        
        abbreviated_transcription = abbreviate_text(transcribed_text)
        
        segments_data.append({
            "abbreviated_text": abbreviated_transcription,
            "segment_file": str(segment_path.resolve()),
            "timestamp_ms": start_ms,
            "segment_duration_ms": segment_duration_ms
        })
        time.sleep(0.1)

    if segments_data:
        return {original_file_path_str: segments_data}
    return None

def main():
    input_dir = Path(INPUT_FOLDER)
    output_dir = Path(OUTPUT_FOLDER)
    json_output_file = Path(JSON_OUTPUT_FILE)

    if not input_dir.is_dir():
        print(f"Error: Input folder '{input_dir}' does not exist. Please check INPUT_FOLDER variable.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}
    audio_files = [f for f in input_dir.glob('*.wav')]

    if not audio_files:
        print(f"No .wav files found in the input folder: {input_dir}.")
        return

    total_files = len(audio_files)
    for i, audio_file in enumerate(audio_files):
        print(f"\n--- Processing file {i+1}/{total_files}: {audio_file.name} ---")
        def current_file_logger(message):
            print(f"  {message}")
        
        file_result = process_audio_file(
            audio_file,
            output_dir,
            current_file_logger,
            MIN_SILENCE_LEN_MS,
            SILENCE_THRESHOLD_AMP,
            KEEP_SILENCE_MS
        )
        if file_result:
            all_results.update(file_result)
        time.sleep(0.1)

    try:
        with open(json_output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=4, ensure_ascii=False)
        print(f"\nProcessing complete. Results saved to {json_output_file}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    main()
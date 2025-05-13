import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import json
from pathlib import Path
import threading
import time
import tempfile

from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import speech_recognition as sr

# --- Core Processing Logic ---

def abbreviate_text(text, max_words=30):
    if not text:
        return ""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def transcribe_audio_segment(segment_path):
    recognizer = sr.Recognizer()
    
    try:
        audio_segment_pydub = AudioSegment.from_file(str(segment_path))
    except Exception as e:
        return f"Pydub could not load segment {segment_path.name}: {e}"

    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav_file:
            temp_wav_path = tmp_wav_file.name
        
        audio_segment_pydub.export(temp_wav_path, format="wav")

        with sr.AudioFile(temp_wav_path) as source:
            audio_data = recognizer.record(source)
        
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError as e:
        return f"Speech recognition service error; {e}"
    except Exception as e:
        return f"Transcription error (processing {segment_path.name}): {e}"
    finally:
        if 'temp_wav_path' in locals() and os.path.exists(temp_wav_path):
            try:
                os.remove(temp_wav_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary file {temp_wav_path}: {e}")

def process_audio_file(audio_file_path, base_output_dir, log_callback):
    original_file_path_str = str(audio_file_path)
    log_callback(f"Processing: {audio_file_path.name}")

    try:
        audio = AudioSegment.from_file(audio_file_path)
    except Exception as e:
        log_callback(f"Error loading {audio_file_path.name}: {e}")
        return None

    min_silence_len_ms = 700
    silence_thresh_dbfs = -40
    keep_silence_ms = 200

    nonsilent_ranges = detect_nonsilent(
        audio,
        min_silence_len=min_silence_len_ms,
        silence_thresh=silence_thresh_dbfs,
        seek_step=1
    )

    if not nonsilent_ranges:
        log_callback(f"No non-silent audio found in {audio_file_path.name}")
        return None

    file_stem = audio_file_path.stem
    file_output_dir = base_output_dir / file_stem
    file_output_dir.mkdir(parents=True, exist_ok=True)

    segments_data = []

    for i, (start_ms, end_ms) in enumerate(nonsilent_ranges):
        start_ms_padded = max(0, start_ms - keep_silence_ms)
        end_ms_padded = min(len(audio), end_ms + keep_silence_ms)
        
        segment = audio[start_ms_padded:end_ms_padded]
        segment_filename = f"{file_stem}_segment_{i:03d}{audio_file_path.suffix}"
        segment_path = file_output_dir / segment_filename
        
        try:
            segment.export(segment_path, format=audio_file_path.suffix[1:])
            log_callback(f"  Exported: {segment_path.name}")
        except Exception as e:
            log_callback(f"  Error exporting {segment_path.name}: {e}")
            continue

        transcribed_text = transcribe_audio_segment(segment_path)
        log_callback(f"    Transcribed: \"{transcribed_text[:50]}...\"")
        
        abbreviated_transcription = abbreviate_text(transcribed_text)
        
        segments_data.append({
            "abbreviated_text": abbreviated_transcription,
            "segment_file": str(segment_path.resolve()),
            "timestamp_ms": start_ms
        })
        time.sleep(0.1) 

    if segments_data:
        return {original_file_path_str: segments_data}
    return None


# --- GUI Application ---
class AudioAnalyzerApp:
    def __init__(self, root):
        self.root = root
        root.title("Audio Analyzer")

        tk.Label(root, text="Input Audio Folder:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.input_folder_entry = tk.Entry(root, width=50)
        self.input_folder_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="Browse...", command=self.browse_input_folder).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(root, text="Output Segments Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.output_folder_entry = tk.Entry(root, width=50)
        self.output_folder_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(root, text="Browse...", command=self.browse_output_folder).grid(row=1, column=2, padx=5, pady=5)

        tk.Label(root, text="JSON Output File:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.json_file_entry = tk.Entry(root, width=50)
        self.json_file_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Button(root, text="Save As...", command=self.browse_json_file).grid(row=2, column=2, padx=5, pady=5)

        self.start_button = tk.Button(root, text="Start Processing", command=self.start_processing_thread)
        self.start_button.grid(row=3, column=0, columnspan=3, pady=10)

        tk.Label(root, text="Log:").grid(row=4, column=0, sticky="nw", padx=5, pady=5)
        self.log_area = scrolledtext.ScrolledText(root, width=70, height=15, wrap=tk.WORD)
        self.log_area.grid(row=5, column=0, columnspan=3, padx=5, pady=5)
        self.log_area.config(state=tk.DISABLED)

    def _browse_folder(self, entry_widget):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder_selected)

    def browse_input_folder(self):
        self._browse_folder(self.input_folder_entry)

    def browse_output_folder(self):
        self._browse_folder(self.output_folder_entry)

    def browse_json_file(self):
        file_selected = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_selected:
            self.json_file_entry.delete(0, tk.END)
            self.json_file_entry.insert(0, file_selected)

    def log_message(self, message):
        def _update_log():
            self.log_area.config(state=tk.NORMAL)
            self.log_area.insert(tk.END, message + "\n")
            self.log_area.see(tk.END)
            self.log_area.config(state=tk.DISABLED)
        self.root.after(0, _update_log) 

    def start_processing_thread(self):
        input_folder = self.input_folder_entry.get()
        output_folder = self.output_folder_entry.get()
        json_file_path = self.json_file_entry.get()

        if not all([input_folder, output_folder, json_file_path]):
            messagebox.showerror("Error", "All paths must be specified.")
            return
        
        if not Path(input_folder).is_dir():
            messagebox.showerror("Error", "Input folder does not exist.")
            return
        
        Path(output_folder).mkdir(parents=True, exist_ok=True)

        self.start_button.config(state=tk.DISABLED)
        self.log_message("Starting processing...")

        thread = threading.Thread(target=self.run_processing, args=(input_folder, output_folder, json_file_path), daemon=True)
        thread.start()

    def run_processing(self, input_folder_str, output_folder_str, json_file_path_str):
        input_dir = Path(input_folder_str)
        output_dir = Path(output_folder_str)
        json_output_file = Path(json_file_path_str)
        
        all_results = {}
        audio_files = [f for f in input_dir.glob('*') if f.suffix.lower() in ('.mp3', '.wav')]

        if not audio_files:
            self.log_message("No .mp3 or .wav files found in the input folder.")
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            return

        total_files = len(audio_files)
        for i, audio_file in enumerate(audio_files):
            self.log_message(f"--- Progress: {i+1}/{total_files} ---")
            file_result = process_audio_file(audio_file, output_dir, self.log_message)
            if file_result:
                all_results.update(file_result)
            time.sleep(0.1)

        try:
            with open(json_output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=4, ensure_ascii=False)
            self.log_message(f"Processing complete. Results saved to {json_output_file}")
        except Exception as e:
            self.log_message(f"Error saving JSON file: {e}")
            messagebox.showerror("JSON Save Error", f"Could not save JSON: {e}")

        self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioAnalyzerApp(root)
    root.mainloop()
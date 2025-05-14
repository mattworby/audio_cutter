# Audio Segmenter and Analyzer

This Python script analyzes a folder of audio files (MP3 or WAV), segments them based on non-silent periods, transcribes the speech in each segment, provides an abbreviated version of the transcribed text, and outputs a JSON file detailing the results. It features a simple Tkinter-based GUI for user input.

## Features

*   Processes MP3 and WAV audio files.
*   Segments audio based on detected non-silent periods (i.e., "series of audio noise" or speech).
*   Exports each segment as a separate audio file.
*   Transcribes speech from each segment using Google Web Speech API.
*   Provides an abbreviated version (first N words) of the transcribed text for each segment.
*   Creates a JSON output file mapping original files to their segments, abbreviated text, and timestamps.
*   Simple GUI for specifying input/output paths.

## Prerequisites

1.  **Python 3.7+**: Ensure you have Python installed.
2.  **pip**: Python's package installer (usually comes with Python).
3.  **FFmpeg**: This is crucial for `pydub` to process audio files.
    *   **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, and add the `bin` folder to your system's PATH environment variable.
    *   **macOS (using Homebrew)**: `brew install ffmpeg`
    *   **Linux (Debian/Ubuntu)**: `sudo apt-get update && sudo apt-get install ffmpeg`
    *   Verify installation by typing `ffmpeg -version` in your terminal.

## Setup

1.  **Clone or Download:**
    Get the script (`audio_cutter_analyzer.py` or similar name) and the `requirements.txt` file.

2.  **Create a Virtual Environment (Recommended):**
    Open your terminal or command prompt in the project directory.
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    *   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install Dependencies:**
    With the virtual environment activated, install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

1.  **Execute the Script:**
    Navigate to the directory containing `audio_cutter_analyzer.py` (or the name you saved it as) in your terminal (ensure your virtual environment is activated).
    Run the script:
    ```bash
    python audio_cutter_analyzer.py
    ```

2.  **Using the UI:**
    A small window will appear with the following fields:
    *   **Input Audio Folder:** Click "Browse..." to select the folder containing your thousands of MP3 or WAV audio files.
    *   **Output Segments Folder:** Click "Browse..." to choose a directory where the cut audio segments will be saved. The script will create subfolders within this directory, one for each original audio file, to store its segments.
    *   **JSON Output File:** Click "Save As..." to specify the name and location for the JSON summary file (e.g., `analysis_results.json`).
    *   **Start Processing:** Click this button to begin the analysis.
    *   **Log:** A text area below the buttons will display progress messages, file names being processed, and any errors encountered.

3.  **Processing:**
    The script will iterate through each audio file:
    *   Detect non-silent portions.
    *   Export these segments.
    *   Transcribe each segment (requires an internet connection for Google Web Speech API).
    *   Generate an abbreviated version of the transcribed text.
    The UI will remain responsive due to threading, but the overall process can be very time-consuming for a large number of files.

## Output

1.  **Segmented Audio Files:**
    In the "Output Segments Folder" you specified, subdirectories will be created for each processed audio file. Inside these subdirectories, you'll find the individual audio segments (e.g., `original_filename_segment_000.mp3`, `original_filename_segment_001.mp3`, etc.).

2.  **JSON Output File:**
    The JSON file you specified will contain a dictionary where:
    *   Keys are the full paths to the original audio files.
    *   Values are lists of dictionaries, each representing a segment:
        ```json
        {
            "C:\\path\\to\\your\\audio\\folder\\original_audio1.mp3": [
                {
                    "abbreviated_text": "This is an abbreviated version of the transcribed text...",
                    "segment_file": "D:\\path\\to\\your\\output\\segments\\original_audio1\\original_audio1_segment_000.mp3",
                    "timestamp_ms": 1234,
                    "segment_duration_ms": 5678
                },
                {
                    "abbreviated_text": "Another piece of transcribed text, also abbreviated...",
                    "segment_file": "D:\\path\\to\\your\\output\\segments\\original_audio1\\original_audio1_segment_001.mp3",
                    "timestamp_ms": 8000,
                    "segment_duration_ms": 4321
                }
            ],
            "C:\\path\\to\\your\\audio\\folder\\another_audio.wav": [
                // ... similar entries
            ]
        }
        ```
        *   `abbreviated_text`: An abbreviated version (e.g., first 30 words) of the transcribed text from the segment.
        *   `segment_file`: The full path to the exported audio segment file.
        *   `timestamp_ms`: The start time (in milliseconds) of this non-silent segment in the *original* audio file.
        *   `segment_duration_ms`: The duration (in milliseconds) of this specific clipped audio segment.

## Important Notes & Configuration

*   **Internet Connection:** Required for the default speech-to-text functionality (Google Web Speech API).
*   **API Limits:** The Google Web Speech API is free but has usage limits. For very large-scale processing, consider alternative speech recognition services or offline models.
*   **Processing Time:** Analyzing thousands of audio files, especially with speech recognition, will take a significant amount of time.
*   **Silence Detection Parameters:**
    In the `process_audio_file` function within the script, you can find these parameters:
    *   `min_silence_len_ms`: Minimum duration (in ms) for a silence to be considered a split point.
    *   `silence_thresh_dbfs`: Audio below this dBFS level is considered silent.
    *   `keep_silence_ms`: Milliseconds of silence to keep at the beginning/end of chunks.
    You may need to tune these values based on the characteristics of your audio files for optimal segmentation.
*   **Text Abbreviation:** The `abbreviate_text` function currently takes the first `max_words` (default 30) words. You can adjust this value in the script if needed.

## Troubleshooting

*   **`pydub` errors / `Could not find ffplay or avplay` / `FileNotFoundError: [WinError 2] The system cannot find the file specified` (referring to ffmpeg):**
    This almost always means `ffmpeg` is not installed correctly or not in your system's PATH. Double-check the FFmpeg prerequisite steps.
*   **Speech Recognition Errors (`Speech recognition service error` or `Could not understand audio`):**
    *   Ensure your internet connection is stable.
    *   The audio segment might be too noisy, contain no clear speech, or be in a language not well-supported by the default recognizer settings.
    *   You might be hitting API rate limits.

## Libraries Used

*   **Tkinter**: For the GUI.
*   **Pydub**: For audio manipulation (loading, slicing, silence detection, exporting).
*   **SpeechRecognition**: For speech-to-text.
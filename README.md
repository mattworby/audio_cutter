# WAV Audio Segmenter and Analyzer (Hardcoded Config)

This Python script analyzes a folder of **WAV audio files**, segments them based on non-silent periods, transcribes the speech in each segment, provides an abbreviated version of the transcribed text, and outputs a JSON file detailing the results. It also attempts to classify the type of vocalization (e.g., sustained sounds, repetitive phrases) based on the transcribed text. This version minimizes external library dependencies and has its configuration settings hardcoded directly within the script.

## Features

*   Processes **WAV audio files exclusively**.
*   Segments audio based on detected non-silent periods (custom implementation).
*   Exports each segment as a separate WAV audio file.
*   Transcribes speech from each segment using Google Web Speech API.
*   Provides an abbreviated version (first N words) of the transcribed text for each segment.
*   **Classifies vocalization type** (e.g., sustained vowel, repetitive phrase) based on the transcribed text.
*   Creates a JSON output file mapping original files to their segments, abbreviated text, timestamps, segment durations, and vocalization type.
*   **Configuration settings are hardcoded** inside the `audio_analyzer_hardcoded.py` file.

## Prerequisites

1.  **Python 3.7+**: Ensure you have Python installed.
2.  **pip**: Python's package installer (usually comes with Python).

## Setup

1.  **Clone or Download:**
    Get the script (`audio_analyzer_hardcoded.py` or similar name) and the `requirements.txt` file.

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

Before running, you **must edit the configuration variables directly in the `audio_analyzer_hardcoded.py` file**.

1.  **Edit Configuration Variables:**
    Open `audio_analyzer_hardcoded.py` in a text editor.
    Locate the section starting with `# --- Configuration Variables (Edit these values) ---`.
    Update the paths for `INPUT_FOLDER`, `OUTPUT_FOLDER`, and `JSON_OUTPUT_FILE` to your desired locations.
    Optionally, adjust `MIN_SILENCE_LEN_MS`, `SILENCE_THRESHOLD_AMP`, and `KEEP_SILENCE_MS` if needed.

    Example:
    ```python
    INPUT_FOLDER = "D:\\MyWAVs\\Source"
    OUTPUT_FOLDER = "D:\\MyWAVs\\Segments"
    JSON_OUTPUT_FILE = "D:\\MyWAVs\\analysis_summary.json"

    MIN_SILENCE_LEN_MS = 800
    SILENCE_THRESHOLD_AMP = 0.008
    KEEP_SILENCE_MS = 250
    ```

2.  **Execute the Script:**
    Navigate to the directory containing `audio_analyzer_hardcoded.py` in your terminal (ensure your virtual environment is activated).
    Run the script:
    ```bash
    python audio_analyzer_hardcoded.py
    ```

    The script will print progress and status messages to the console.

## Output

1.  **Segmented Audio Files:**
    In the `OUTPUT_FOLDER` you specified, subdirectories will be created for each processed WAV file. Inside these, you'll find the individual WAV audio segments (e.g., `original_filename_segment_000.wav`).

2.  **JSON Output File:**
    The JSON file you specified in `JSON_OUTPUT_FILE` will contain a dictionary where:
    *   Keys are the full paths to the original audio files.
    *   Values are lists of dictionaries, each representing a segment:
        ```json
        {
            "C:\\path\\to\\your\\audio\\folder\\original_audio1.wav": [
                {
                    "abbreviated_text": "This is an abbreviated version of the transcribed text...",
                    "segment_file": "D:\\path\\to\\your\\output\\segments\\original_audio1\\original_audio1_segment_000.wav",
                    "timestamp_ms": 1234,
                    "segment_duration_ms": 5678,
                    "vocalization_type": "Repetitive Word/Phrase"
                },
                {
                    "abbreviated_text": "Another piece of transcribed text, also abbreviated...",
                    "segment_file": "D:\\path\\to\\your\\output\\segments\\original_audio1\\original_audio1_segment_001.wav",
                    "timestamp_ms": 8000,
                    "segment_duration_ms": 4321,
                    "vocalization_type": "Sustained Vowel"
                }
            ],
            "C:\\path\\to\\your\\audio\\folder\\another_audio.wav": [
                // ... similar entries
            ]
        }
        ```
        *   `abbreviated_text`: An abbreviated version (e.g., first 30 words) of the transcribed text from the segment.
        *   `segment_file`: The full path to the exported WAV audio segment file.
        *   `timestamp_ms`: The start time (in milliseconds) of this non-silent segment in the *original* audio file.
        *   `segment_duration_ms`: The duration (in milliseconds) of this specific clipped audio segment.
        *   `vocalization_type`: A classification of the vocalization (e.g., "Sustained Vowel", "Repetitive Word/Phrase", "Common Filler/Sustained Non-Word", "Normal Speech", "Empty/Unintelligible").

## Important Notes & Configuration

*   **Input Format:** This script **only processes standard, uncompressed PCM `.wav` files**. Other WAV formats (e.g., ADPCM, compressed, floating-point) or other audio formats (MP3, FLAC) are NOT supported by this script due to the custom audio processing.
*   **Vocalization Classification Limitations:** The `vocalization_type` field is generated by **text-based pattern matching on the transcription**. It does *not* involve deep audio signal analysis (e.g., pitch or timbre detection). Its accuracy depends entirely on the accuracy of the speech-to-text engine and the effectiveness of the simple text-based heuristics. It may not reliably detect all forms of non-word vocalizations or repetitions, especially if transcription is imperfect or patterns are complex.
*   **Silence Detection (`SILENCE_THRESHOLD_AMP`):** This parameter is crucial and may require significant tuning based on the ambient noise level of your audio. It represents a normalized RMS amplitude (0.0 to 1.0) below which audio is considered silent. A value of `0.01` is a starting point, but you might need to adjust it (e.g., `0.005` for quieter silence, `0.05` for louder silence).
*   **Internet Connection:** Required for the Google Web Speech API.
*   **API Limits:** Google's Web Speech API is free but has usage limits. For very large-scale processing, you might hit these limits.
*   **Processing Time:** Analyzing thousands of audio files will take a significant amount of time.

## Libraries Used and PII/PHI Considerations

Understanding how each library handles data is critical for data privacy (PII - Personally Identifiable Information, PHI - Protected Health Information).

### Built-in Python Libraries:

These libraries are part of Python's standard distribution. They run locally on your machine and do not inherently transmit data externally.

*   **`os`**:
    *   **Purpose:** Provides a way to interact with the operating system, such as creating directories, checking file existence, and joining/splitting paths.
    *   **Why Used Here:** Used for managing file paths (`os.path.exists`, `os.mkdir`) and interacting with the filesystem for input/output.
    *   **PII/PHI Considerations:** `os` itself does not process the *content* of PII/PHI. However, if your file paths or filenames contain PII/PHI (e.g., "patient_john_doe_audio.wav"), `os` will handle these strings. Ensure your file naming conventions and folder structures do not inadvertently expose sensitive information.

*   **`json`**:
    *   **Purpose:** Enables encoding and decoding JSON (JavaScript Object Notation) data.
    *   **Why Used Here:** Used to write the final analysis summary (containing transcribed text) into a structured JSON file.
    *   **PII/PHI Considerations:** If the transcribed audio contains PII/PHI, then this sensitive data will be written into the JSON file. The `json` library merely formats this data; it does not introduce new PII/PHI or transmit it. **The security of the output JSON file is paramount.** It should be stored in a secure, access-controlled environment, and subject to appropriate data retention policies.

*   **`pathlib`**:
    *   **Purpose:** Offers an object-oriented approach to filesystem paths. It provides a more robust and readable way to manipulate paths compared to string-based methods.
    *   **Why Used Here:** Used for creating `Path` objects, checking if paths are directories (`.is_dir()`), and creating nested directories (`.mkdir(parents=True)`).
    *   **PII/PHI Considerations:** Similar to `os`, `pathlib` works with path strings. If these strings contain PII/PHI, `pathlib` will handle them. Adhere to secure file naming conventions.

*   **`time`**:
    *   **Purpose:** Provides time-related functions, including pausing program execution.
    *   **Why Used Here:** A small delay (`time.sleep(0.1)`) is introduced between processing each audio file to manage resource consumption and avoid overwhelming external APIs (like Google's Speech-to-Text).
    *   **PII/PHI Considerations:** None. This library does not interact with PII/PHI.

*   **`wave`**:
    *   **Purpose:** Python's built-in module for reading and writing standard uncompressed WAV audio files.
    *   **Why Used Here:** Used to open the input WAV files, extract their raw audio data (samples), and then write segments of this raw data to new WAV files. This is the core audio I/O component in this version of the script.
    *   **PII/PHI Considerations:** This library directly processes the raw audio data (the bytes that constitute the sound). If the audio contains spoken PII/PHI, then this raw data *is* the sensitive information being handled. **All audio files (input and output segments) containing PII/PHI must be treated as sensitive data and stored securely with appropriate access controls.**

*   **`struct`**:
    *   **Purpose:** Interprets sequences of bytes as packed binary data, and vice versa.
    *   **Why Used Here:** Used to convert the raw audio bytes read from `.wav` files into numerical sample values (integers). This conversion is necessary to perform calculations like Root Mean Square (RMS) for silence detection.
    *   **PII/PHI Considerations:** `struct` operates directly on the raw audio data bytes, similar to the `wave` module. Therefore, it handles the underlying sensitive audio data. **The same security considerations for the `wave` module apply here.**

*   **`re` (Regular Expressions):**
    *   **Purpose:** Provides operations for working with regular expressions.
    *   **Why Used Here:** Used within the `get_vocalization_type` function to detect patterns (like repeated characters or words) in the transcribed text.
    *   **PII/PHI Considerations:** `re` itself does not introduce or transmit PII/PHI. It processes the transcribed text locally. If the transcribed text contains PII/PHI, `re` will operate on that sensitive text. The security of the *source* of the text (the transcription) and the *storage* of the text (the JSON file) are the primary concerns.

*   **`collections.Counter`:**
    *   **Purpose:** A specialized dictionary subclass for counting hashable objects.
    *   **Why Used Here:** Used within the `get_vocalization_type` function to efficiently count character frequencies to detect dominant characters in text for sustained vocalization classification.
    *   **PII/PHI Considerations:** Similar to `re`, `collections.Counter` processes the transcribed text locally. It does not introduce or transmit PII/PHI.

### External Library:

*   **`SpeechRecognition`**:
    *   **Purpose:** Provides an easy-to-use interface for various speech recognition APIs and offline engines.
    *   **Why Used Here:** To convert the audio segments into text. By default, and as configured in this script, it uses **Google's Web Speech API**.
    *   **PII/PHI Considerations: This is the most critical component concerning PII/PHI.**
        *   **External Data Transmission:** When `recognize_google()` is called, the audio data from your segments is **sent over the internet to Google's servers** for processing. Google's privacy policy applies to this data. If your audio contains PII/PHI, that sensitive data is being transmitted to and processed by a third-party service.
        *   **Data Processing by Third-Party:** Google processes the audio to convert it into text. While Google generally has strong security measures, the data is no longer solely under your control during this phase.
        *   **Transcribed Text:** The output (the transcribed text) will contain any PII/PHI spoken in the audio. This text is then stored locally in your JSON output file.
    *   **Mitigation Strategies:**
        *   **Explicit Disclosure:** Users of this script **must be aware** that audio data is sent to an an external service (Google).
        *   **Data Governance:** Ensure compliance with all relevant data privacy regulations (e.g., HIPAA for PHI, GDPR for PII) when deciding to send sensitive audio to any third-party API.
        *   **Alternative Engines:** For strict PII/PHI compliance or environments where external transmission is forbidden, you would need to modify the script to use an **offline speech recognition engine** (e.g., Vosk, Mozilla DeepSpeech). These engines run locally and keep all data on your premises, but they require more complex setup, model downloads, and potentially more computational resources. This script does *not* include offline engine support and using such an engine would be a significant change requiring different libraries.

---

**General Data Privacy and Security Considerations:**

*   **Data at Rest:** Ensure the input audio files, the generated audio segments, and the final JSON output file are stored on secure systems with appropriate access controls (e.g., encrypted storage, limited permissions).
*   **Data Minimization:** Only retain the audio segments and transcribed data that are absolutely necessary for your purpose. Implement data retention policies.
*   **Access Control:** Limit who has access to the input audio, the output segments, and the JSON analysis file.
*   **Legal & Compliance:** Always consult with legal counsel regarding data privacy regulations (e.g., HIPAA, GDPR, CCPA) that apply to your specific data and use case. Relying on free web APIs for sensitive data might not meet stringent compliance requirements.
from pathlib import Path
from datetime import datetime
import numpy as np
import soundfile as sf
import calendar

SAMPLE_RATE = 22050
DURATION_SEC = 5
YEAR = 2026
MIN_FREQ = 50
MAX_FREQ = 3000
MINUTES = [10]

def generate_sine(freq, duration_sec=5, sr=22050):
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    audio = 0.2 * np.sin(2 * np.pi * freq * t)
    return audio.astype(np.float32)

def generate_audio_files(output_folder):
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamps = []
    for month in range(1, 13):
        days_in_month = calendar.monthrange(YEAR, month)[1]
        for day in range(1, days_in_month + 1):
            for hour in range(24):
                for minute in MINUTES:
                    timestamps.append(datetime(YEAR, month, day, hour, minute))

    total = len(timestamps)
    frequencies = np.linspace(MIN_FREQ, MAX_FREQ, total)

    for idx, (ts, freq) in enumerate(zip(timestamps, frequencies)):
        audio = generate_sine(freq, DURATION_SEC, SAMPLE_RATE)

        # Saved natively as .wav to avoid FFmpeg crashing on Windows
        filename = f"audio_{ts.year:04d}_{ts.month:02d}_{ts.day:02d}_{ts.hour:02d}_{ts.minute:02d}.wav"
        filepath = output_path / filename

        sf.write(filepath, audio, SAMPLE_RATE)

        print(f"[{idx+1}/{total}] {filename} -> {freq:.2f} Hz")

if __name__ == "__main__":
    # Pointed directly to our application's audio folder
    generate_audio_files("audio_files")
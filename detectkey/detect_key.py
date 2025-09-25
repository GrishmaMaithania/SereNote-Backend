import librosa
import numpy as np

major_template = np.array([
    6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
    2.52, 5.19, 2.39, 3.66, 2.29, 2.88
])
minor_template = np.array([
    6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
    2.54, 4.75, 3.98, 2.69, 3.34, 3.17
])
KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def rotate(template, n):
    return np.roll(template, n)

def detect_key(filepath):
    y, sr = librosa.load(filepath)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)

    best_key = ""
    best_score = -np.inf

    for i in range(12):
        score = np.corrcoef(chroma_mean, rotate(major_template, i))[0, 1]
        if score > best_score:
            best_score = score
            best_key = KEYS[i] + " Major"

    for i in range(12):
        score = np.corrcoef(chroma_mean, rotate(minor_template, i))[0, 1]
        if score > best_score:
            best_score = score
            best_key = KEYS[i] + " Minor"

    return best_key

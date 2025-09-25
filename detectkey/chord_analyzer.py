import librosa
import numpy as np

def get_chord_templates():
    """Generate 12 major + 12 minor chord templates."""
    templates = {}
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F',
             'F#', 'G', 'G#', 'A', 'A#', 'B']
    for i, note in enumerate(notes):
        # Major (root, major 3rd, perfect 5th)
        major_template = np.zeros(12)
        major_template[[i, (i + 4) % 12, (i + 7) % 12]] = 1
        templates[f"{note}"] = major_template

        # Minor (root, minor 3rd, perfect 5th)
        minor_template = np.zeros(12)
        minor_template[[i, (i + 3) % 12, (i + 7) % 12]] = 1
        templates[f"{note}m"] = minor_template

    return templates

def get_chord_templates():
    """Generate templates for major, minor, and diminished triads."""
    templates = {}
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    for i, note in enumerate(notes):
        # Major triad
        major = np.zeros(12)
        major[[i, (i + 4) % 12, (i + 7) % 12]] = 1
        templates[f'{note}'] = major

        # Minor triad
        minor = np.zeros(12)
        minor[[i, (i + 3) % 12, (i + 7) % 12]] = 1
        templates[f'{note}m'] = minor

        # Diminished triad
        dim = np.zeros(12)
        dim[[i, (i + 3) % 12, (i + 6) % 12]] = 1
        templates[f'{note}dim'] = dim
    return templates


# --- Diatonic Chords for Key ---
def get_diatonic_chords(key_name):
    """Return the 7 diatonic triads for the given key."""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    note_to_index = {n: i for i, n in enumerate(notes)}

    if "Major" in key_name:
        root, _ = key_name.split()
        i = note_to_index[root]
        # Major scale intervals: W W H W W W H
        scale_degrees = [0, 2, 4, 5, 7, 9, 11]
        scale_notes = [(i + d) % 12 for d in scale_degrees]
        chords = [
            notes[scale_notes[0]],      # I major
            notes[scale_notes[1]] + "m",# ii minor
            notes[scale_notes[2]] + "m",# iii minor
            notes[scale_notes[3]],      # IV major
            notes[scale_notes[4]],      # V major
            notes[scale_notes[5]] + "m",# vi minor
            notes[scale_notes[6]] + "dim" # vii° diminished
        ]
    else:  # Natural minor
        root, _ = key_name.split()
        i = note_to_index[root]
        # Natural minor intervals: W H W W H W W
        scale_degrees = [0, 2, 3, 5, 7, 8, 10]
        scale_notes = [(i + d) % 12 for d in scale_degrees]
        chords = [
            notes[scale_notes[0]] + "m", # i minor
            notes[scale_notes[1]] + "dim",# ii° dim
            notes[scale_notes[2]],       # III major
            notes[scale_notes[3]] + "m", # iv minor
            notes[scale_notes[4]] + "m", # v minor
            notes[scale_notes[5]],       # VI major
            notes[scale_notes[6]],       # VII major
        ]
    return chords


# --- Key-aware Chord Detection ---
def detect_chords(audio_path, detect_key_fn, group_size=4, restrict_to_key=True):

    y, sr = librosa.load(audio_path)
    duration = librosa.get_duration(y=y, sr=sr)

    # Beat tracking
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Chroma
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    beat_chroma = librosa.util.sync(chroma, beat_frames, aggregate=np.median)

    # Detect key
    key_name = detect_key_fn(audio_path)
    allowed_chords = get_diatonic_chords(key_name) if restrict_to_key else None

    templates = get_chord_templates()
    chords_on_each_group = []

    # Match groups of beats to chords
    for i in range(0, beat_chroma.shape[1], group_size):
        group = beat_chroma[:, i:i + group_size]
        if group.shape[1] == 0:
            continue
        group_avg = np.median(group, axis=1)

        # Restrict to allowed chords
        search_space = allowed_chords if allowed_chords else templates.keys()
        correlations = {
            chord: np.corrcoef(group_avg, templates[chord])[0, 1]
            for chord in search_space if chord in templates
        }
        best_chord = max(correlations, key=correlations.get)
        chords_on_each_group.append((best_chord, i))

    # Convert to times
    chords_with_times = []
    for chord, group_idx in chords_on_each_group:
        start_idx = group_idx
        end_idx = group_idx + group_size
        start_time = beat_times[start_idx] if start_idx < len(beat_times) else duration
        end_time = beat_times[end_idx] if end_idx < len(beat_times) else duration
        chords_with_times.append({
            "chord": chord,
            "start_time": round(start_time, 2),
            "end_time": round(end_time, 2)
        })

    # Merge consecutive identical chords
    final_chords = []
    for chord in chords_with_times:
        if final_chords and final_chords[-1]['chord'] == chord['chord']:
            final_chords[-1]['end_time'] = chord['end_time']
        else:
            final_chords.append(chord)

    return {
        "key": key_name,
        "chords": final_chords
    }


if __name__ == "__main__":
    from detect_key import detect_key   # ✅ import your real key detector

    path = "song.mp3"  # make sure this file exists in your project folder
    chords = detect_chords(path, detect_key_fn=detect_key, group_size=4)

    print(f"Detected key: {chords['key']}")
    for c in chords["chords"]:
        print(f"{c['chord']} from {c['start_time']}s to {c['end_time']}s")


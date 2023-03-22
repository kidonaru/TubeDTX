import librosa
import pretty_midi
import numpy as np

from scripts.config_utils import ProjectConfig
from scripts.debug_utils import debug_args

def _clamp(n, smallest, largest):
    return sorted([smallest, n, largest])[1]

def get_peak_frame_data(frame_data, samples_num, frame_clip):
    samples_indices = range(-(samples_num // 2), -(samples_num // 2) + samples_num)

    # 上下のピッチでならす
    tmp_frame_data = {}
    for pitch, power in frame_data.items():
        frames = [frame_data[pitch + i] if pitch + i in frame_data else 0 for i in samples_indices]
        tmp_frame_data[pitch] = _clamp(max(frames), 0, 1) if frame_clip else max(frames)

    # ピークのみ抽出
    peak_frame_data = {}
    for pitch, power in tmp_frame_data.items():
        frames = [tmp_frame_data[pitch + i] if pitch + i in tmp_frame_data else 0 for i in samples_indices]
        peak_frame_data[pitch] = tmp_frame_data[pitch] if frames.count(power) == len(frames) else 0

    return peak_frame_data

@debug_args
def convert_to_midi_drums(output_path, input_path, bpm, resolution, threshold, segmentation, adjust_velocity, config: ProjectConfig):
    # 音声ファイルの読み込みと解析
    y, sr = librosa.load(input_path)
    y_normalized = librosa.util.normalize(y)
    C = np.abs(librosa.cqt(y_normalized, sr=sr))

    # MIDIファイルの作成
    midi_data = pretty_midi.PrettyMIDI(resolution=bpm * resolution, initial_tempo=bpm)

    # トラックを作成
    track = pretty_midi.Instrument(program=0, is_drum=True)

    # 曲の解析とノートイベントの追加
    start_times = {}
    start_powers = {}
    prev_drums_frame_data = {}
    frame_time = librosa.frames_to_time(1, sr=sr)

    # Define MIDI note numbers
    hh_note = 42
    sn_note = 38
    bd_note = 36
    ht_note = 50
    lt_note = 45
    ft_note = 41
    cy_note = 49
    hho_note = 46
    ride_note = 51
    lc_note = 52
    lp_note = 44
    lbd_note = 35

    max_velocities = {}

    for t, frame in enumerate(C.T):
        frame_data = {i + 24: power for i, power in enumerate(frame)}

        # ピークのみ抽出
        peak_frame_data = get_peak_frame_data(frame_data, 3, True)
        drums_frame_data = {}

        def get_peak_power(pitch_min, pitch_range):
            if pitch_range <= 0:
                return 0

            powers = [peak_frame_data[i] if i in peak_frame_data else 0 for i in range(pitch_min, pitch_min + pitch_range)]
            peak = np.mean(powers)
            if peak < threshold:
                return 0

            powers = [frame_data[i] if i in frame_data else 0 for i in range(pitch_min, pitch_min + pitch_range)]
            power = np.mean(powers) * adjust_velocity
            return power

        # バスドラ推定
        bd_power = get_peak_power(config.bd_min, config.bd_range)
        drums_frame_data[bd_note] = bd_power

        # フロアタム推定
        ft_power = get_peak_power(config.ft_min, config.ft_range)
        drums_frame_data[ft_note] = ft_power and bd_power == 0

        # ロータム推定
        lt_power = get_peak_power(config.lt_min, config.lt_range)
        drums_frame_data[lt_note] = lt_power and bd_power == 0 and ft_power == 0

        # ハイタム推定
        ht_power = get_peak_power(config.ht_min, config.ht_range)
        drums_frame_data[ht_note] = ht_power and bd_power == 0 and ft_power == 0 and lt_power == 0

        # スネア推定
        sn_power = get_peak_power(config.sn_min, config.sn_range)
        drums_frame_data[sn_note] = sn_power

        # notesを生成
        for pitch, power in drums_frame_data.items():
            prev_power = prev_drums_frame_data[pitch] if pitch in prev_drums_frame_data else 0

            if power > prev_power:
                if pitch not in start_times:
                    start_times[pitch] = t * frame_time

                start_powers[pitch] = power
            if power < prev_power * segmentation and pitch in start_times:
                start = start_times.pop(pitch)
                end = t * frame_time
                velocity = min(int(start_powers.pop(pitch) * 127), 127)
                max_velocities[pitch] = max(max_velocities.get(pitch, 0), velocity)
                note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
                track.notes.append(note)

        prev_drums_frame_data = drums_frame_data

    # チャンネルごとにノーマライズ
    for note in track.notes:
        note: pretty_midi.Note = note
        note.velocity = int(note.velocity / max_velocities.get(note.pitch, 0) * 127)

    # トラックをMIDIデータに追加
    midi_data.instruments.append(track)

    # MIDIファイルの保存
    midi_data.write(output_path)

    print(f"MIDI convert is complete. {output_path}")

@debug_args
def convert_to_midi_peak(output_path, input_path, bpm, resolution, threshold, segmentation, adjust_velocity):
    # 音声ファイルの読み込みと解析
    y, sr = librosa.load(input_path)
    y_normalized = librosa.util.normalize(y)
    C = np.abs(librosa.cqt(y_normalized, sr=sr))

    # MIDIファイルの作成
    midi_data = pretty_midi.PrettyMIDI(resolution=bpm * resolution, initial_tempo=bpm)

    # トラックを作成
    track = pretty_midi.Instrument(program=0, is_drum=False)

    # 曲の解析とノートイベントの追加
    for t, frame in enumerate(C.T):
        frame_data = {i + 24: power for i, power in enumerate(frame)}

        # ピークのみ抽出
        peak_frame_data = get_peak_frame_data(frame_data, 3, True)

        # notesを生成
        for pitch, power in peak_frame_data.items():
            if power > threshold:
                start = t * librosa.frames_to_time(1, sr=sr)
                end = (t + 1) * librosa.frames_to_time(1, sr=sr)
                velocity = min(int(power * 127), 127)
                note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
                track.notes.append(note)

    # トラックをMIDIデータに追加
    midi_data.instruments.append(track)

    # MIDIファイルの保存
    midi_data.write(output_path)

    print(f"MIDI convert is complete. {output_path}")

@debug_args
def convert_to_midi_cqt(output_path, input_path, bpm, resolution, threshold, segmentation, adjust_velocity):
    # 音声ファイルの読み込みと解析
    y, sr = librosa.load(input_path)
    y_normalized = librosa.util.normalize(y)
    C = np.abs(librosa.cqt(y_normalized, sr=sr))

    # MIDIファイルの作成
    midi_data = pretty_midi.PrettyMIDI(resolution=bpm * resolution, initial_tempo=bpm)

    # トラックを作成
    track = pretty_midi.Instrument(program=0, is_drum=False)

    # 曲の解析とノートイベントの追加
    for t, frame in enumerate(C.T):
        frame_data = {i + 24: power for i, power in enumerate(frame)}

        # notesを生成
        for pitch, power in frame_data.items():
            if power > threshold:
                start = t * librosa.frames_to_time(1, sr=sr)
                end = (t + 1) * librosa.frames_to_time(1, sr=sr)
                velocity = min(int(power * adjust_velocity * 127), 127)
                note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
                track.notes.append(note)

    # トラックをMIDIデータに追加
    midi_data.instruments.append(track)

    # MIDIファイルの保存
    midi_data.write(output_path)

    print(f"MIDI convert is complete. {output_path}")

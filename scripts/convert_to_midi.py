import librosa
from matplotlib import pyplot as plt
import pretty_midi
import numpy as np
from scipy.signal import butter, filtfilt

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
def convert_to_midi_drums(output_path, input_path, bpm, resolution, threshold, segmentation, hop_length, onset_delta, config: ProjectConfig):
    # 音声ファイルの読み込みと解析
    y, sr = librosa.load(input_path)
    y_normalized = librosa.util.normalize(y)
    C = np.abs(librosa.cqt(y_normalized, sr=sr, hop_length=hop_length))
    frame_time = librosa.frames_to_time(1, sr=sr, hop_length=hop_length)

    # onsetを検出
    onset_env = librosa.onset.onset_strength(y=y_normalized, sr=sr, hop_length=hop_length)
    onsets = set(librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, delta=onset_delta, hop_length=hop_length))

    # MIDIファイルの作成
    midi_data = pretty_midi.PrettyMIDI(resolution=bpm * resolution, initial_tempo=bpm)

    # トラックを作成
    track = pretty_midi.Instrument(program=0, is_drum=True)

    # 曲の解析とノートイベントの追加
    peak_times = {}
    start_powers = {}
    prev_drums_frame_data = {}

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
    used_onsets = set()

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
            power = np.mean(powers)
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
                peak_times[pitch] = t * frame_time
                start_powers[pitch] = power
            if power < prev_power * segmentation and pitch in peak_times:
                start = peak_times.pop(pitch)
                velocity = int(start_powers.pop(pitch) * 127)

                def get_onset(t):
                    for i in range(-2, 3):
                        if t + i in onsets:
                            return t + i
                    return None

                onset = get_onset(t)
                if onset is not None:
                    used_onsets.add(onset)

                end = start + frame_time
                max_velocities[pitch] = max(max_velocities.get(pitch, 0), velocity)
                note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
                track.notes.append(note)

        prev_drums_frame_data = drums_frame_data

    # ハイハット推定
    # onsetがあってノーツがない場合はハイハット扱い
    for onset in onsets:
        if onset not in used_onsets:
            pitch = hh_note
            start = onset * frame_time
            end = start + frame_time
            power = onset_env[onset]
            velocity = int(power * 127)
            max_velocities[pitch] = max(max_velocities.get(pitch, 0), velocity)
            note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
            track.notes.append(note)

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
def convert_to_midi_peak(output_path, input_path, bpm, resolution, threshold, segmentation, hop_length, onset_delta, test_duration):
    # 音声ファイルの読み込みと解析
    y, sr = librosa.load(input_path, duration=test_duration)
    y_normalized = librosa.util.normalize(y)
    C = np.abs(librosa.cqt(y_normalized, sr=sr, hop_length=hop_length))
    frame_time = librosa.frames_to_time(1, sr=sr, hop_length=hop_length)

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
                start = t * frame_time
                end = start + frame_time
                velocity = min(int(power * 127), 127)
                note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
                track.notes.append(note)

    # トラックをMIDIデータに追加
    midi_data.instruments.append(track)

    # MIDIファイルの保存
    midi_data.write(output_path)

    print(f"MIDI convert is complete. {output_path}")

@debug_args
def convert_to_midi_cqt(output_path, input_path, bpm, resolution, threshold, segmentation, hop_length, onset_delta, test_duration):
    # 音声ファイルの読み込みと解析
    y, sr = librosa.load(input_path, duration=test_duration)
    y_normalized = librosa.util.normalize(y)
    C = np.abs(librosa.cqt(y_normalized, sr=sr, hop_length=hop_length))
    frame_time = librosa.frames_to_time(1, sr=sr, hop_length=hop_length)

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
                start = t * frame_time
                end = start + frame_time
                velocity = min(int(power * 127), 127)
                note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
                track.notes.append(note)

    # トラックをMIDIデータに追加
    midi_data.instruments.append(track)

    # MIDIファイルの保存
    midi_data.write(output_path)

    print(f"MIDI convert is complete. {output_path}")

def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def apply_highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y

@debug_args
def output_onset_image(audio_file, output_image, hop_length, onset_delta, test_duration):
    # 音声ファイルの読み込み
    y, sr = librosa.load(audio_file, duration=test_duration)
    y_normalized = librosa.util.normalize(y)

    # ハイパスフィルタを適用
    #y_normalized = apply_highpass_filter(y_normalized, 512, sr)

    # メル周波数対数パワースペクトログラムの計算
    S = librosa.feature.melspectrogram(y=y_normalized, sr=sr, n_mels=128)
    S_dB = librosa.power_to_db(S, ref=np.max)

    # onsetを検出
    onset_env = librosa.onset.onset_strength(y=y_normalized, sr=sr, hop_length=hop_length)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, delta=onset_delta, hop_length=hop_length)

    # 時間軸を作成
    time_spectrogram = np.linspace(0, len(y_normalized) / sr, num=S_dB.shape[1])
    time_onset_env = np.linspace(0, len(y_normalized) / sr, num=len(onset_env))

    # onset envelopeとonsetを表示
    plt.figure(figsize=(60, 24))

    ax1 = plt.subplot(2, 1, 1)
    librosa.display.specshow(S_dB, x_coords=time_spectrogram, y_axis='mel', sr=sr, fmax=8000)
    plt.title('Mel spectrogram')

    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    plt.plot(time_onset_env, onset_env, label='Onset envelope')
    plt.vlines(time_onset_env[onsets], 0, onset_env.max(), color='r', alpha=0.9, linestyle='--', label='Onsets')
    plt.title('Onset Envelope and Detected Onsets')
    plt.xlabel('Time (s)')
    plt.legend()

    plt.tight_layout()

    # 画像として保存
    plt.savefig(output_image, dpi=100, bbox_inches='tight')

    # 画像を閉じる
    plt.close()

import librosa
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import pretty_midi
import numpy as np

from scripts.config_utils import ProjectConfig
from scripts.debug_utils import debug_args

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
def convert_to_midi_drums(
        output_path,
        input_path,
        offset,
        duration,
        bpm,
        resolution,
        threshold,
        segmentation,
        hop_length,
        onset_delta,
        onset_range_min,
        onset_range_max,
        velocity_max_percentile,
        config: ProjectConfig):
    # 音声ファイルの読み込みと解析
    y, sr = librosa.load(input_path, offset=offset, duration=duration)
    y_normalized = librosa.util.normalize(y)
    C = np.abs(librosa.cqt(y_normalized, sr=sr, hop_length=hop_length))
    frame_time = librosa.frames_to_time(1, sr=sr, hop_length=hop_length)

    # メル周波数対数パワースペクトログラムの計算
    S = librosa.feature.melspectrogram(y=y_normalized, sr=sr, n_mels=128, hop_length=hop_length)
    S_dB = librosa.power_to_db(S, ref=np.max)

    # onsetを検出
    onset_env = librosa.onset.onset_strength(S=S_dB, sr=sr)
    onsets = set(librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, delta=onset_delta, hop_length=hop_length))

    # MIDIファイルの作成
    midi_data = pretty_midi.PrettyMIDI(resolution=bpm * resolution, initial_tempo=bpm)

    # トラックを作成
    track = pretty_midi.Instrument(program=0, is_drum=True)

    # 曲の解析とノートイベントの追加
    start_frames = {}
    peak_frames = {}
    peak_powers = {}
    prev_drums_frame_data = {}

    velocities_map: dict[int, list[float]] = {}
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
        drums_frame_data[ft_note] = ft_power if bd_power == 0 else 0

        # ロータム推定
        lt_power = get_peak_power(config.lt_min, config.lt_range)
        drums_frame_data[lt_note] = lt_power if bd_power == 0 and ft_power == 0 else 0

        # ハイタム推定
        ht_power = get_peak_power(config.ht_min, config.ht_range)
        drums_frame_data[ht_note] = ht_power if bd_power == 0 and ft_power == 0 and lt_power == 0 else 0

        # スネア推定
        sn_power = get_peak_power(config.sn_min, config.sn_range)
        drums_frame_data[sn_note] = sn_power

        # notesを生成
        for pitch, power in drums_frame_data.items():
            prev_power = prev_drums_frame_data[pitch] if pitch in prev_drums_frame_data else 0
            peak_power = peak_powers[pitch] if pitch in peak_powers else 0

            if power > prev_power:
                if pitch not in start_frames:
                    start_frames[pitch] = t
                if power > peak_power:
                    peak_frames[pitch] = t
                    peak_powers[pitch] = power
            if power < prev_power * segmentation and pitch in peak_frames:
                start_frame = start_frames.pop(pitch)
                peak_frame = peak_frames.pop(pitch)
                velocity = peak_powers.pop(pitch)

                def get_onset(t):
                    for i in range(onset_range_min, onset_range_max):
                        if t + i in onsets:
                            return t + i
                    return None

                onset = get_onset(start_frame)
                if onset is not None:
                    used_onsets.add(onset)

                start = start_frame * frame_time
                end = start + frame_time
                note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
                track.notes.append(note)

                if pitch not in velocities_map:
                    velocities_map[pitch] = []
                velocities_map[pitch].append(velocity)

        prev_drums_frame_data = drums_frame_data

    # ハイハット推定
    # onsetがあってノーツがない場合はハイハット扱い
    for onset in onsets:
        if onset not in used_onsets:
            pitch = hh_note
            start = onset * frame_time
            end = start + frame_time
            power = onset_env[onset]
            velocity = power
            note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
            track.notes.append(note)

            if pitch not in velocities_map:
                velocities_map[pitch] = []
            velocities_map[pitch].append(velocity)

    # パーセンタイルで音量最大値を設定
    max_velocities = {}
    for pitch, velocities in velocities_map.items():
        max_velocities[pitch] = np.percentile(velocities, velocity_max_percentile)

    # チャンネルごとにノーマライズ
    for note in track.notes:
        note: pretty_midi.Note = note
        max_velocity = max_velocities.get(note.pitch, 0)
        note.velocity = _clamp(int(note.velocity / max_velocity * 127), 0, 127)

    # トラックをMIDIデータに追加
    midi_data.instruments.append(track)

    # MIDIファイルの保存
    midi_data.write(output_path)

    print(f"MIDI convert is complete. {output_path}")

@debug_args
def convert_to_midi_peak(
        output_path,
        input_path,
        bpm,
        resolution,
        threshold,
        hop_length,
        test_offset,
        test_duration):
    # 音声ファイルの読み込みと解析
    y, sr = librosa.load(input_path, offset=test_offset, duration=test_duration)
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
def convert_to_midi_cqt(
        output_path,
        input_path,
        bpm,
        resolution,
        threshold,
        hop_length,
        test_offset,
        test_duration):
    # 音声ファイルの読み込みと解析
    y, sr = librosa.load(input_path, offset=test_offset, duration=test_duration)
    y_normalized = librosa.util.normalize(y)
    C = np.abs(librosa.cqt(y_normalized, sr=sr, hop_length=hop_length))
    frame_time = librosa.frames_to_time(1, sr=sr, hop_length=hop_length)

    # MIDIファイルの作成
    midi_data = pretty_midi.PrettyMIDI(resolution=bpm * resolution, initial_tempo=bpm)

    # トラックを作成
    track = pretty_midi.Instrument(program=0, is_drum=False)

    # 曲の解析とノートイベントの追加
    velocities = []
    for t, frame in enumerate(C.T):
        frame_data = {i + 24: power for i, power in enumerate(frame)}

        # notesを生成
        for pitch, power in frame_data.items():
            if power > threshold:
                start = t * frame_time
                end = start + frame_time
                velocity = power
                note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
                track.notes.append(note)
                velocities.append(velocity)

    max_velocity = np.percentile(velocities, 90)

    # velocityを最大値に合わせて補正
    def fix_velocity(note: pretty_midi.Note):
        note.velocity = _clamp(int(note.velocity / max_velocity * 127), 0, 127)
        return note

    track.notes = [fix_velocity(note) for note in track.notes]

    # トラックをMIDIデータに追加
    midi_data.instruments.append(track)

    # MIDIファイルの保存
    midi_data.write(output_path)

    print(f"MIDI convert is complete. {output_path}")

from scripts.midi_to_dtx import channel_to_lane_id, pitch_to_channel, note_color_map

@debug_args
def output_test_image(
        audio_file,
        drum_midi_file,
        peak_midi_file,
        cqt_midi_file,
        output_image,
        hop_length,
        onset_delta,
        offset,
        duration,
        config: ProjectConfig):
    # 音声ファイルの読み込み
    y, sr = librosa.load(audio_file, offset=offset, duration=duration)
    y_normalized = librosa.util.normalize(y)

    # メル周波数対数パワースペクトログラムの計算
    S = librosa.feature.melspectrogram(y=y_normalized, sr=sr, n_mels=128, hop_length=hop_length)
    S_dB = librosa.power_to_db(S, ref=np.max)

    # onsetを検出
    onset_env = librosa.onset.onset_strength(S=S_dB, sr=sr)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, delta=onset_delta, hop_length=hop_length)

    # 時間軸を作成
    spectrogram_times = np.linspace(0, len(y_normalized) / sr, num=S_dB.shape[1])
    onset_env_times = np.linspace(0, len(y_normalized) / sr, num=len(onset_env))

    # 音程ライン作成
    pitch_lines_map = {
        bd_note: [config.bd_min - 0.5, config.bd_min + config.bd_range - 0.5],
        sn_note: [config.sn_min - 0.5, config.sn_min + config.sn_range - 0.5],
        ht_note: [config.ht_min - 0.5, config.ht_min + config.ht_range - 0.5],
        lt_note: [config.lt_min - 0.5, config.lt_min + config.lt_range - 0.5],
        ft_note: [config.ft_min - 0.5, config.ft_min + config.ft_range - 0.5],
    }

    def draw_pitch_lines():
        for pitch, lines in pitch_lines_map.items():
            channel = pitch_to_channel.get(pitch, 0)
            lane_id = channel_to_lane_id.get(channel, 0)
            color = note_color_map.get(lane_id, None)
            plt.hlines(lines, 0, duration, color=color, alpha=0.9, linestyle='--')

    min_pitch = min([lines[0] - 2 for lines in pitch_lines_map.values() if lines[0] > 0 and lines[1] > 0])
    max_pitch = max([lines[1] + 2 for lines in pitch_lines_map.values() if lines[0] > 0 and lines[1] > 0])

    # Set style color
    plt.style.use({
        'axes.facecolor': 'black',
        'axes.edgecolor': 'white',
        'axes.labelcolor': 'white',
        'xtick.color': 'white',
        'ytick.color': 'white',
        'axes.titlecolor': 'white',
        'figure.facecolor': 'black',
    })

    # onset envelopeとonsetを表示
    plt.figure(figsize=(60, 40))

    ax1 = plt.subplot(5, 1, 1)
    librosa.display.specshow(S_dB, x_coords=spectrogram_times, y_axis='mel', sr=sr, fmax=8000)
    plt.title('Mel spectrogram')

    ax2 = plt.subplot(5, 1, 2, sharex=ax1)
    plt.plot(onset_env_times, onset_env, label='Onset envelope')
    plt.vlines(onset_env_times[onsets], 0, onset_env.max(), color='r', alpha=0.9, linestyle='--', label='Onsets')
    plt.title('Onset Envelope and Detected Onsets')
    plt.legend()

    ax3 = plt.subplot(5, 1, 3, sharex=ax1)

    pm = pretty_midi.PrettyMIDI(cqt_midi_file)
    notes = []
    for instrument in pm.instruments:
        for note in instrument.notes:
            note: pretty_midi.Note = note
            color = (1, 0, 0, note.velocity / 127)
            notes.append((note.start, note.pitch, color))

    times, pitches, colors = zip(*notes)
    plt.scatter(times, pitches, c=colors, marker='s')

    draw_pitch_lines()

    ax3.set_ylim(min_pitch, max_pitch)
    plt.ylabel('Pitch')
    plt.title('CQT')

    ax4 = plt.subplot(5, 1, 4, sharex=ax1)

    pm = pretty_midi.PrettyMIDI(peak_midi_file)
    pitches = []
    for instrument in pm.instruments:
        for note in instrument.notes:
            note: pretty_midi.Note = note
            color = (1, 0, 0, note.velocity / 127)
            notes.append((note.start, note.pitch, color))

    times, pitches, colors = zip(*notes)
    plt.scatter(times, pitches, c=colors, marker='s')

    draw_pitch_lines()

    ax4.set_ylim(min_pitch, max_pitch)
    plt.ylabel('Pitch')
    plt.title('CQT Peak')

    ax5 = plt.subplot(5, 1, 5, sharex=ax1)

    pm = pretty_midi.PrettyMIDI(drum_midi_file)
    for instrument in pm.instruments:
        for note in instrument.notes:
            note: pretty_midi.Note = note
            channel = pitch_to_channel.get(note.pitch, 0)
            lane_id = channel_to_lane_id.get(channel, 0)
            color = note_color_map.get(lane_id, None)
            alpha = note.velocity / 127
            rect = Rectangle((note.start, lane_id - 0.5), note.end - note.start, 1, facecolor=color, alpha=alpha, edgecolor='white', linewidth=0.5)
            ax5.add_patch(rect)

    plt.vlines(onset_env_times[onsets], 0, onset_env.max(), color='r', alpha=0.9, linestyle='--', label='Onsets')

    ax5.set_ylim(0, 11)
    plt.xlabel('Time (seconds)')
    plt.ylabel('Lane')
    plt.title('Drum Notes')

    plt.tight_layout()

    # 画像として保存
    plt.savefig(output_image, dpi=100, bbox_inches='tight')

    # 画像を閉じる
    plt.close()

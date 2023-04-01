from dataclasses import dataclass
import numpy as np
import pretty_midi
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import japanize_matplotlib

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

# Define DTX channels
hh_channel = '11'
sn_channel = '12'
bd_channel = '13'
ht_channel = '14'
lt_channel = '15'
ft_channel = '17'
cy_channel = '16'
hho_channel = '18'
ride_channel = '19'
lc_channel = '1A'
lp_channel = '1B'
lbd_channel = '1C'

bgm_channel = '01'
video_channel = '54'

channel_to_lane_id = {
    hh_channel : 2,
    sn_channel : 4,
    bd_channel : 6,
    ht_channel : 5,
    lt_channel : 7,
    ft_channel : 8,
    cy_channel : 9,
    hho_channel : 2,
    ride_channel : 10,
    lc_channel : 1,
    lp_channel : 3,
    lbd_channel : 3,
}

pitch_to_channel = {
    hh_note: hh_channel,
    sn_note: sn_channel,
    bd_note: bd_channel,
    ht_note: ht_channel,
    lt_note: lt_channel,
    ft_note: ft_channel,
    cy_note: cy_channel,
    hho_note: hho_channel,
    ride_note: ride_channel,
    lc_note: lc_channel,
    lp_note: lp_channel,
    lbd_note: lbd_channel,
}

note_color_map = {
    1: "red",
    2: "skyblue",
    3: "pink",
    4: "yellow",
    5: "lightgreen",
    6: "violet",
    7: "red",
    8: "orange",
    9: "skyblue",
    10: "skyblue",
}

@dataclass
class DtxInfo:
    TITLE: str = "Sample Music"
    ARTIST: str = ""
    COMMENT: str = ""
    PREVIEW: str = "pre.ogg"
    PREIMAGE: str = "pre.jpg"
    BGM: str = "bgm.ogg"
    VIDEO: str = "movie.mp4"
    BPM: float = 120.0
    DLEVEL: int = 50

    HHC_WAV: str = "chips\\close.xa"
    SNARE_WAV: str = "chips\\snare.xa"
    BD_WAV: str = "chips\\bd.xa"
    HT_WAV: str = "chips\\high.xa"
    LT_WAV: str = "chips\\low.xa"
    CYMBAL_WAV: str = "chips\\cymbal.xa"
    FT_WAV: str = "chips\\floor.xa"
    HHO_WAV: str = "chips\\open.xa"
    RIDE_WAV: str = "chips\\ride.xa"
    LC_WAV: str = "chips\\lc.xa"
    LP_WAV: str = "chips\\lp.xa"
    LBD_WAV: str = "chips\\lbd.xa"

    HHC_VOLUME: int = 100
    SNARE_VOLUME: int = 100
    BD_VOLUME: int = 100
    HT_VOLUME: int = 100
    LT_VOLUME: int = 100
    CYMBAL_VOLUME: int = 100
    FT_VOLUME: int = 100
    HHO_VOLUME: int = 100
    RIDE_VOLUME: int = 100
    LC_VOLUME: int = 100
    LP_VOLUME: int = 100
    LBD_VOLUME: int = 100

    HHC_OFFSET: float = 0.0
    SNARE_OFFSET: float = 0.0
    BD_OFFSET: float = 0.0
    HT_OFFSET: float = 0.0
    LT_OFFSET: float = 0.0
    CYMBAL_OFFSET: float = 0.0
    FT_OFFSET: float = 0.0
    HHO_OFFSET: float = 0.0
    RIDE_OFFSET: float = 0.0
    LC_OFFSET: float = 0.0
    LP_OFFSET: float = 0.0
    LBD_OFFSET: float = 0.0

    CHIP_RESOLUTION: int = 32
    BGM_RESOLUTION: int = 128
    SHIFT_TIME: float = 0.0
    AUTO_SHIFT_TIME: bool = True
    ALIGN_NTH_BD: int = 1
    AUTO_ALIGN_NTH_BD: bool = True
    BGM_OFFSET_TIME: float = 0
    BGM_VOLUME: int = 100
    WAV_SPLITS: int = 4
    WAV_VOLUME: int = 80

@dataclass
class DtxChip:
    channel: str = ""
    time: float = 0.0
    measure_pos: int = 0
    beat_pos: int = 0
    resolution: int = 0
    velocity: int = 0
    wav_number: int = 0

def _clamp(n, smallest, largest):
    return sorted([smallest, n, largest])[1]

def auto_shift_time(bd_notes, chip_timings_list, dtx_info: DtxInfo, measure_time):
    beat_pos_zero_count_list = []
    nth_bd_start = bd_notes[dtx_info.ALIGN_NTH_BD - 1].start if dtx_info.ALIGN_NTH_BD > 0 else 0
    for i in range(0, 20):
        auto_shift_time = (i - 10) * 0.01 + measure_time * (nth_bd_start // measure_time + 1) - nth_bd_start
        beat_pos_zero_count = 0

        for current_time, next_time, current_measure, beat_pos in chip_timings_list:
            if beat_pos != 0:
                continue

            for note in bd_notes:
                if note.start + auto_shift_time >= current_time and note.start + auto_shift_time < next_time:
                    beat_pos_zero_count += 1

        beat_pos_zero_count_list.append(beat_pos_zero_count)

    index = int(np.argmax(beat_pos_zero_count_list))
    best_shift_time = (index - 10) * 0.01
    best_zero_count = beat_pos_zero_count_list[index]

    print(f"beat_pos_zero_count_list: {beat_pos_zero_count_list}")
    print(f"best shift_time: {best_shift_time}")

    return best_shift_time, best_zero_count

#@debug_args
def drum_notes_to_image(
        notes,
        output_image_path,
        total_duration,
        bpm,
        measure_y_count,
        chip_resolution,
        image_width,
        image_height,
        title):

    measure_time = 60 * 4 / float(bpm) # 1小節の時間
    time_interval = measure_time * measure_y_count
    grid_interval = measure_time

    # Calculate the number of subplots needed
    num_subplots = int(total_duration / time_interval) + 1
    
    # Calculate dpi for custom image size
    dpi = 100
    width = image_width / dpi
    height = image_height / dpi

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

    # Create subplots with custom width and height
    fig, axes = plt.subplots(1, num_subplots, sharey=True, figsize=(width * num_subplots, height), dpi=dpi)

    fig.suptitle(f"{title} / BPM {bpm}", color="white")

    for i, ax in enumerate(axes):
        # Set the range of the x-axis (pitch) and y-axis (time)
        ax.set_xlim(0, 11)
        ax.set_ylim(0, time_interval)

    # Plot notes with specified colors and transparency based on velocity in each subplot
    for time, channel, velocity in notes:
        start_time = time
        end_time = time + grid_interval / chip_resolution
        lane_id = channel_to_lane_id.get(channel, 0)
        subplot_idx = int(start_time // time_interval)
        relative_start_time = start_time % time_interval
        relative_end_time = end_time % time_interval
        color = note_color_map.get(lane_id, None)
        alpha = velocity / 127

        if color is not None:
            rect_duration = relative_end_time - relative_start_time
            if rect_duration < 0:
                rect_duration = time_interval - relative_start_time
            rect = Rectangle((lane_id - 0.5, relative_start_time), 1, rect_duration, edgecolor='white', facecolor=color, alpha=alpha, linewidth=0.5)
            axes[subplot_idx].add_patch(rect)

    for i, ax in enumerate(axes):
        ax.set_title(f"{i * measure_y_count + 1} - {(i + 1) * measure_y_count}")

        # Draw grid lines
        for t in np.arange(0, time_interval + grid_interval, grid_interval):
            ax.axhline(t, color='gray', linestyle='--', linewidth=0.5)

        ax.set_yticklabels([])
        ax.set_xticks([])

    # Save plot as an image
    plt.tight_layout()
    plt.savefig(output_image_path, dpi=dpi)

    print(f"Generation of Notes image is complete. {output_image_path}")

@debug_args
def midi_to_dtx(midi_file, output_path, output_image_path, dtx_info: DtxInfo):
    pm = pretty_midi.PrettyMIDI(midi_file)

    # Initialize defaultdict
    dtx_data = defaultdict(lambda: '00' * dtx_info.CHIP_RESOLUTION)

    pitch_list = list(pitch_to_channel.keys())

    measure_time = 60 * 4 / float(dtx_info.BPM) # 1小節の時間
    max_measure = int(pm.get_end_time() / measure_time) + 1 # 最大小節数
    shift_time = dtx_info.SHIFT_TIME

    note_offsets = {
        hh_note: dtx_info.HHC_OFFSET,
        sn_note: dtx_info.SNARE_OFFSET,
        bd_note: dtx_info.BD_OFFSET,
        ht_note: dtx_info.HT_OFFSET,
        lt_note: dtx_info.LT_OFFSET,
        ft_note: dtx_info.FT_OFFSET,
        cy_note: dtx_info.CYMBAL_OFFSET,
        hho_note: dtx_info.HHO_OFFSET,
        ride_note: dtx_info.RIDE_OFFSET,
        lc_note: dtx_info.LC_OFFSET,
        lp_note: dtx_info.LP_OFFSET,
        lbd_note: dtx_info.LBD_OFFSET,
    }

    # Collect notes and adjust offset
    notes: list[pretty_midi.Note] = []
    for instrument in pm.instruments:
        for note in instrument.notes:
            note: pretty_midi.Note = note
            offset = note_offsets.get(note.pitch, 0)
            if offset != 0:
                note.start += offset
                note.end += offset
            notes.append(note)

    # Collect bd_notes
    bd_notes = [note for note in notes if note.pitch == bd_note]
    bd_notes.sort(key=lambda note: note.start)

    def calculate_timings_list(max_measure, measure_time, resolution):
        timings_list = []

        for i in range(max_measure * resolution):
            current_time = measure_time / resolution * i
            next_time = measure_time / resolution * (i + 1)
            current_measure = int(i / resolution) + 1
            beat_pos = int(i % resolution)

            timings_list.append((current_time, next_time, current_measure, beat_pos))

        return timings_list

    chip_timings_list = calculate_timings_list(max_measure, measure_time, dtx_info.CHIP_RESOLUTION)
    bgm_timings_list = calculate_timings_list(max_measure, measure_time, dtx_info.BGM_RESOLUTION)

    if dtx_info.AUTO_ALIGN_NTH_BD:
        beat_pos_zero_count_list = []
        for i in range(0, 5):
            dtx_info.ALIGN_NTH_BD = i + 1
            _, zero_count = auto_shift_time(bd_notes, chip_timings_list, dtx_info, measure_time)
            beat_pos_zero_count_list.append(zero_count)

        dtx_info.ALIGN_NTH_BD = int(np.argmax(beat_pos_zero_count_list)) + 1

        print(f"beat_pos_zero_count_list: {beat_pos_zero_count_list}")
        print(f"best align_nth_bd: {dtx_info.ALIGN_NTH_BD}")

    if dtx_info.AUTO_SHIFT_TIME:
        dtx_info.SHIFT_TIME, zero_count = auto_shift_time(bd_notes, chip_timings_list, dtx_info, measure_time)
        shift_time = dtx_info.SHIFT_TIME

    if dtx_info.ALIGN_NTH_BD > 0:
        if len(bd_notes) >= dtx_info.ALIGN_NTH_BD:
            nth_bd_start = bd_notes[dtx_info.ALIGN_NTH_BD - 1].start
            shift_time += measure_time * (nth_bd_start // measure_time + 1) - nth_bd_start

    def get_wav_number(pitch, velocity):
        try:
            index = pitch_list.index(pitch)
        except ValueError:
            return 0

        offset = index * dtx_info.WAV_SPLITS + 2
        split_velocity = 128 // dtx_info.WAV_SPLITS
        wav_num = _clamp((velocity - 1) // split_velocity + 1, 0, dtx_info.WAV_SPLITS - 1)

        return offset + wav_num

    dtx_chips: list[DtxChip] = []

    # Convert bgm, video to dtx_chips
    for current_time, next_time, current_measure, beat_pos in bgm_timings_list:
        if current_time >= shift_time + dtx_info.BGM_OFFSET_TIME:
            dtx_chip_bgm = DtxChip(
                channel=bgm_channel,
                time=current_time,
                measure_pos=current_measure,
                beat_pos=beat_pos,
                resolution=dtx_info.BGM_RESOLUTION,
                wav_number=1
            )
            dtx_chips.append(dtx_chip_bgm)

            dtx_chip_video = DtxChip(
                channel=video_channel,
                time=current_time,
                measure_pos=current_measure,
                beat_pos=beat_pos,
                resolution=dtx_info.BGM_RESOLUTION,
                wav_number=1
            )
            dtx_chips.append(dtx_chip_video)
            break

    # Convert notes to dtx_chips
    for current_time, next_time, current_measure, beat_pos in chip_timings_list:
        for note in notes:
            if note.start + shift_time >= current_time and note.start + shift_time < next_time:
                channel = pitch_to_channel.get(note.pitch)
                if channel:
                    wav_number = get_wav_number(note.pitch, note.velocity)
                    dtx_chip = DtxChip(
                        channel=channel,
                        time=current_time,
                        measure_pos=current_measure,
                        beat_pos=beat_pos,
                        resolution=dtx_info.CHIP_RESOLUTION,
                        velocity=note.velocity,
                        wav_number=wav_number
                    )
                    dtx_chips.append(dtx_chip)

    # Convert dtx_chips to dtx_data
    for dtx_chip in dtx_chips:
        measure_pos_str = str(dtx_chip.measure_pos).zfill(3)
        channel_key = measure_pos_str + dtx_chip.channel

        # Ensure the length of the dtx_data string is correct for the resolution
        if len(dtx_data[channel_key]) != dtx_chip.resolution * 2:
            dtx_data[channel_key] = '00' * dtx_chip.resolution

        # Convert the WAV number to hexadecimal
        wav_number_str = np.base_repr(dtx_chip.wav_number, 36).rjust(2, "0")
        dtx_data[channel_key] = dtx_data[channel_key][:dtx_chip.beat_pos * 2] + wav_number_str + dtx_data[channel_key][(dtx_chip.beat_pos + 1) * 2:]

    # Generate DTX format text
    dtx_text = f"""; Created by TubeDTX

#TITLE: {dtx_info.TITLE}
#ARTIST: {dtx_info.ARTIST}
#COMMENT: {dtx_info.COMMENT}
#PREVIEW: {dtx_info.PREVIEW}
#PREIMAGE: {dtx_info.PREIMAGE}
#BPM: {dtx_info.BPM}
#DLEVEL: {dtx_info.DLEVEL}

"""

    # Add WAV and VOLUME commands
    dtx_text += f"""
#WAV01: {dtx_info.BGM}
#VOLUME01: {dtx_info.BGM_VOLUME}
#BGMWAV: 01
"""

    wav_splits = dtx_info.WAV_SPLITS
    wav_names = [
        dtx_info.HHC_WAV,
        dtx_info.SNARE_WAV,
        dtx_info.BD_WAV,
        dtx_info.HT_WAV,
        dtx_info.LT_WAV,
        dtx_info.FT_WAV,
        dtx_info.CYMBAL_WAV,
        dtx_info.HHO_WAV,
        dtx_info.RIDE_WAV,
        dtx_info.LC_WAV,
        dtx_info.LP_WAV,
        dtx_info.LBD_WAV,
    ]
    wav_volumes = [
        dtx_info.HHC_VOLUME,
        dtx_info.SNARE_VOLUME,
        dtx_info.BD_VOLUME,
        dtx_info.HT_VOLUME,
        dtx_info.LT_VOLUME,
        dtx_info.FT_VOLUME,
        dtx_info.CYMBAL_VOLUME,
        dtx_info.HHO_VOLUME,
        dtx_info.RIDE_VOLUME,
        dtx_info.LC_VOLUME,
        dtx_info.LP_VOLUME,
        dtx_info.LBD_VOLUME,
    ]
    wav_volumes = [v * dtx_info.WAV_VOLUME / 100 for v in wav_volumes]
    for i in range(0, wav_splits * len(wav_names)):
        group_index = i // wav_splits
        wav_name = wav_names[group_index]
        wav_volume = wav_volumes[group_index]
        wav_number_str = np.base_repr(i + 2, 36).rjust(2, "0")
        dtx_text += f"#WAV{wav_number_str}: {wav_name}\n"
        dtx_text += f"#VOLUME{wav_number_str}: {int((wav_volume / wav_splits) * (i % wav_splits + 1))}\n"

    dtx_text += f"""
#AVI01: {dtx_info.VIDEO}

"""

    for key in sorted(dtx_data.keys()):
        dtx_text += f"#{key}: {dtx_data[key]}\n"

    # Save dtx text
    with open(output_path, 'w', encoding='shift_jis', errors='ignore') as f:
        f.write(dtx_text)

    # Generate image
    if output_image_path is not None:
        notes = [(chip.time, chip.channel, chip.velocity) for chip in dtx_chips]
        drum_notes_to_image(
            notes=notes,
            output_image_path=output_image_path,
            total_duration=pm.get_end_time(),
            bpm=dtx_info.BPM,
            measure_y_count=10,
            chip_resolution=dtx_info.CHIP_RESOLUTION,
            image_width=128,
            image_height=1024,
            title=dtx_info.TITLE)

    print(f"MIDI to DTX is complete. {output_path}")

    return dtx_text

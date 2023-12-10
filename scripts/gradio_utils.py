from contextlib import nullcontext
from dataclasses import asdict
import datetime
import multiprocessing as mp
import os
import shutil
import traceback
import gradio as gr
import requests

from scripts.config_utils import AppConfig, ProjectConfig, DevConfig
from scripts.convert_to_midi_with_onsets_frames import convert_to_midi_with_onsets_frames
from scripts.debug_utils import debug_args
from scripts.media_utils import convert_audio, create_preview_audio, crop_copy_video, download_video, extract_audio, get_tmp_dir, get_tmp_file_path, get_video_info, resize_image, trim_and_crop_video
from scripts.music_utils import compute_bpm, compute_chorus_time
from scripts.convert_to_midi import convert_to_midi_cqt, convert_to_midi_drums, convert_to_midi_peak, output_test_image
from scripts.midi_to_dtx import midi_to_dtx
from scripts.platform_utils import force_copy_file, get_audio_path, get_folder_path, get_video_path, safe_remove_file
from scripts.separate_music import separate_music

app_config = AppConfig.instance()
dev_config = DevConfig.instance()

@debug_args
def auto_save(config: ProjectConfig, project_path: str):
    if not app_config.auto_save:
        return ""

    config.save(project_path)

    timestr = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    config_path = ProjectConfig.get_config_path(project_path)
    output_log = f"[{timestr}] 譜面設定のセーブをしました。\n{config_path}"
    return output_log

@debug_args
def select_workspace_gr():
    workspace_path = get_folder_path(app_config.workspace_path)
    if workspace_path == '':
        raise Exception("Workspaceを選択してください")

    app_config.workspace_path = workspace_path
    app_config.save(".")

    output_log = f"Workspaceを開きました。{workspace_path}\n\n"

    return [output_log, workspace_path]

@debug_args
def select_project_gr(evt: gr.SelectData):
    project_paths = app_config.get_project_paths()

    if evt.index >= len(project_paths):
        raise Exception(f"選択している譜面が見つかりません。 {evt.indexs}")

    project_path = project_paths[evt.index]
    config = ProjectConfig.load(project_path)

    app_config.project_path = project_path
    app_config.save(".")

    output_log = f"譜面をロードしました。\n\n{ProjectConfig.get_config_path(project_path)}\n\n"

    return [
        output_log,
        project_path,
        app_config.get_current_preimage(),
        app_config.get_current_movie(),
        *asdict(config).values(),
        *([None] * 13),
    ]

@debug_args
def new_score_gr(url: str):
    if not os.path.exists(app_config.workspace_path):
        raise Exception(f"Workspaceが選択されていません。")

    if url == "":
        raise Exception(f"URLが入力されていません。")

    title, thumbnail_url = get_video_info(url)

    new_score_name = title.translate(str.maketrans({
        '/': '-',
        '\\': '-',
        '¥': '-',
        ':': '-',
        '*': '-',
        '”': '-',
        '|': '-',
    }))

    project_path = os.path.join(app_config.workspace_path, new_score_name)
    if os.path.exists(project_path):
        raise Exception(f"すでに同名ディレクトリが存在しています。 {project_path}")

    os.mkdir(project_path)

    config = ProjectConfig.load(project_path)
    config.movie_url = url
    config.save(project_path)

    # サムネDL
    thumbnail_file_name = config.movie_thumbnail_file_name2
    thumbnail_path = os.path.join(project_path, thumbnail_file_name)

    response = requests.get(thumbnail_url)
    with open(thumbnail_path, "wb") as file:
        file.write(response.content)

    thumbnail_width = app_config.thumbnail_width
    thumbnail_height = app_config.thumbnail_height

    resize_image(thumbnail_path, thumbnail_path, (thumbnail_width, thumbnail_height))

    app_config.project_path = project_path
    app_config.save(".")

    output_log = f"譜面ディレクトリを新規作成しました。\n"
    output_log += f'"1. Download Movie"タブから処理を開始してください。\n\n'

    output_log += f"title: {new_score_name}\n\n"

    return [output_log, project_path, app_config.get_current_preimage(), *asdict(config).values()]

@debug_args
def reload_workspace_gr():
    gallery = app_config.get_all_gallery()
    if len(gallery) == 0:
        raise Exception("譜面が見つかりません。")

    return gallery

@debug_args
def _batch_convert_gr(lock: mp.Lock, project_path):
    config = ProjectConfig.load(project_path)

    base_output_log = ""
    output_log = ""

    def check_converted(file_name):
        output_path = os.path.join(project_path, file_name)
        return app_config.batch_skip_converted and os.path.exists(output_path)

    try:
        if app_config.batch_download_movie:
            if not check_converted(config.get_fixed_download_file_name()):
                outputs = download_video_gr(*app_config.to_dict().values(), *config.to_dict().values(), project_path=project_path)
                config = ProjectConfig.load(project_path)
                base_output_log = outputs[0]
                output_log += outputs[1]

        if app_config.batch_convert_movie:
            if not check_converted(config.bgm_name):
                outputs = convert_video_gr(*app_config.to_dict().values(), *config.to_dict().values(), project_path=project_path)
                config = ProjectConfig.load(project_path)
                base_output_log = outputs[0]
                output_log += outputs[1]

        if app_config.batch_create_preview:
            if not check_converted(config.preview_output_name):
                outputs = create_preview_gr(*config.to_dict().values(), project_path=project_path)
                config = ProjectConfig.load(project_path)
                base_output_log = outputs[0]
                output_log += outputs[1]

        if app_config.batch_separate_music:
            if not check_converted("drums.wav"):
                outputs = separate_music_gr(*app_config.to_dict().values(), *config.to_dict().values(), project_path=project_path, lock=lock)
                config = ProjectConfig.load(project_path)
                base_output_log = outputs[0]
                output_log += outputs[1]

        if app_config.batch_convert_to_midi:
            if not check_converted("drums.mid"):
                outputs = convert_to_midi_gr(*app_config.to_dict().values(), *config.to_dict().values(), project_path=project_path)
                config = ProjectConfig.load(project_path)
                base_output_log = outputs[0]
                output_log += outputs[1]

        if app_config.batch_convert_to_dtx:
            if not check_converted(config.dtx_output_name):
                outputs = midi_to_dtx_gr(*config.to_dict().values(), project_path=project_path)
                config = ProjectConfig.load(project_path)
                base_output_log = outputs[0]
                output_log += outputs[1]
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        output_log = f"[失敗] {config.dtx_title}\n\n"
        output_log += f"{str(e)}\n{traceback.format_exc()}\n\n"
    else:
        if output_log != "":
            output_log = f"[成功] {config.dtx_title}\n\n"

    return [base_output_log, output_log, *config.to_dict().values()]

@debug_args
def batch_convert_selected_score_gr(*args):
    app_config.update(*args)
    app_config.save(".")

    lock = mp.Manager().Lock()
    outputs = _batch_convert_gr(lock, app_config.project_path)

    outputs[1] += f"==============================\n\n"
    outputs[1] += "全てのバッチ処理が完了しました。\n\n"

    return outputs

@debug_args
def batch_convert_all_score_gr(*args):
    app_config.update(*args)
    app_config.save(".")

    project_paths = app_config.get_project_paths()

    base_output_log = ""
    output_log = ""

    pool = mp.Pool(app_config.batch_jobs)
    lock = mp.Manager().Lock()
    result = pool.starmap(_batch_convert_gr, [(lock, p) for p in project_paths])

    index = project_paths.index(app_config.project_path)
    base_output_log = result[index][0]

    for outputs in result:
        output_log += outputs[1]

    output_log += f"==============================\n\n"
    output_log += "全てのバッチ処理が完了しました。\n\n"

    config = ProjectConfig.load(app_config.project_path)

    return [base_output_log, output_log, *config.to_dict().values()]

@debug_args
def _download_video_gr(config: ProjectConfig, project_path):
    url = config.movie_url
    output_file_name = config.get_fixed_download_file_name()
    thumbnail_file_name = config.movie_thumbnail_file_name2
    thumbnail_width = app_config.thumbnail_width
    thumbnail_height = app_config.thumbnail_height
    downloader = app_config.downloader

    if url == "":
        raise Exception("URLを入力してください。")

    output_path = os.path.join(project_path, output_file_name)
    thumbnail_path = os.path.join(project_path, thumbnail_file_name)

    comment, title, artist, duration, width, height = download_video(
        url,
        output_path,
        thumbnail_path,
        (thumbnail_width, thumbnail_height),
        downloader)

    config.dtx_title = title
    config.dtx_artist = artist
    config.dtx_comment = comment

    output_log = "動画のダウンロードに成功しました。\n"
    output_log += '"2. Create Preview File"タブに進んでください。\n\n'

    output_log += f"title: {title}\n"
    output_log += f"artist: {artist}\n"
    output_log += f"duration: {duration}\n"
    output_log += f"dimensions: {width} x {height}\n\n"

    base_output_log = auto_save(config, project_path)

    return [base_output_log, output_log, output_path, None, None, title, artist, comment, thumbnail_path]

@debug_args
def _convert_video_gr(config: ProjectConfig, project_path):
    input_file_name = config.get_fixed_download_file_name()
    output_file_name = config.movie_output_file_name
    bgm_file_name = config.bgm_name
    start_time = config.movie_start_time
    end_time = config.movie_end_time
    width = config.movie_width
    height = config.movie_height
    target_dbfs = config.movie_target_dbfs if config.movie_target_dbfs < 0 else app_config.default_dbfs
    bitrate = app_config.bgm_bitrate

    input_path = os.path.join(project_path, input_file_name)
    output_path = os.path.join(project_path, output_file_name)
    bgm_path = os.path.join(project_path, bgm_file_name)

    if os.path.exists(output_path):
        os.remove(output_path)

    output_path = trim_and_crop_video(input_path, output_path, start_time, end_time, width, height, bitrate)
    extract_audio(output_path, bgm_path, target_dbfs, bitrate)

    output_log = "動画の処理に成功しました。\n"
    output_log += '"2. Create Preview File"タブに進んでください。\n\n'

    base_output_log = auto_save(config, project_path)

    return [base_output_log, output_log, input_path, output_path, bgm_path]

@debug_args
def parse_args(*args, project_path=None):
    app_config.update(*(args[:AppConfig.get_parameters_size()]))
    app_config.save(".")

    project_path = project_path or app_config.project_path
    config = ProjectConfig(*(args[AppConfig.get_parameters_size():]))

    return config, project_path

@debug_args
def download_and_convert_video_gr(*args, project_path=None):
    config, project_path = parse_args(*args, project_path=project_path)

    download_outputs = _download_video_gr(config, project_path)

    outputs = _convert_video_gr(config, project_path)

    outputs[1] = download_outputs[1] + outputs[1]
    outputs.append(download_outputs[5])
    outputs.append(download_outputs[6])
    outputs.append(download_outputs[7])
    outputs.append(download_outputs[8])

    return outputs

@debug_args
def download_video_gr(*args, project_path=None):
    config, project_path = parse_args(*args, project_path=project_path)

    outputs = _download_video_gr(config, project_path)

    return outputs

@debug_args
def convert_video_gr(*args, project_path=None):
    config, project_path = parse_args(*args, project_path=project_path)

    outputs = _convert_video_gr(config, project_path)

    return outputs

@debug_args
def reload_video_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    input_file_name = config.get_fixed_download_file_name()
    output_file_name = config.movie_output_file_name
    bgm_file_name = config.bgm_name

    input_path = os.path.join(project_path, input_file_name)
    output_path = os.path.join(project_path, output_file_name)
    bgm_path = os.path.join(project_path, bgm_file_name)

    output_path = output_path if os.path.exists(output_path) else None
    bgm_path = bgm_path if os.path.exists(bgm_path) else None

    output_log = "表示を更新しました。\n\n"

    base_output_log = auto_save(config, project_path)

    return [base_output_log, output_log, input_path, output_path, bgm_path]

@debug_args
def create_preview_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    input_file_name = config.bgm_name
    output_file_name = config.preview_output_name
    start_time = config.preview_start_time
    preview_time = config.preview_duration
    fade_in_duration = config.preview_fade_in_duration
    fade_out_duration = config.preview_fade_out_duration
    bitrate = app_config.bgm_bitrate

    input_path = os.path.join(project_path, input_file_name)
    output_path = os.path.join(project_path, output_file_name)

    output_log = "プレビューの作成に成功しました。\n"
    output_log += '"3. Separate Music"タブに進んでください。\n\n'

    if start_time == 0.0:
        start_time = compute_chorus_time(input_path)
        config.preview_start_time = start_time
        output_log += f"start time: {start_time}\n\n"

    create_preview_audio(
        input_path,
        output_path,
        start_time,
        preview_time,
        fade_in_duration,
        fade_out_duration,
        bitrate,
    )

    base_output_log = auto_save(config, project_path)

    return [base_output_log, output_log, input_path, output_path, start_time]

@debug_args
def reload_preview_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    input_file_name = config.bgm_name
    output_file_name = config.preview_output_name

    input_path = os.path.join(project_path, input_file_name)
    output_path = os.path.join(project_path, output_file_name)
    output_path = output_path if os.path.exists(output_path) else None

    output_log = "表示を更新しました。\n\n"

    base_output_log = auto_save(config, project_path)

    return [base_output_log, output_log, input_path, output_path]

@debug_args
def separate_music_gr(*args, project_path=None, lock: mp.Lock=None):
    config, project_path = parse_args(*args, project_path=project_path)

    model = app_config.separate_model
    jobs = app_config.separate_jobs
    input_file = config.bgm_name
    output_file = config.midi_input_name2
    bitrate = app_config.bgm_bitrate

    input_path = os.path.join(project_path, input_file)
    output_path = os.path.join(project_path, output_file)

    if not os.path.exists(input_path):
        raise Exception(f"BGMが見つかりません。 {input_path}")

    with lock if lock is not None else nullcontext():
        output_files = separate_music(model, input_path, project_path, jobs, drums_only=True)

    # 音声の変換
    convert_audio(output_files[0], output_path, bitrate)
    safe_remove_file(output_files[0])

    bpm = compute_bpm(output_path)
    config.dtx_bpm = bpm

    output_log = "ドラム音の分離に成功しました。\n"
    output_log += '"4. Convert to MIDI"タブに進んでください。\n\n'
    output_log += f"bpm: {bpm}\n\n"

    base_output_log = auto_save(config, project_path)

    return [base_output_log, output_log, output_path, bpm]

@debug_args
def _convert_to_midi_gr(*args, project_path=None, is_test=False):
    config, project_path = parse_args(*args, project_path=project_path)

    input_file_name = config.midi_input_name2
    resolution = config.midi_resolution
    threshold = config.midi_threshold
    segmentation = config.midi_segmentation
    hop_length = config.midi_hop_length
    onset_delta = config.midi_onset_delta
    disable_hh_frame = config.midi_disable_hh_frame
    adjust_offset_count = config.midi_adjust_offset_count
    adjust_offset_min = config.midi_adjust_offset_min
    adjust_offset_max = config.midi_adjust_offset_max
    velocity_max_percentile = config.midi_velocity_max_percentile
    bpm = config.dtx_bpm
    convert_model = app_config.midi_convert_model

    input_path = os.path.join(project_path, input_file_name)
    test_image_path = None

    if convert_model == "e-gmd" and not is_test:
        output_path = os.path.splitext(input_path)[0] + ".mid"
        offset = 0
        duration = None

        convert_to_midi_with_onsets_frames(
            output_path,
            input_path,
            offset,
            duration,
            bpm,
            resolution,
            hop_length,
            onset_delta,
            adjust_offset_count,
            adjust_offset_min,
            adjust_offset_max,
            velocity_max_percentile,
            convert_model,
            config
        )

        output_log = "MIDIへの変換に成功しました。\n"
        output_log += '"5. Convert to DTX"タブに進んでください。\n\n'
        output_log += f"output_path: {output_path}\n\n"

    elif convert_model == "original" and not is_test:
        output_path = os.path.splitext(input_path)[0] + ".mid"
        offset = 0
        duration = None

        convert_to_midi_drums(
            output_path,
            input_path,
            None,
            offset,
            duration,
            bpm,
            resolution,
            threshold,
            segmentation,
            hop_length,
            onset_delta,
            disable_hh_frame,
            adjust_offset_count,
            adjust_offset_min,
            adjust_offset_max,
            velocity_max_percentile,
            config)

        output_log = "MIDIへの変換に成功しました。\n"
        output_log += '"5. Convert to DTX"タブに進んでください。\n\n'
        output_log += f"output_path: {output_path}\n\n"
    
    elif convert_model == "mixed" and not is_test:
        output_path = os.path.splitext(input_path)[0] + ".mid"
        convert_model = "e-gmd"
        e_gmd_output_path = os.path.splitext(input_path)[0] + f".{convert_model}.mid"
        offset = 0
        duration = None

        convert_to_midi_with_onsets_frames(
            e_gmd_output_path,
            input_path,
            offset,
            duration,
            bpm,
            resolution,
            hop_length,
            onset_delta,
            adjust_offset_count,
            adjust_offset_min,
            adjust_offset_max,
            velocity_max_percentile,
            convert_model,
            config
        )

        convert_to_midi_drums(
            output_path,
            input_path,
            e_gmd_output_path,
            offset,
            duration,
            bpm,
            resolution,
            threshold,
            segmentation,
            hop_length,
            onset_delta,
            disable_hh_frame,
            adjust_offset_count,
            adjust_offset_min,
            adjust_offset_max,
            velocity_max_percentile,
            config)

        output_log = "MIDIへの変換に成功しました。\n"
        output_log += '"5. Convert to DTX"タブに進んでください。\n\n'
        output_log += f"output_path: {output_path}\n\n"
    else:
        test_midi_path = os.path.join(project_path, "test.mid")
        peak_midi_path = os.path.join(project_path, "peak.mid")
        cqt_midi_path = os.path.join(project_path, "cqt.mid")
        test_image_path = os.path.join(project_path, "test.png")
        offset = config.midi_test_offset
        duration = config.midi_test_duration

        convert_to_midi_drums(
            test_midi_path,
            input_path,
            None,
            offset,
            duration,
            bpm,
            resolution,
            threshold,
            segmentation,
            hop_length,
            onset_delta,
            disable_hh_frame,
            adjust_offset_count,
            adjust_offset_min,
            adjust_offset_max,
            velocity_max_percentile,
            config)

        convert_to_midi_peak(
            peak_midi_path,
            input_path,
            bpm,
            resolution,
            threshold,
            hop_length,
            offset,
            duration)

        convert_to_midi_cqt(
            cqt_midi_path,
            input_path,
            bpm,
            resolution,
            threshold,
            hop_length,
            offset,
            duration)

        output_test_image(
            input_path,
            test_midi_path,
            peak_midi_path,
            cqt_midi_path,
            test_image_path,
            hop_length,
            onset_delta,
            offset,
            duration,
            config)

        output_log = "テスト用画像の作成に成功しました。\n\n"

    base_output_log = auto_save(config, project_path)

    return [base_output_log, output_log, test_image_path]

@debug_args
def convert_to_midi_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    return _convert_to_midi_gr(*args, project_path=project_path, is_test=False)

@debug_args
def convert_test_to_midi_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    return _convert_to_midi_gr(*args, project_path=project_path, is_test=True)

@debug_args
def reset_pitch_midi_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    default_config = ProjectConfig.get_default_config()

    config.bd_min = default_config.bd_min
    config.sn_min = default_config.sn_min
    config.ht_min = default_config.ht_min
    config.lt_min = default_config.lt_min
    config.ft_min = default_config.ft_min

    config.bd_range = default_config.bd_range
    config.sn_range = default_config.sn_range
    config.ht_range = default_config.ht_range
    config.lt_range = default_config.lt_range
    config.ft_range = default_config.ft_range

    base_output_log = auto_save(config, project_path)

    output_log = "音程情報のリセットが完了しました。\n\n"
    output_image = None

    return [
        base_output_log,
        output_log,
        output_image,

        config.bd_min,
        config.sn_min,
        config.ht_min,
        config.lt_min,
        config.ft_min,

        config.bd_range,
        config.sn_range,
        config.ht_range,
        config.lt_range,
        config.ft_range,
    ]

@debug_args
def copy_resources(config: ProjectConfig, project_path):
    for file in config.get_resources():
        file = file.replace("¥", os.path.sep).replace("\\", os.path.sep).replace("/", os.path.sep)
        from_path = os.path.join("resources", file)
        to_path = os.path.join(project_path, file)
        if os.path.exists(from_path) and not os.path.exists(to_path):
            print(f"copy {from_path} -> {to_path}")
            os.makedirs(os.path.dirname(to_path), exist_ok=True)
            shutil.copyfile(from_path, to_path)

    print(f"Resource copying is complete.")

@debug_args
def _midi_to_dtx_gr(config: ProjectConfig, project_path: str, output_image: bool):
    input_file_name = config.dtx_input_name
    output_file_name = config.dtx_output_name
    output_image_name = config.dtx_output_image_name

    input_path = os.path.join(project_path, input_file_name)
    output_path = os.path.join(project_path, output_file_name)
    output_image_path = os.path.join(project_path, output_image_name) if output_image else None
    dtx_info = config.get_dtx_info()

    if not os.path.exists(os.path.join(project_path, dtx_info.VIDEO)):
        dtx_info.VIDEO = config.get_fixed_download_file_name()

    dtx_text = midi_to_dtx(input_path, output_path, output_image_path, dtx_info)

    config.dtx_shift_time = dtx_info.SHIFT_TIME
    config.dtx_align_nth_bd = dtx_info.ALIGN_NTH_BD

    copy_resources(config, project_path)

    output_log = "DTX譜面の作成に成功しました。\n"
    output_log += 'アプリで譜面の確認をしてください。\n\n'

    base_output_log = auto_save(config, project_path)

    return [base_output_log, output_log, dtx_info.SHIFT_TIME, dtx_info.ALIGN_NTH_BD, dtx_text, output_image_path]

@debug_args
def midi_to_dtx_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    outputs = _midi_to_dtx_gr(config, project_path, output_image=False)
    return outputs

@debug_args
def midi_to_dtx_and_output_image_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    outputs = _midi_to_dtx_gr(config, project_path, output_image=True)
    return outputs

@debug_args
def reset_dtx_wav_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    default_config = ProjectConfig.get_default_config()

    config.hhc_wav = default_config.hhc_wav
    config.snare_wav = default_config.snare_wav
    config.bd_wav = default_config.bd_wav
    config.ht_wav = default_config.ht_wav
    config.lt_wav = default_config.lt_wav
    config.cymbal_wav = default_config.cymbal_wav
    config.ft_wav = default_config.ft_wav
    config.hho_wav = default_config.hho_wav
    config.ride_wav = default_config.ride_wav
    config.lc_wav = default_config.lc_wav
    config.lp_wav = default_config.lp_wav
    config.lbd_wav = default_config.lbd_wav

    config.hhc_volume = default_config.hhc_volume
    config.snare_volume = default_config.snare_volume
    config.bd_volume = default_config.bd_volume
    config.ht_volume = default_config.ht_volume
    config.lt_volume = default_config.lt_volume
    config.cymbal_volume = default_config.cymbal_volume
    config.ft_volume = default_config.ft_volume
    config.hho_volume = default_config.hho_volume
    config.ride_volume = default_config.ride_volume
    config.lc_volume = default_config.lc_volume
    config.lp_volume = default_config.lp_volume
    config.lbd_volume = default_config.lbd_volume

    config.hhc_offset = default_config.hhc_offset
    config.snare_offset = default_config.snare_offset
    config.bd_offset2 = default_config.bd_offset2
    config.ht_offset = default_config.ht_offset
    config.lt_offset = default_config.lt_offset
    config.cymbal_offset = default_config.cymbal_offset
    config.ft_offset = default_config.ft_offset
    config.hho_offset = default_config.hho_offset
    config.ride_offset = default_config.ride_offset
    config.lc_offset = default_config.lc_offset
    config.lp_offset = default_config.lp_offset
    config.lbd_offset = default_config.lbd_offset

    base_output_log = auto_save(config, project_path)

    output_log = "チップ出力設定のリセットが完了しました。\n\n"

    return [
        base_output_log,
        output_log,

        config.hhc_wav,
        config.snare_wav,
        config.bd_wav,
        config.ht_wav,
        config.lt_wav,
        config.cymbal_wav,
        config.ft_wav,
        config.hho_wav,
        config.ride_wav,
        config.lc_wav,
        config.lp_wav,
        config.lbd_wav,

        config.hhc_volume,
        config.snare_volume,
        config.bd_volume,
        config.ht_volume,
        config.lt_volume,
        config.cymbal_volume,
        config.ft_volume,
        config.hho_volume,
        config.ride_volume,
        config.lc_volume,
        config.lp_volume,
        config.lbd_volume,

        config.hhc_offset,
        config.snare_offset,
        config.bd_offset2,
        config.ht_offset,
        config.lt_offset,
        config.cymbal_offset,
        config.ft_offset,
        config.hho_offset,
        config.ride_offset,
        config.lc_offset,
        config.lp_offset,
        config.lbd_offset,
    ]

@debug_args
def dev_select_separate_audio_gr(*args):
    dev_config.update(*args)
    dev_config.save(".")

    initialdir = os.path.dirname(dev_config.separate_audio_file)
    audio_file = get_audio_path(initialdir=initialdir)
    if audio_file == '':
        raise Exception("音声ファイルを選択してください")

    dev_config.separate_audio_file = audio_file
    dev_config.save(".")

    output_log = f"音声ファイルを開きました。{audio_file}\n\n"

    return [output_log, audio_file]

@debug_args
def dev_separate_audio_gr(*args):
    dev_config.update(*args)
    dev_config.save(".")

    model = dev_config.separate_model
    input_path = dev_config.separate_audio_file
    output_dir = os.path.dirname(input_path)
    jobs = dev_config.separate_jobs
    bitrate = app_config.bgm_bitrate

    if not os.path.exists(input_path):
        raise Exception(f"BGMが見つかりません。 {input_path}")

    output_files = separate_music(model, input_path, output_dir, jobs, drums_only=False)

    # 音声の変換
    converted_files = []
    for output_file in output_files:
        converted_path = output_file.replace(".wav", ".ogg")
        convert_audio(output_file, converted_path, bitrate)
        safe_remove_file(output_file)
        converted_files.append(converted_path)

    output_log = "音声の分離に成功しました。\n\n"

    return [output_log, *converted_files]

@debug_args
def dev_select_download_video_output_dir_gr(*args):
    dev_config.update(*args)
    dev_config.save(".")

    initialdir = os.path.dirname(dev_config.download_video_output_dir)
    output_dir = get_folder_path(initialdir=initialdir)
    if output_dir == '':
        raise Exception("出力先フォルダを選択してください")

    dev_config.download_video_output_dir = output_dir
    dev_config.save(".")

    output_log = f"出力先フォルダを開きました。{output_dir}\n\n"

    return [output_log, output_dir]

@debug_args
def dev_download_video_gr(*args):
    dev_config.update(*args)
    dev_config.save(".")

    url = dev_config.download_video_url
    output_dir = dev_config.download_video_output_dir
    downloader = app_config.downloader
    tmp_output_path = get_tmp_file_path(app_config.download_format)
    tmp_thumbnail_path = get_tmp_file_path(".jpg")
    thumbnail_width = app_config.thumbnail_width
    thumbnail_height = app_config.thumbnail_height

    if url == "":
        raise Exception("URLを入力してください。")

    comment, title, artist, duration, width, height = download_video(
        url,
        tmp_output_path,
        tmp_thumbnail_path,
        (thumbnail_width, thumbnail_height),
        downloader)

    output_file_name = f"{artist} - {title}"
    output_path = os.path.join(output_dir, output_file_name + "." + app_config.download_format)
    thumbnail_path = os.path.join(output_dir, output_file_name + ".jpg")

    shutil.move(tmp_output_path, output_path)
    shutil.move(tmp_thumbnail_path, thumbnail_path)

    output_log = "動画のダウンロードに成功しました。\n\n"
    output_log += f"title: {title}\n"
    output_log += f"artist: {artist}\n"
    output_log += f"duration: {duration}\n"

    return [output_log]

@debug_args
def dev_select_crop_video_input_path_gr(*args):
    dev_config.update(*args)
    dev_config.save(".")

    initialdir = os.path.dirname(dev_config.crop_video_input_path)
    input_path = get_video_path(initialdir=initialdir)
    if input_path == '':
        raise Exception("動画を選択してください")

    dev_config.crop_video_input_path = input_path
    dev_config.save(".")

    output_log = f"動画を開きました。{input_path}\n\n"

    return [output_log, input_path]

@debug_args
def dev_crop_video_gr(*args):
    dev_config.update(*args)
    dev_config.save(".")

    input_path = dev_config.crop_video_input_path
    start_time = dev_config.crop_video_start_time
    end_time = dev_config.crop_video_end_time
    adjust_start_keyframe = dev_config.crop_video_adjust_start_keyframe

    if not os.path.exists(input_path):
        raise Exception(f"動画が見つかりません。 {input_path}")

    filename, ext = os.path.splitext(os.path.basename(input_path))

    output_dir = os.path.dirname(input_path)
    output_path = os.path.join(output_dir, filename + "_cropped" + ext)

    output_path = crop_copy_video(input_path, output_path, start_time, end_time, adjust_start_keyframe)

    output_log = "動画のトリミングに成功しました。\n\n"

    return output_log

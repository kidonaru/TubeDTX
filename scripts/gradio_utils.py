from contextlib import nullcontext
from dataclasses import asdict
import datetime
import multiprocessing as mp
import os
import shutil
import traceback
import gradio as gr
import requests

from scripts.config_utils import AppConfig, ProjectConfig, app_config
from scripts.debug_utils import debug_args
from scripts.media_utils import create_preview_audio, download_video, extract_audio, get_tmp_dir, get_tmp_file_path, get_video_info, trim_and_crop_video
from scripts.music_utils import compute_bpm, compute_chorus_time
from scripts.convert_to_midi import convert_to_midi_cqt, convert_to_midi_drums, convert_to_midi_peak, output_test_image
from scripts.midi_to_dtx import midi_to_dtx
from scripts.platform_utils import get_folder_path
from scripts.separate_music import separate_music

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
    thumbnail_file_name = config.movie_thumbnail_file_name
    thumbnail_path = os.path.join(project_path, thumbnail_file_name)

    response = requests.get(thumbnail_url)
    with open(thumbnail_path, "wb") as file:
        file.write(response.content)

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
            if not check_converted(config.movie_download_file_name):
                outputs = download_video_gr(*config.to_dict().values(), project_path=project_path)
                config = ProjectConfig.load(project_path)
                base_output_log = outputs[0]
                output_log += outputs[1]

        if app_config.batch_convert_movie:
            if not check_converted(config.bgm_name):
                outputs = convert_video_gr(*config.to_dict().values(), project_path=project_path)
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
                outputs = separate_music_gr(*config.to_dict().values(), project_path=project_path)
                config = ProjectConfig.load(project_path)
                base_output_log = outputs[0]
                output_log += outputs[1]

        if app_config.batch_convert_to_midi:
            if not check_converted("drums.mid"):
                outputs = convert_to_midi_gr(*config.to_dict().values(), project_path=project_path)
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
        output_log += f"エラーが発生しました。\n"
        output_log += f"{str(e)}\n{traceback.format_exc()}\n\n"

    # ログに譜面名を追加
    if len(output_log) > 0:
        header_log = f"==============================\n"
        header_log += f"{config.dtx_title}\n"
        header_log += f"==============================\n\n"
        output_log = header_log + output_log

    return [base_output_log, output_log, *config.to_dict().values()]

@debug_args
def batch_convert_selected_score_gr(*args):
    global app_config
    app_config = AppConfig(*args)
    app_config.save(".")

    lock = mp.Manager().Lock()
    outputs = _batch_convert_gr(lock, app_config.project_path)

    outputs[1] += "全てのバッチ処理が完了しました。\n\n"

    return outputs

@debug_args
def batch_convert_all_score_gr(*args):
    global app_config
    app_config = AppConfig(*args)
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

    output_log += "全てのバッチ処理が完了しました。\n\n"

    config = ProjectConfig.load(app_config.project_path)

    return [base_output_log, output_log, *config.to_dict().values()]

@debug_args
def _download_video_gr(config: ProjectConfig, project_path):
    url = config.movie_url
    output_file_name = config.movie_download_file_name
    thumbnail_file_name = config.movie_thumbnail_file_name

    if url == "":
        raise Exception("URLを入力してください。")

    output_path = os.path.join(project_path, output_file_name)
    thumbnail_path = os.path.join(project_path, thumbnail_file_name)

    comment, title, artist, duration, width, height = download_video(url, output_path, thumbnail_path)

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
    input_file_name = config.movie_download_file_name
    output_file_name = config.movie_output_file_name
    bgm_file_name = config.bgm_name
    start_time = config.movie_start_time
    end_time = config.movie_end_time
    width = config.movie_width
    height = config.movie_height
    target_dbfs = config.movie_target_dbfs
    bitrate = app_config.bgm_bitrate

    input_path = os.path.join(project_path, input_file_name)
    output_path = os.path.join(project_path, output_file_name)
    bgm_path = os.path.join(project_path, bgm_file_name)

    if os.path.exists(output_path):
        os.remove(output_path)

    output_path = trim_and_crop_video(input_path, output_path, start_time, end_time, width, height)
    extract_audio(output_path, bgm_path, target_dbfs, bitrate)

    output_log = "動画の処理に成功しました。\n"
    output_log += '"2. Create Preview File"タブに進んでください。\n\n'

    base_output_log = auto_save(config, project_path)

    return [base_output_log, output_log, input_path, output_path, bgm_path]

@debug_args
def download_and_convert_video_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

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
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    outputs = _download_video_gr(config, project_path)

    return outputs

@debug_args
def convert_video_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    outputs = _convert_video_gr(config, project_path)

    return outputs

@debug_args
def reload_video_gr(*args, project_path=None):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    input_file_name = config.movie_download_file_name
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
def force_copy_file(input_path, output_path):
    if os.path.exists(output_path):
        os.remove(output_path)
    shutil.copyfile(input_path, output_path)

@debug_args
def separate_music_gr(*args, project_path=None, lock: mp.Lock=None):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    model = config.separate_model
    bgm_name = config.bgm_name
    jobs = config.separate_jobs

    input_path = os.path.join(project_path, bgm_name)
    if not os.path.exists(input_path):
        return [f"BGMが見つかりません。 {input_path}", None]

    tmp_dir = get_tmp_dir()

    # 全角文字が入ってるとコンバートに失敗するので作業ディレクトリに移動する
    tmp_input_path = get_tmp_file_path(os.path.splitext(bgm_name)[1])
    force_copy_file(input_path, tmp_input_path)

    with lock if lock is not None else nullcontext():
        separate_music(model, tmp_dir, tmp_input_path, jobs)

    # 一時出力先パス
    basename_without_ext = os.path.splitext(os.path.basename(tmp_input_path))[0]
    tmp_output_path = os.path.join(tmp_dir, model, basename_without_ext, "drums.wav")

    # ファイルのコピー
    output_path = os.path.join(project_path, "drums.wav")
    force_copy_file(tmp_output_path, output_path)

    # 一時ファイルの削除
    os.remove(tmp_input_path)
    shutil.rmtree(os.path.join(tmp_dir, model, basename_without_ext))

    bpm = compute_bpm(output_path)
    config.dtx_bpm = bpm

    output_log = "ドラム音の分離に成功しました。\n"
    output_log += '"4. Convert to MIDI"タブに進んでください。\n\n'
    output_log += f"bpm: {bpm}\n\n"

    base_output_log = auto_save(config, project_path)

    return [base_output_log, output_log, output_path, bpm]

@debug_args
def _convert_to_midi_gr(*args, project_path=None, is_test=False):
    project_path = project_path or app_config.project_path
    config = ProjectConfig(*args)

    input_file_name = config.midi_input_name
    resolution = config.midi_resolution
    threshold = config.midi_threshold
    segmentation = config.midi_segmentation
    hop_length = config.midi_hop_length
    onset_delta = config.midi_onset_delta
    disable_hh_frame = config.midi_disable_hh_frame
    adjust_offset_frame = config.midi_adjust_offset_frame
    velocity_max_percentile = config.midi_velocity_max_percentile
    bpm = config.dtx_bpm

    input_path = os.path.join(project_path, input_file_name)
    test_image_path = None

    if not is_test:
        output_path = os.path.splitext(input_path)[0] + ".mid"
        offset = 0
        duration = None

        convert_to_midi_drums(
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
            disable_hh_frame,
            adjust_offset_frame,
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
            offset,
            duration,
            bpm,
            resolution,
            threshold,
            segmentation,
            hop_length,
            onset_delta,
            disable_hh_frame,
            adjust_offset_frame,
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
        dtx_info.VIDEO = config.movie_download_file_name

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

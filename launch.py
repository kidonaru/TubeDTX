import gradio as gr

from scripts.config_utils import ProjectConfig, app_config, dev_config
from scripts.gradio_utils import batch_convert_all_score_gr, batch_convert_selected_score_gr, convert_to_midi_gr, convert_video_gr, create_preview_gr, download_and_convert_video_gr, download_video_gr, midi_to_dtx_and_output_image_gr, midi_to_dtx_gr, new_score_gr, reload_preview_gr, reload_video_gr, reload_workspace_gr, reset_dtx_wav_gr, reset_pitch_midi_gr, select_project_gr, select_workspace_gr, separate_music_gr, convert_test_to_midi_gr, dev_select_separate_audio_gr, dev_separate_audio_gr

demucs_models = ["htdemucs", "htdemucs_ft", "htdemucs_6s", "hdemucs_mmi", "mdx", "mdx_extra", "mdx_q", "mdx_extra_q", "SIG"]
midi_models = ["original", "e-gmd"]

config = ProjectConfig.load(app_config.project_path)

def add_space(space_count:int=1):
    for i in range(0, space_count):
        gr.HTML(value="")

with gr.Blocks(title="TubeDTX") as demo:
    gr.Markdown("TubeDTX")

    with gr.Row():
        with gr.Column(scale=1, min_width=150):
            project_image = gr.Image(show_label=False, value=app_config.get_current_preimage()).style(width=150)
        with gr.Column(scale=3):
            project_path_textbox = gr.Textbox(label="Score Path", value=app_config.project_path)
        with gr.Column(scale=3):
            base_output = gr.Markdown(show_label=False)

    with gr.Tabs():
        with gr.TabItem("0. Workspace"):
            with gr.Row():
                with gr.Column(scale=1.5):
                    workspace_gallery = gr.Gallery(value=app_config.get_all_gallery()).style(grid=4, preview=True)
                with gr.Column(scale=1):
                    with gr.Tabs():
                        with gr.TabItem("Base"):
                            workspace_output = gr.Textbox(show_label=False)
                            with gr.Row():
                                with gr.Column(scale=5):
                                    workspace_path_textbox = gr.Textbox(label="Workspace Path", value=app_config.workspace_path)
                                with gr.Column(scale=1, min_width=50):
                                    workspace_open_button = gr.Button("Open", variant="primary")
                            with gr.Row():
                                with gr.Column(scale=5):
                                    workspace_new_score_url_textbox = gr.Textbox(label="New Score from YouTube URL", value="")
                                with gr.Column(scale=1, min_width=50):
                                    workspace_new_score_button = gr.Button("New", variant="primary")
                            auto_save_checkbox = gr.Checkbox(value=app_config.auto_save, label="Auto Save", visible=False)
                            bgm_bitrate_textbox = gr.Textbox(value=app_config.bgm_bitrate, label="BGM Bitrate", visible=False)
                            workspace_reload_button = gr.Button("Reload", variant="primary")
                            workspace_video = gr.Video(source="upload")
                        with gr.TabItem("Batch"):
                            batch_output = gr.Textbox(show_label=False)
                            batch_download_movie_checkbox = gr.Checkbox(value=app_config.batch_download_movie, label="1. Download Movie")
                            batch_convert_movie_checkbox = gr.Checkbox(value=app_config.batch_convert_movie, label="1.5. Convert Movie")
                            batch_create_preview_checkbox = gr.Checkbox(value=app_config.batch_create_preview, label="2. Create Preview File")
                            batch_separate_music_checkbox = gr.Checkbox(value=app_config.batch_separate_music, label="3. Separate Music")
                            batch_convert_to_midi_checkbox = gr.Checkbox(value=app_config.batch_convert_to_midi, label="4. Convert to MIDI")
                            batch_convert_to_dtx_checkbox = gr.Checkbox(value=app_config.batch_convert_to_dtx, label="5. Convert to DTX")

                            with gr.Row():
                                batch_skip_converted_checkbox = gr.Checkbox(value=app_config.batch_skip_converted, label="Skip Converted")
                                batch_jobs_slider = gr.Slider(1, 32, value=app_config.batch_jobs, step=1, label="Batch Jobs")

                            with gr.Row():
                                batch_convert_selected_score_button = gr.Button("Batch Convert Selected Score", variant="primary")
                                batch_convert_all_score_button = gr.Button("Batch Convert All Score", variant="primary")

            text = "作業ディレクトリの選択と新規譜面の作成ができます。\n\n"

            text += "まず、\"Open\"ボタンを押して。作成する譜面を格納するディレクトリを選択してください\n"
            text += "次に、\"New Score from YouTube URL\"に譜面にしたい動画のURLを入力して\"New\"ボタンを押します。\n"
            text += "\"Reload\"ボタンを押すと、譜面リストの再読み込みを行います。\n\n"

            text += "\"Batch\"タブでは、全譜面に対して一括で処理を実行できます。\n"
            text += "実行したいタブ名にチェックを入れると、その処理をバッチで実行します。\n"
            text += "\"Batch Convert Selected Score\"ボタンを押すと、選択中の譜面に対してバッチ処理を行います。\n"
            text += "\"Batch Convert All Score\"ボタンを押すと、ワークスペース内全譜面に対してバッチ処理を行います。\n"
            text += "\"Skip Converted\"のチェックを入れると、すでに変換済みの譜面はスキップされます。\n\n"
            text += "\"Batch Jobs\"で並列実行数を設定できます。\n\n"

            gr.TextArea(text, show_label=False)
        with gr.TabItem("1. Download Movie"):
            with gr.Row():
                with gr.Column():
                    add_space(1)
                    with gr.Row():
                        movie_download_and_convert_button = gr.Button("Download & Convert", variant="primary")
                    with gr.Row():
                        movie_download_button = gr.Button("Download")
                        movie_convert_button = gr.Button("Convert")
                        movie_refresh_button = gr.Button("Refresh")
                    with gr.Row():
                        movie_url_textbox = gr.Textbox(label="YouTube URL", value=config.movie_url)
                    with gr.Row():
                        movie_download_file_textbox = gr.Textbox(label="Download File Name", value=config.movie_download_file_name)
                        movie_output_file_textbox = gr.Textbox(label="Output File Name", value=config.movie_output_file_name)
                    with gr.Row():
                        bgm_name_textbox = gr.Textbox(label="BGM File Name", value=config.bgm_name)
                        thumbnail_file_textbox = gr.Textbox(label="Thumbnail File Name", value=config.movie_thumbnail_file_name2)
                    with gr.Row():
                        movie_start_time_slider = gr.Number(value=config.movie_start_time, label="Trim Start Time")
                        movie_end_time_slider = gr.Number(value=config.movie_end_time, label="Trim End Time")
                    with gr.Row():
                        movie_width_slider = gr.Number(value=config.movie_width, label="Crop Width")
                        movie_height_slider = gr.Number(value=config.movie_height, label="Crop Height")
                    movie_target_dbfs_slider = gr.Slider(value=config.movie_target_dbfs, label="Target dBFS", minimum=-30, maximum=0, step=1)
                with gr.Column():
                    movie_output = gr.Textbox(show_label=False)
                    movie_input_video = gr.Video(label="Input", source="upload")
                    movie_output_video = gr.Video(label="Result", source="upload")
                    movie_output_audio = gr.Audio(label="Result", source="upload", type="filepath")

            text = "動画のダウンロードと変換処理を行います。\n\n"
            text += "\"Download & Convert\"ボタンを押すと、動画をダウンロードして、指定時間で動画を切り取り、BGMを吐き出します。\n"
            text += "\"Convert\"ボタンを押すと、ダウンロード処理を飛ばして変換処理のみを行います。\n"
            text += "\"Refresh\"ボタンを押すと、表示を更新します。\n\n"

            text += "- Trim Start/End Time: 切り取り時間を指定します\n"
            text += "- Crop Width/Height: 動画のクリップするサイズを指定します\n"
            text += "- Target dBFS: 目標音量を指定します。YouTube標準は-12dBFS程度。0で無効化\n"

            gr.TextArea(text, show_label=False)
        with gr.TabItem("2. Create Preview File"):
            with gr.Row():
                with gr.Column():
                    add_space(1)
                    with gr.Row():
                        preview_create_button = gr.Button("Create", variant="primary")
                    with gr.Row():
                        preview_reload_button = gr.Button("Refresh")
                    preview_output_name_textbox = gr.Textbox(label="Preview File Name", value=config.preview_output_name)
                    with gr.Row():
                        preview_start_time_slider = gr.Number(value=config.preview_start_time, label="Preview Start Time")
                        preview_duration_slider = gr.Number(value=config.preview_duration, label="Preview Duration")
                    with gr.Row():
                        preview_fade_in_duration_slider = gr.Number(value=config.preview_fade_in_duration, label="Fade In Duration")
                        preview_fade_out_duration_slider = gr.Number(value=config.preview_fade_out_duration, label="Fade Out Duration")
                with gr.Column():
                    preview_output = gr.Textbox(show_label=False)
                    preview_input_audio = gr.Audio(label="Input", source="upload", type="filepath")
                    preview_output_audio = gr.Audio(label="Result", source="upload", type="filepath")

            text = "プレビュー用の音声ファイルを作成します。\n\n"

            text += "\"Create\"ボタンを押すと、手動設定で音声ファイルを作成します。\n"
            text += "\"Refresh\"ボタンを押すと、表示を更新します。\n\n"

            text += "- Preview Start Time: プレビューの開始時間。0の場合自動で推定して設定します\n"
            text += "- Preview Duration: プレビューの再生時間\n"
            text += "- Fade In/Out Duration: フェードイン/アウトの時間\n\n"
            gr.TextArea(text, show_label=False)
        with gr.TabItem("3. Separate Music"):
            with gr.Row():
                with gr.Column():
                    add_space(1)
                    separate_button = gr.Button("Separate", variant="primary")
                    separate_model_dropdown = gr.Dropdown(demucs_models, value=config.separate_model, label="Model")
                    separate_jobs_slider = gr.Slider(0, 32, value=config.separate_jobs, step=1, label="Number of Jobs")
                with gr.Column():
                    separate_output = gr.Textbox(show_label=False)
                    separate_output_audio = gr.Audio(label="Result", source="upload", type="filepath")

            text = "BGMからドラム音を分離します。\n\n"

            text += "\"Separate\"ボタンを押すと、Demucsを使用して分離を実行します。\n"
            text += "各Modelの詳細は公式のREADMEを参照してください。\n"
            text += "https://github.com/facebookresearch/demucs\n"

            gr.TextArea(text, show_label=False)
        with gr.TabItem("4. Convert to MIDI"):
            with gr.Row():
                with gr.Column():
                    add_space(1)
                    with gr.Row():
                        midi_convert_button = gr.Button("Convert", variant="primary")
                    with gr.Row():
                        midi_convert_test_button = gr.Button("Convert Test")
                    with gr.Tabs():
                        with gr.TabItem("Base"):
                            midi_input_name_textbox = gr.Textbox(label="Input File Name", value=config.midi_input_name2)
                            midi_convert_model_dropdown = gr.Dropdown(midi_models, value=config.midi_convert_model, label="Model")
                            midi_resolution_slider = gr.Slider(0, 16, step=1, value=config.midi_resolution, label="Resolution")
                            with gr.Row():
                                midi_threshold_slider = gr.Slider(0, 1, value=config.midi_threshold, label="Threshold")
                                midi_segmentation_slider = gr.Slider(0, 1, value=config.midi_segmentation, label="Segmentation")
                            with gr.Row():
                                midi_hop_length_slider = gr.Slider(1, 512, step=1, value=config.midi_hop_length, label="Hop Length")
                                midi_onset_delta_slider = gr.Slider(0, 1, step=0.01, value=config.midi_onset_delta, label="Onset Delta")
                            with gr.Row():
                                midi_disable_hh_frame_slider = gr.Slider(0, 10, step=1, value=config.midi_disable_hh_frame, label="Disable HH Frame")
                                midi_adjust_offset_count_slider = gr.Slider(0, 10, step=1, value=config.midi_adjust_offset_count, label="Adjust Offset Count")
                            with gr.Row():
                                midi_adjust_offset_min_slider = gr.Slider(-20, 0, step=1, value=config.midi_adjust_offset_min, label="Adjust Offset Min")
                                midi_adjust_offset_max_slider = gr.Slider(0, 20, step=1, value=config.midi_adjust_offset_max, label="Adjust Offset Max")
                            with gr.Row():
                                midi_velocity_max_percentile_slider = gr.Slider(0, 100, step=1, value=config.midi_velocity_max_percentile, label="Velocity Max Percentile")
                            with gr.Row():
                                midi_test_offset_slider = gr.Number(value=config.midi_test_offset, label="Test Offset")
                                midi_test_duration_slider = gr.Number(value=config.midi_test_duration, label="Test Duration")
                        with gr.TabItem("Pitch"):
                            with gr.Row():
                                midi_bd_min_slider = gr.Slider(0, 127, step=1, value=config.bd_min, label="BD Min")
                                midi_bd_range_slider = gr.Slider(0, 127, step=1, value=config.bd_range, label="BD Range")
                            with gr.Row():
                                midi_sn_min_slider = gr.Slider(0, 127, step=1, value=config.sn_min, label="Snare Min")
                                midi_sn_range_slider = gr.Slider(0, 127, step=1, value=config.sn_range, label="Snare Range")
                            with gr.Row():
                                midi_ht_min_slider = gr.Slider(0, 127, step=1, value=config.ht_min, label="HighTom Min")
                                midi_ht_range_slider = gr.Slider(0, 127, step=1, value=config.ht_range, label="HighTom Range")
                            with gr.Row():
                                midi_lt_min_slider = gr.Slider(0, 127, step=1, value=config.lt_min, label="LowTom Min")
                                midi_lt_range_slider = gr.Slider(0, 127, step=1, value=config.lt_range, label="LowTom Range")
                            with gr.Row():
                                midi_ft_min_slider = gr.Slider(0, 127, step=1, value=config.ft_min, label="FloorTom Min")
                                midi_ft_range_slider = gr.Slider(0, 127, step=1, value=config.ft_range, label="FloorTom Range")
                            midi_reset_pitch_button = gr.Button("Reset").style(full_width=False, size='sm')
                with gr.Column():
                    midi_output = gr.Textbox(show_label=False)
                    midi_output_image = gr.Image(show_label=False)

            text = "分離したドラム音をMIDIに変換します。\n\n"

            text += "\"Convert\"ボタンを押すと、音高を解析してDTX変換用のMIDIを出力します。\n"
            text += "\"Convert Test\"ボタンを押すと、音高確認用の画像ファイルを出力します。\n\n"

            text += "各パラメータの説明\n"
            text += "- Threshold: 変換しきい値。下げると小さい音も拾いやすくなりますが、ノイズも乗りやすくなります\n"
            text += "- Segmentation: ノーツの分裂しやすさ。上げると連打系が拾いやすくなりますが、ノイズも乗りやすくなります\n"
            text += "- Hop Length: 解析時の移動幅(フレーム数)\n"
            text += "- Onset Delta: Onset検出の感度。下げると小さい音も拾いやすくなりますが、ノイズも乗りやすくなります\n"
            text += "- Disable HH Frame: 指定フレーム内にノーツがある場合、ハイハットを無効化します\n"
            text += "- Adjust Offset Count: Onsetに合わせて調整する施行回数\n"
            text += "- Adjust Offset Min/Max: Onsetに合わせて調整するフレーム範囲\n"
            text += "- Velocity Max Percentile: Velocityの最大値に対応するnパーセンタイル\n"
            text += "- Test Offset: 音高確認画像の開始位置(秒)\n"
            text += "- Test Duration: 音高確認画像の再生時間(秒)\n\n"

            text += "Pitchタブで各チャンネルの基準音高を変更できます。\n"
            gr.TextArea(text, show_label=False)
        with gr.TabItem("5. Convert to DTX"):
            with gr.Row():
                with gr.Column():
                    add_space(1)
                    with gr.Row():
                        dtx_convert_button = gr.Button("Convert", variant="primary")
                        dtx_convert_and_output_image_button = gr.Button("Convert And Output Image", variant="primary")
                    with gr.Tabs():
                        with gr.TabItem("Base"):
                            with gr.Row():
                                dtx_input_name_textbox = gr.Textbox(label="Input File Name", value=config.dtx_input_name)
                                dtx_output_name_textbox = gr.Textbox(label="Output File Name", value=config.dtx_output_name)
                                dtx_output_image_name_textbox = gr.Textbox(label="Output Image Name", value=config.dtx_output_image_name)
                            dtx_bpm_slider = gr.Slider(60, 240, step=0.1, value=config.dtx_bpm, label="BPM")
                            with gr.Row():
                                dtx_chip_resolution_slider = gr.Slider(4, 64, value=config.dtx_chip_resolution, step=1, label="Chip Resolution")
                                dtx_bgm_resolution_slider = gr.Slider(4, 256, value=config.dtx_bgm_resolution, step=1, label="BGM Resolution")
                            with gr.Row():
                                dtx_shift_time_slider = gr.Slider(-1, 1, value=config.dtx_shift_time, step=0.01, label="Shift Time")
                                dtx_auto_shift_time_checkbox = gr.Checkbox(value=config.dtx_auto_shift_time, label="Auto Shift Time")
                            with gr.Row():
                                dtx_align_nth_bd_slider = gr.Slider(0, 32, value=config.dtx_align_nth_bd, step=1, label="Align Nth BD")
                                dtx_auto_align_nth_bd_checkbox = gr.Checkbox(value=config.dtx_auto_align_nth_bd, label="Auto Align Nth BD")
                            with gr.Row():
                                dtx_bgm_offset_time_slider = gr.Slider(-1, 1, value=config.dtx_bgm_offset_time, step=0.01, label="BGM Offset Time")
                                dtx_bgm_volume_slider = gr.Slider(0, 100, value=config.dtx_bgm_volume, step=1, label="BGM Volume")
                            with gr.Row():
                                dtx_wav_splits_slider = gr.Slider(1, 10, value=config.dtx_wav_splits, step=1, label="Wav Splits")
                                dtx_wav_volume_slider = gr.Slider(0, 100, value=config.dtx_wav_volume, step=1, label="Wav Volume")
                        with gr.TabItem("Header"):
                            dtx_title_textbox = gr.Textbox(label="Music Title", value=config.dtx_title)
                            dtx_artist_textbox = gr.Textbox(label="Artist", value=config.dtx_artist)
                            dtx_comment_textbox = gr.Textbox(label="Comment", value=config.dtx_comment)
                            dtx_dlevel_slider = gr.Slider(1, 100, value=config.dtx_dlevel, step=1, label="Score Level")
                        with gr.TabItem("Chips 1"):
                            with gr.Row():
                                dtx_hhc_wav_textbox = gr.Textbox(label="HiHatClose", value=config.hhc_wav)
                                dtx_hhc_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.hhc_volume)
                                dtx_hhc_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.hhc_offset)
                                dtx_hhc_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.hhc_pan)
                            with gr.Row():
                                dtx_snare_wav_textbox = gr.Textbox(label="Snare", value=config.snare_wav)
                                dtx_snare_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.snare_volume)
                                dtx_snare_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.snare_offset)
                                dtx_snare_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.snare_pan)
                            with gr.Row():
                                dtx_bd_wav_textbox = gr.Textbox(label="BassDrum", value=config.bd_wav)
                                dtx_bd_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.bd_volume)
                                dtx_bd_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.bd_offset2)
                                dtx_bd_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.bd_pan)
                            with gr.Row():
                                dtx_ht_wav_textbox = gr.Textbox(label="HighTom", value=config.ht_wav)
                                dtx_ht_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.ht_volume)
                                dtx_ht_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.ht_offset)
                                dtx_ht_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.ht_pan)
                            with gr.Row():
                                dtx_lt_wav_textbox = gr.Textbox(label="LowTom", value=config.lt_wav)
                                dtx_lt_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.lt_volume)
                                dtx_lt_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.lt_offset)
                                dtx_lt_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.lt_pan)
                            with gr.Row():
                                dtx_cymbal_wav_textbox = gr.Textbox(label="Cymbal", value=config.cymbal_wav)
                                dtx_cymbal_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.cymbal_volume)
                                dtx_cymbal_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.cymbal_offset)
                                dtx_cymbal_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.cymbal_pan)
                            dtx_reset_wav_button1 = gr.Button("Reset").style(full_width=False, size='sm')
                        with gr.TabItem("Chips 2"):
                            with gr.Row():
                                dtx_ft_wav_textbox = gr.Textbox(label="FloorTom", value=config.ft_wav)
                                dtx_ft_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.ft_volume)
                                dtx_ft_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.ft_offset)
                                dtx_ft_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.ft_pan)
                            with gr.Row():
                                dtx_hho_wav_textbox = gr.Textbox(label="HiHatOpen", value=config.hho_wav)
                                dtx_hho_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.hho_volume)
                                dtx_hho_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.hho_offset)
                                dtx_hho_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.hho_pan)
                            with gr.Row():
                                dtx_ride_wav_textbox = gr.Textbox(label="RideCymbal", value=config.ride_wav)
                                dtx_ride_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.ride_volume)
                                dtx_ride_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.ride_offset)
                                dtx_ride_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.ride_pan)
                            with gr.Row():
                                dtx_lc_wav_textbox = gr.Textbox(label="LeftCymbal", value=config.lc_wav)
                                dtx_lc_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.lc_volume)
                                dtx_lc_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.lc_offset)
                                dtx_lc_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.lc_pan)
                            with gr.Row():
                                dtx_lp_wav_textbox = gr.Textbox(label="LeftPedal", value=config.lp_wav)
                                dtx_lp_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.lp_volume)
                                dtx_lp_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.lp_offset)
                                dtx_lp_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.lp_pan)
                            with gr.Row():
                                dtx_lbd_wav_textbox = gr.Textbox(label="LeftBassDrum", value=config.lbd_wav)
                                dtx_lbd_volume_slider = gr.Slider(0, 100, label="Volume", step=1, value=config.lbd_volume)
                                dtx_lbd_offset_slider = gr.Slider(-1, 1, label="Offset", step=0.01, value=config.lbd_offset)
                                dtx_lbd_pan_slider = gr.Slider(-100, 100, label="Pan", step=1, value=config.lbd_pan)
                            dtx_reset_wav_button2 = gr.Button("Reset").style(full_width=False, size='sm')
                with gr.Column():
                    dtx_output = gr.Textbox(show_label=False)
                    dtx_output_score = gr.Textbox(show_label=False)
                    dtx_output_image = gr.Image(show_label=False)

            text = "MIDIをDTXに変換します。\n\n"

            text += "\"Convert\"ボタンを押すと、MIDIからDTX譜面を出力します。\n"
            text += "\"Convert And Output Image\"ボタンを押すと、譜面を画像化したものも同時に出力します。(時間がかかります)\n\n"

            text += "- Chip Resolution: チップ配置の解像度\n"
            text += "- BGM Resolution: チップ配置の解像度\n"
            text += "- Shift Time: チップ全体を指定時間(秒)ずらします\n"
            text += "- Auto Shift Time: Shift Timeを自動調整します\n"
            text += "- Align Nth BD: 指定番目のバスドラムのチップ位置を、小節開始位置に設定します\n"
            text += "- Auto Align Nth BD: Align Nth BDを自動調整します\n"
            text += "- BGM Offset: BGMの開始位置を調整します(秒)\n"
            text += "- BGM Volume: BGMの音量\n"
            text += "- Wav Splits: WAVの音量による分割数\n"
            text += "- Wav Volume: WAVの最大音量\n\n"

            text += "Headerタブでヘッダー情報を編集できます\n"
            text += "Chipsタブでチップ音のファイル名、音量、開始時間を編集できます\n"
            gr.TextArea(text, show_label=False)
        if dev_config.development:
            with gr.TabItem("Develpment"):
                with gr.Tabs():
                    with gr.TabItem("Separate Audio"):
                        with gr.Row():
                            with gr.Column():
                                add_space(1)
                                with gr.Row():
                                    dev_separate_button = gr.Button("Separate", variant="primary")
                                with gr.Row():
                                    with gr.Column(scale=5):
                                        dev_separate_audio_path_textbox = gr.Textbox(label="Separate Audio Path", value=dev_config.separate_audio_file)
                                    with gr.Column(scale=1, min_width=50):
                                        dev_separate_audio_open_button = gr.Button("Open", variant="primary")
                                dev_separate_model_dropdown = gr.Dropdown(demucs_models, value=dev_config.separate_model, label="Model")
                                dev_separate_jobs_slider = gr.Slider(0, 32, value=dev_config.separate_jobs, step=1, label="Number of Jobs")
                            with gr.Column():
                                dev_checkbox = gr.Checkbox(value=dev_config.development, label="Development", visible=False)
                                dev_separate_output = gr.Textbox(show_label=False)
                                dev_separate_drums_audio = gr.Audio(label="Drums", source="upload", type="filepath")
                                dev_separate_bass_audio = gr.Audio(label="Bass", source="upload", type="filepath")
                                dev_separate_other_audio = gr.Audio(label="Other", source="upload", type="filepath")
                                dev_separate_vocals_audio = gr.Audio(label="Vocals", source="upload", type="filepath")

    app_config_inputs = [
        project_path_textbox,
        workspace_path_textbox,
        auto_save_checkbox,
        bgm_bitrate_textbox,

        batch_download_movie_checkbox,
        batch_convert_movie_checkbox,
        batch_create_preview_checkbox,
        batch_separate_music_checkbox,
        batch_convert_to_midi_checkbox,
        batch_convert_to_dtx_checkbox,

        batch_skip_converted_checkbox,
        batch_jobs_slider,
    ]

    if dev_config.development:
        dev_config_inputs = [
            dev_checkbox,
            dev_separate_audio_path_textbox,
            dev_separate_model_dropdown,
            dev_separate_jobs_slider,
        ]

    dtx_wav_inputs = [
        dtx_hhc_wav_textbox,
        dtx_snare_wav_textbox,
        dtx_bd_wav_textbox,
        dtx_ht_wav_textbox,
        dtx_lt_wav_textbox,
        dtx_cymbal_wav_textbox,
        dtx_ft_wav_textbox,
        dtx_hho_wav_textbox,
        dtx_ride_wav_textbox,
        dtx_lc_wav_textbox,
        dtx_lp_wav_textbox,
        dtx_lbd_wav_textbox,

        dtx_hhc_volume_slider,
        dtx_snare_volume_slider,
        dtx_bd_volume_slider,
        dtx_ht_volume_slider,
        dtx_lt_volume_slider,
        dtx_cymbal_volume_slider,
        dtx_ft_volume_slider,
        dtx_hho_volume_slider,
        dtx_ride_volume_slider,
        dtx_lc_volume_slider,
        dtx_lp_volume_slider,
        dtx_lbd_volume_slider,

        dtx_hhc_offset_slider,
        dtx_snare_offset_slider,
        dtx_bd_offset_slider,
        dtx_ht_offset_slider,
        dtx_lt_offset_slider,
        dtx_cymbal_offset_slider,
        dtx_ft_offset_slider,
        dtx_hho_offset_slider,
        dtx_ride_offset_slider,
        dtx_lc_offset_slider,
        dtx_lp_offset_slider,
        dtx_lbd_offset_slider,

        dtx_hhc_pan_slider,
        dtx_snare_pan_slider,
        dtx_bd_pan_slider,
        dtx_ht_pan_slider,
        dtx_lt_pan_slider,
        dtx_cymbal_pan_slider,
        dtx_ft_pan_slider,
        dtx_hho_pan_slider,
        dtx_ride_pan_slider,
        dtx_lc_pan_slider,
        dtx_lp_pan_slider,
        dtx_lbd_pan_slider,
    ]

    inputs = [
        bgm_name_textbox,

        movie_url_textbox,
        movie_download_file_textbox,
        movie_output_file_textbox,
        thumbnail_file_textbox,
        movie_start_time_slider,
        movie_end_time_slider,
        movie_width_slider,
        movie_height_slider,
        movie_target_dbfs_slider,

        preview_output_name_textbox,
        preview_start_time_slider,
        preview_duration_slider,
        preview_fade_in_duration_slider,
        preview_fade_out_duration_slider,

        separate_model_dropdown,
        separate_jobs_slider,

        midi_input_name_textbox,
        midi_convert_model_dropdown,
        midi_resolution_slider,
        midi_threshold_slider,
        midi_segmentation_slider,
        midi_hop_length_slider,
        midi_onset_delta_slider,
        midi_disable_hh_frame_slider,
        midi_adjust_offset_count_slider,
        midi_adjust_offset_min_slider,
        midi_adjust_offset_max_slider,
        midi_velocity_max_percentile_slider,
        midi_test_offset_slider,
        midi_test_duration_slider,

        midi_bd_min_slider,
        midi_sn_min_slider,
        midi_ht_min_slider,
        midi_lt_min_slider,
        midi_ft_min_slider,

        midi_bd_range_slider,
        midi_sn_range_slider,
        midi_ht_range_slider,
        midi_lt_range_slider,
        midi_ft_range_slider,

        dtx_input_name_textbox,
        dtx_output_name_textbox,
        dtx_output_image_name_textbox,
        dtx_bpm_slider,
        dtx_chip_resolution_slider,
        dtx_bgm_resolution_slider,
        dtx_shift_time_slider,
        dtx_auto_shift_time_checkbox,
        dtx_align_nth_bd_slider,
        dtx_auto_align_nth_bd_checkbox,
        dtx_bgm_offset_time_slider,
        dtx_bgm_volume_slider,
        dtx_wav_splits_slider,
        dtx_wav_volume_slider,

        dtx_title_textbox,
        dtx_artist_textbox,
        dtx_comment_textbox,
        dtx_dlevel_slider,

        *dtx_wav_inputs,
    ]

    outputs = [
        movie_output,
        movie_input_video,
        movie_output_video,
        movie_output_audio,

        preview_output,
        preview_input_audio,
        preview_output_audio,

        separate_output,
        separate_output_audio,

        midi_output,

        dtx_output,
        dtx_output_score,
        dtx_output_image,
    ]

    workspace_open_button.click(select_workspace_gr,
                                  inputs=[],
                                  outputs=[
                                        workspace_output,
                                        workspace_path_textbox,
                                  ])

    workspace_gallery.select(select_project_gr,
                             inputs=[],
                             outputs=[
                                    workspace_output,
                                    project_path_textbox,
                                    project_image,
                                    workspace_video,
                                    *inputs,
                                    *outputs,
                             ])

    workspace_new_score_button.click(new_score_gr,
                                  inputs=[
                                        workspace_new_score_url_textbox,
                                  ],
                                  outputs=[
                                        workspace_output,
                                        project_path_textbox,
                                        project_image,
                                        *inputs
                                  ])

    workspace_reload_button.click(reload_workspace_gr,
                                  inputs=[],
                                  outputs=workspace_gallery)

    batch_convert_selected_score_button.click(batch_convert_selected_score_gr,
                                            inputs=app_config_inputs,
                                            outputs=[
                                                    base_output,
                                                    batch_output,
                                                    *inputs,
                                            ])

    batch_convert_all_score_button.click(batch_convert_all_score_gr,
                                            inputs=app_config_inputs,
                                            outputs=[
                                                    base_output,
                                                    batch_output,
                                                    *inputs,
                                            ])

    movie_download_and_convert_button.click(download_and_convert_video_gr,
                          inputs=inputs,
                          outputs=[
                                base_output,
                                movie_output,
                                movie_input_video,
                                movie_output_video,
                                movie_output_audio,
                                dtx_title_textbox,
                                dtx_artist_textbox,
                                dtx_comment_textbox,
                                project_image,
                          ])

    movie_download_button.click(download_video_gr,
                          inputs=inputs,
                          outputs=[
                                base_output,
                                movie_output,
                                movie_input_video,
                                movie_output_video,
                                movie_output_audio,
                                dtx_title_textbox,
                                dtx_artist_textbox,
                                dtx_comment_textbox,
                                project_image,
                          ])

    movie_convert_button.click(convert_video_gr,
                          inputs=inputs,
                          outputs=[
                                base_output,
                                movie_output,
                                movie_input_video,
                                movie_output_video,
                                movie_output_audio,
                          ])

    movie_refresh_button.click(reload_video_gr,
                          inputs=inputs,
                          outputs=[
                                base_output,
                                movie_output,
                                movie_input_video,
                                movie_output_video,
                                movie_output_audio,
                          ])

    preview_create_button.click(create_preview_gr,
                      inputs=inputs,
                      outputs=[
                            base_output,
                            preview_output,
                            preview_input_audio,
                            preview_output_audio,
                            preview_start_time_slider,
                      ])

    preview_reload_button.click(reload_preview_gr,
                      inputs=inputs,
                      outputs=[
                            base_output,
                            preview_output,
                            preview_input_audio,
                            preview_output_audio,
                      ])

    separate_button.click(separate_music_gr,
                          inputs=inputs,
                          outputs=[
                                base_output,
                                separate_output,
                                separate_output_audio,
                                dtx_bpm_slider,
                          ])

    midi_convert_button.click(convert_to_midi_gr,
                      inputs=inputs,
                      outputs=[
                            base_output,
                            midi_output,
                            midi_output_image,
                      ])

    midi_convert_test_button.click(convert_test_to_midi_gr,
                      inputs=inputs,
                      outputs=[
                            base_output,
                            midi_output,
                            midi_output_image,
                      ])

    midi_reset_pitch_button.click(reset_pitch_midi_gr,
                      inputs=inputs,
                      outputs=[
                            base_output,
                            midi_output,
                            midi_output_image,

                            midi_bd_min_slider,
                            midi_sn_min_slider,
                            midi_ht_min_slider,
                            midi_lt_min_slider,
                            midi_ft_min_slider,

                            midi_bd_range_slider,
                            midi_sn_range_slider,
                            midi_ht_range_slider,
                            midi_lt_range_slider,
                            midi_ft_range_slider,
                      ])

    dtx_convert_button.click(midi_to_dtx_gr,
                      inputs=inputs,
                      outputs=[
                            base_output,
                            dtx_output,
                            dtx_shift_time_slider,
                            dtx_align_nth_bd_slider,
                            dtx_output_score,
                            dtx_output_image,
                      ])

    dtx_convert_and_output_image_button.click(midi_to_dtx_and_output_image_gr,
                      inputs=inputs,
                      outputs=[
                            base_output,
                            dtx_output,
                            dtx_shift_time_slider,
                            dtx_align_nth_bd_slider,
                            dtx_output_score,
                            dtx_output_image,
                      ])

    dtx_reset_wav_button1.click(reset_dtx_wav_gr,
                      inputs=inputs,
                      outputs=[
                            base_output,
                            dtx_output,
                            *dtx_wav_inputs,
                      ])

    dtx_reset_wav_button2.click(reset_dtx_wav_gr,
                      inputs=inputs,
                      outputs=[
                            base_output,
                            dtx_output,
                            *dtx_wav_inputs,
                      ])

    if dev_config.development:
        dev_separate_audio_open_button.click(dev_select_separate_audio_gr,
                                    inputs=dev_config_inputs,
                                    outputs=[
                                            dev_separate_output,
                                            dev_separate_audio_path_textbox,
                                    ])

        dev_separate_button.click(dev_separate_audio_gr,
                        inputs=dev_config_inputs,
                        outputs=[
                                dev_separate_output,
                                dev_separate_drums_audio,
                                dev_separate_bass_audio,
                                dev_separate_other_audio,
                                dev_separate_vocals_audio,
                        ])

if __name__ == "__main__":
    demo.launch()

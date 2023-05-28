import librosa
import numpy as np
from scripts.config_utils import ProjectConfig
from scripts.debug_utils import debug_args
from scripts.media_utils import convert_audio, download_and_extract, get_tmp_dir
from scripts.convert_to_midi import adjust_offset, get_onsets, hh_note, normalize_notes, sn_note, bd_note, ht_note, lt_note, ft_note, cy_note, hho_note, ride_note, lc_note, lp_note, lbd_note
import os

import tensorflow._api.v2.compat.v1 as tf
from magenta.models.onsets_frames_transcription import audio_label_data_utils
from magenta.models.onsets_frames_transcription import configs
from magenta.models.onsets_frames_transcription import data
from magenta.models.onsets_frames_transcription import infer_util
from magenta.models.onsets_frames_transcription import train_util
import note_seq
from note_seq import midi_io

import pretty_midi

@debug_args
def convert_to_midi_with_onsets_frames(
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
        config: ProjectConfig):
    checkpoint_url = f"https://storage.googleapis.com/magentadata/models/onsets_frames_transcription/{convert_model}_checkpoint.zip"
    checkpoint_dir = f"checkpoints/{convert_model}"

    tf.compat.v1.disable_eager_execution()

    # checkpointのダウンロード/解凍
    if not os.path.exists(checkpoint_dir):
        download_and_extract(checkpoint_url, checkpoint_dir)

    drums_config = configs.CONFIG_MAP['drums']
    hparams = drums_config.hparams
    hparams.batch_size = 1

    examples = tf.placeholder(tf.string, [None])

    dataset = data.provide_batch(
        examples=examples,
        preprocess_examples=True,
        params=hparams,
        is_training=False,
        shuffle_examples=False,
        skip_n_initial_records=0)
    
    estimator = train_util.create_estimator(
    drums_config.model_fn, checkpoint_dir, hparams)

    iterator = tf.data.make_initializable_iterator(dataset)
    next_record = iterator.get_next()

    uploaded = {}
    input_name = os.path.basename(input_path)

    tmp_dir = get_tmp_dir()
    wav_input_path = os.path.join(tmp_dir, f"{input_name}.wav")
    convert_audio(input_path, wav_input_path, remove_original=False)

    with open(wav_input_path, 'rb') as f:
        uploaded[input_name] = f.read()

    to_process = []
    for fn in uploaded.keys():
        print('User uploaded file "{name}" with length {length} bytes'.format(
            name=fn, length=len(uploaded[fn])))
        wav_data = uploaded[fn]
        example_list = list(
            audio_label_data_utils.process_record(
                wav_data=wav_data,
                sample_rate=hparams.sample_rate,
                ns=note_seq.NoteSequence(),
                example_id=fn,
                min_length=0,
                max_length=-1,
                allow_empty_notesequence=True))
        assert len(example_list) == 1
        to_process.append(example_list[0].SerializeToString())
        
        print('Processing complete for', fn)

    sess = tf.Session()

    sess.run([
        tf.initializers.global_variables(),
        tf.initializers.local_variables()
    ])

    sess.run(iterator.initializer, {examples: to_process})

    def transcription_data(params):
        del params
        return tf.data.Dataset.from_tensors(sess.run(next_record))
    input_fn = infer_util.labels_to_features_wrapper(transcription_data)
    print(input_fn)

    #@title Run inference
    prediction_list = list(
        estimator.predict(
            input_fn,
            yield_single_examples=False))
    assert len(prediction_list) == 1

    sequence_prediction = note_seq.NoteSequence.FromString(
        prediction_list[0]['sequence_predictions'][0])

    # Ignore warnings caused by pyfluidsynth
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning) 

    note_seq.plot_sequence(sequence_prediction)
    note_seq.play_sequence(sequence_prediction, note_seq.midi_synth.fluidsynth,
                    colab_ephemeral=False)

    midi_io.sequence_proto_to_midi_file(sequence_prediction, output_path)

    # onsetsの取得
    onsets, onset_env, C, sr, frame_time = get_onsets(input_path, offset, duration, hop_length, onset_delta)

    # MIDIファイルの作成
    midi_output = pretty_midi.PrettyMIDI(resolution=bpm * resolution, initial_tempo=bpm)

    # MIDIファイルのロード
    midi_input = pretty_midi.PrettyMIDI(output_path)

    # ドラムトラックの読み込み
    track_input = pretty_midi.Instrument(program=0, is_drum=True)
    for instrument in midi_input.instruments:
        for note in instrument.notes:
            track_input.notes.append(note)

    # 音量ノーマライズ
    normalize_notes(track_input, velocity_max_percentile)

    note_volumes = {
        sn_note: config.e_gmd_sn_volume,
        bd_note: config.e_gmd_bd_volume,
        ht_note: config.e_gmd_ht_volume,
        hho_note: config.e_gmd_hho_volume,
        ride_note: config.e_gmd_ride_volume,
    }

    # 音量補正
    track_output = pretty_midi.Instrument(program=0, is_drum=True)
    for note in track_input.notes:
        note: pretty_midi.Note = note
        volume = note_volumes.get(note.pitch, 0)
        note.velocity = int(note.velocity * volume / 100)

        if note.velocity > 0:
            note.start_frame = int(note.start / frame_time)
            track_output.notes.append(note)

    # offsetの調整
    #adjust_offset(track_output, onsets, frame_time, adjust_offset_count, adjust_offset_min, adjust_offset_max)

    # MIDIファイルの書き込み
    midi_output.instruments.append(track_output)
    midi_output.write(output_path)

    print(f"MIDI convert is complete. {output_path}")

from scripts.config_utils import ProjectConfig
from scripts.debug_utils import debug_args
from scripts.media_utils import convert_audio, download_and_extract, get_tmp_dir
import os

import tensorflow._api.v2.compat.v1 as tf
from magenta.models.onsets_frames_transcription import audio_label_data_utils
from magenta.models.onsets_frames_transcription import configs
from magenta.models.onsets_frames_transcription import data
from magenta.models.onsets_frames_transcription import infer_util
from magenta.models.onsets_frames_transcription import train_util
import note_seq
from note_seq import midi_io

@debug_args
def convert_to_midi_with_onsets_frames(
        output_path,
        input_path,
        offset,
        duration,
        bpm,
        resolution,
        convert_model,
        config: ProjectConfig):
    checkpoint_url = f"https://storage.googleapis.com/magentadata/models/onsets_frames_transcription/{convert_model}_checkpoint.zip"
    checkpoint_dir = f"checkpoints/{convert_model}"

    tf.compat.v1.disable_eager_execution()

    # checkpointのダウンロード/解凍
    if not os.path.exists(checkpoint_dir):
        download_and_extract(checkpoint_url, checkpoint_dir)

    config = configs.CONFIG_MAP['drums']
    hparams = config.hparams
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
    config.model_fn, checkpoint_dir, hparams)

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

    print(f"MIDI convert is complete. {output_path}")
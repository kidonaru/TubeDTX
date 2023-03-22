import librosa
import numpy as np

from scripts.debug_utils import debug_args

# https://www.wizard-notes.com/entry/music-analysis/compute-bpm
@debug_args
def compute_bpm(input_path):
    outputs = ""
    offset = 0.0
    duration = None
    x_sr = 200
    bpm_min, bpm_max = 60, 240

    # 楽曲の信号を読み込む
    y, sr = librosa.load(input_path, offset=offset, duration=duration, mono=True)

    # ビート検出用信号の生成
    # リサンプリング & パワー信号の抽出
    x = np.abs(librosa.resample(y=y, orig_sr=sr, target_sr=x_sr)) ** 2
    x_len = len(x)

    # 各BPMに対応する複素正弦波行列を生成
    M = np.zeros((bpm_max, x_len), dtype=np.complex128)
    for bpm in range(bpm_min, bpm_max): 
        thete = 2 * np.pi * (bpm/60) * (np.arange(0, x_len) / x_sr)
        M[bpm] = np.exp(-1j * thete)

    # 各BPMとのマッチング度合い計算
    #（複素正弦波行列とビート検出用信号との内積）
    x_bpm = np.abs(np.dot(M, x))

    # BPM　を算出
    bpm = np.argmax(x_bpm)

    print(f"BPM estimation is complete. {bpm}")

    return int(bpm)

# https://www.wizard-notes.com/entry/music-analysis/highlight-detection-by-rms
@debug_args
def compute_chorus_time(
        input_path,
    ):

    sr = 44100

    # オーディオファイルを信号データとして読み込み
    # 今回はモノラル信号（中央定位成分）を利用
    y, sr = librosa.load(input_path, sr=sr, mono=True, duration=120)

    # 特徴量算出用のパラメタ
    frame_length = 65536 # 特徴量を１つ算出するのに使うサンプル数
    hop_length   = 16384 # 何サンプルずらして特徴量を算出するかを決める変数

    # RMS：短時間ごとのエネルギーの大きさを算出
    rms   = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    rms   /= np.max(rms) # [0.0. 1.0]に正規化

    # スペクトル重心：短時間ごとの音色の煌びやかさを算出
    sc    = librosa.feature.spectral_centroid(y=y, n_fft=frame_length, hop_length=hop_length)[0]
    sc    /= np.max(sc) # [0.0. 1.0]に正規化

    # 最大値探索で無視する,先頭と末尾のデータ数を指定
    n_ignore = 10 

    # サビらしさ特徴量時系列データ sc+rms より、
    # 最もサビらしいインデックスを最大値探索で算出
    # 念のため、2, 3番目に大きい値をとるインデックスも算出する
    indices = np.argsort((sc+rms)[n_ignore:-n_ignore])[::-1] + n_ignore
    # 最大値のみであれば、np.max((sc+rms)[n_ignore:-n_ignore]) でよい

    # 特徴量時系列データのインデックスと時間（秒）の対応関係
    # 今回は、rmsとscはhop_lengthが同じなので以下でよい
    times = np.floor(librosa.times_like(sc, hop_length=hop_length, sr=sr))

    # 推定サビ時刻（秒）を算出
    chorus_estimated_time = times[indices[0]]

    print(f"Chorus time estimation is complete. {chorus_estimated_time}")

    return chorus_estimated_time

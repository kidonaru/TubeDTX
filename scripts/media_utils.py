import os
import random
import re
import shutil
import string
import subprocess
import time
import zipfile
from moviepy.video.fx.crop import crop
from moviepy.editor import AudioFileClip, AudioClip, VideoFileClip
from moviepy.audio.fx.all import audio_fadein, audio_fadeout
from moviepy.config import get_setting
from typing import Tuple
from pytube import YouTube

from pytube.cipher import get_throttling_function_code
import requests

from bs4 import BeautifulSoup

from scripts.debug_utils import debug_args

def randomname(n):
   return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

@debug_args
def get_tmp_dir():
    tmp_dir = os.path.join(".", "tmp")
    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)
    return tmp_dir

@debug_args
def get_tmp_file_path(ext):
    tmp_dir = os.path.join(".", "tmp")
    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)

    tmp_file_path = os.path.join(tmp_dir, randomname(10) + ext)
    return tmp_file_path

@debug_args
def get_video_info(url):
    # YouTubeのページを取得
    response = requests.get(url)

    # BeautifulSoupオブジェクトを作成
    soup = BeautifulSoup(response.text, 'html.parser')

    # ページタイトルを取得
    title = soup.find('title').text

    # " - YouTube"の部分を削除
    title = title.replace(" - YouTube", "")

    # サムネイル画像のURLを取得
    thumbnail_url = soup.find("meta", property="og:image")["content"]

    return title, thumbnail_url

@debug_args
def download_video(url, output_path, thumbnail_path):
    output_dir, filename = os.path.split(output_path)
    duration = 0

    yt = YouTube(url)
    video = yt.streams.get_highest_resolution()
    original_title, thumbnail_url = get_video_info(url)
    title, artist = extract_title_and_artist(original_title)
    if artist == "":
        artist = yt.author
    video.download(output_path=output_dir, filename=filename)

    print(f"Video download is complete. {output_path}")

    with VideoFileClip(output_path) as video:
        video_size = video.size
        duration = video.duration

    print(f"Thumbnail downloading. {thumbnail_url}")

    response = requests.get(thumbnail_url)
    with open(thumbnail_path, "wb") as file:
        file.write(response.content)

    print(f"Thumbnail download is complete. {thumbnail_path}")

    return original_title, title, artist, duration, video_size[0], video_size[1]

@debug_args
def trim_and_crop_video(input_path, output_path, start_time, end_time, width, height, bitrate):
    # パラメータが全て0の場合は何もしない
    if start_time == 0.0 and end_time == 0.0 and width == 0 and height == 0:
        print(f"Skip trim_and_crop_video. {input_path}")
        return input_path

    with VideoFileClip(input_path) as video:
        if start_time > 0.0 or end_time > 0.0:
            end_time = end_time if end_time > 0.0 else video.duration
            video = video.subclip(start_time, end_time)

        if width > 0 or height > 0:
            width = width if width > 0 else video.w
            height = height if height > 0 else video.h
            print(f"clipping {video.w}x{video.h} -> {width}x{height}")
            video = crop(
                video,
                x_center=video.w/2,
                y_center=video.h/2,
                width=width,
                height=height)
        tmp_file = get_tmp_file_path(".m4a")
        video.write_videofile(output_path, temp_audiofile=tmp_file, codec="libx264", audio_codec="aac", audio_bitrate=bitrate)
        video.close()

    print(f"Video clipping is complete. {output_path}")
    return output_path

@debug_args
def get_audio_volume(audio_file):
    ffmpeg = get_setting("FFMPEG_BINARY")
    null_device = '/dev/null' if os.name == 'posix' else 'NUL'
    cmd = [ffmpeg, '-i', audio_file, '-af', 'volumedetect', '-f', 'null', null_device]
    print(" ".join(cmd))

    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
    _, stderr = process.communicate()
    print(stderr)

    source_dBFS = float(stderr.split("mean_volume: ")[1].split(" dB")[0])
    return source_dBFS

@debug_args
def normalize_audio(audio_file, target_dBFS, bitrate):
    ext = os.path.splitext(audio_file)[1]
    tmp_input_file = get_tmp_file_path(ext)
    tmp_output_file = get_tmp_file_path(ext)

    shutil.move(audio_file, tmp_input_file)

    source_dBFS = get_audio_volume(tmp_input_file)
    print(f"Normalize audio. {source_dBFS}dB -> {target_dBFS}dB")

    change_in_dBFS = target_dBFS - source_dBFS

    ffmpeg = get_setting("FFMPEG_BINARY")
    cmd = [ffmpeg, '-y', '-i', tmp_input_file, '-af', f'volume={change_in_dBFS}dB', '-ab', bitrate, tmp_output_file]
    print(" ".join(cmd))

    subprocess.run(cmd)

    os.remove(tmp_input_file)
    os.rename(tmp_output_file, audio_file)

@debug_args
def extract_audio(input_path, output_path, target_dbfs, bitrate):
    with VideoFileClip(input_path) as video:
        audio = video.audio
        audio.write_audiofile(output_path, bitrate=bitrate)
        audio.close()

    if target_dbfs < 0.0:
        normalize_audio(output_path, target_dbfs, bitrate)

    print(f"Audio extract is complete. {output_path}")

@debug_args
def convert_audio(input_file, output_file, bitrate=None, remove_original=True):
    tmp_input_file = get_tmp_file_path(os.path.splitext(input_file)[1])
    tmp_output_file = get_tmp_file_path(os.path.splitext(output_file)[1])

    if remove_original:
        shutil.move(input_file, tmp_input_file)
    else:
        shutil.copy(input_file, tmp_input_file)

    ffmpeg = get_setting("FFMPEG_BINARY")
    cmd = [ffmpeg, '-y', '-i', tmp_input_file]

    if bitrate is not None:
        cmd.append('-ab')
        cmd.append(bitrate)

    cmd.append(tmp_output_file)

    print(" ".join(cmd))

    subprocess.run(cmd)

    os.remove(tmp_input_file)

    if os.path.exists(output_file):
        os.remove(output_file)
    os.rename(tmp_output_file, output_file)

@debug_args
def create_preview_audio(
        input_path,
        output_path,
        start_time,
        preview_time,
        fade_in_duration,
        fade_out_duration,
        bitrate):
    with AudioFileClip(input_path) as audio:
        duration = audio.duration
        if duration > 0:
            start_time = min(start_time, duration - preview_time)

        trimmed_audio: AudioClip = audio.subclip(start_time, start_time + preview_time)
        trimmed_audio = trimmed_audio.fx(audio_fadein, fade_in_duration)
        trimmed_audio = trimmed_audio.fx(audio_fadeout, fade_out_duration)
        trimmed_audio.write_audiofile(output_path, bitrate=bitrate)
        trimmed_audio.close()

    print(f"Preview creation is complete. {output_path}")

@debug_args
def extract_title_and_artist(youtube_title: str) -> Tuple[str, str]:
    title_patterns = [
        re.compile(r'(?P<title>[^/]+)/(?P<artist>.+)'),
        re.compile(r'(?P<title>.+) - (?P<artist>.+)'),
        re.compile(r'(?P<title>.+)／(?P<artist>.+)'),
        re.compile(r'「(?P<title>[^」]+)」を歌ってみた(?P<artist>.+)'),
    ]

    youtube_title = re.sub(r'【[^【】]+】', '', youtube_title).strip()
    youtube_title = re.sub(r'\[[^\[\]]+\]', '', youtube_title).strip()

    for pattern in title_patterns:
        match = pattern.search(youtube_title)
        if match:
            title = match.group("title").strip()
            artist = match.group("artist").strip() if "artist" in pattern.groupindex else ""

            if "feat." in title and artist != "":
                title, artist = artist, title

            return title, artist

    return youtube_title, ""

@debug_args
def download_and_extract(url, target_path):
    # URLからzipファイルをダウンロード
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise Exception(f"ダウンロードに失敗しました。 url: {url}")

    tmp_dir = get_tmp_dir()
    zip_path = os.path.join(tmp_dir, "download.zip")

    if os.path.exists(zip_path):
        os.remove(zip_path)

    # ダウンロードしたファイルを保存
    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)

    # zipファイルを解凍
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_path)

    # zipファイルを削除
    os.remove(zip_path)

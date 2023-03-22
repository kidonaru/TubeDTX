import os
import re
import shutil
import time
import mock
from moviepy.video.fx.crop import crop
from moviepy.editor import AudioFileClip, AudioClip, VideoFileClip, VideoClip
from moviepy.audio.fx.all import audio_fadein, audio_fadeout

from pytube.cipher import get_throttling_function_code
import requests

from scripts.debug_utils import debug_args

def patched_throttling_plan(js: str):
    """Patch throttling plan, from https://github.com/pytube/pytube/issues/1498"""
    raw_code = get_throttling_function_code(js)

    transform_start = r"try{"
    plan_regex = re.compile(transform_start)
    match = plan_regex.search(raw_code)

    #transform_plan_raw = find_object_from_startpoint(raw_code, match.span()[1] - 1)
    transform_plan_raw = js

    # Steps are either c[x](c[y]) or c[x](c[y],c[z])
    step_start = r"c\[(\d+)\]\(c\[(\d+)\](,c(\[(\d+)\]))?\)"
    step_regex = re.compile(step_start)
    matches = step_regex.findall(transform_plan_raw)
    transform_steps = []
    for match in matches:
        if match[4] != '':
            transform_steps.append((match[0],match[1],match[4]))
        else:
            transform_steps.append((match[0],match[1]))

    return transform_steps

@debug_args
def get_video_info(url):
    title = ""
    thumbnail_url = ""
    with mock.patch('pytube.cipher.get_throttling_plan', patched_throttling_plan):
        from pytube import YouTube
        yt = YouTube(url)
        time.sleep(1) # 早すぎるとエラー起きやすい気がする
        title = yt.title
        thumbnail_url = yt.thumbnail_url

    return title, thumbnail_url

@debug_args
def download_video(url, output_path, thumbnail_path):
    output_dir, filename = os.path.split(output_path)

    title = ""
    duration = 0
    thumbnail_url = ""
    with mock.patch('pytube.cipher.get_throttling_plan', patched_throttling_plan):
        from pytube import YouTube
        yt = YouTube(url)
        video = yt.streams.get_highest_resolution()
        title = yt.title
        thumbnail_url = yt.thumbnail_url
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

    return title, duration, video_size[0], video_size[1]

@debug_args
def trim_and_crop_video(input_path, output_path, start_time, end_time, width, height):
    # パラメータが全て0の場合はコピーのみ
    if start_time == 0.0 and end_time == 0.0 and width == 0 and height == 0:
        shutil.copyfile(input_path, output_path)
        print(f"Video copy is complete. {output_path}")
        return

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
        video.write_videofile(output_path)
        video.close()

    print(f"Video clipping is complete. {output_path}")

@debug_args
def extract_audio(input_path, output_path):
    with VideoFileClip(input_path) as video:
        audio = video.audio
        audio.write_audiofile(output_path)
        audio.close()

    print(f"Audio extract is complete. {output_path}")

@debug_args
def create_preview_audio(
        input_path,
        output_path,
        start_time,
        preview_time,
        fade_in_duration,
        fade_out_duration
    ):

    with AudioFileClip(input_path) as audio:
        duration = audio.duration
        if duration > 0:
            start_time = min(start_time, duration - preview_time)

        trimmed_audio: AudioClip = audio.subclip(start_time, start_time + preview_time)
        trimmed_audio = trimmed_audio.fx(audio_fadein, fade_in_duration)
        trimmed_audio = trimmed_audio.fx(audio_fadeout, fade_out_duration)
        trimmed_audio.write_audiofile(output_path)
        trimmed_audio.close()

    print(f"Preview creation is complete. {output_path}")

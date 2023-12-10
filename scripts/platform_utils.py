import os
import platform
import queue
import shutil
import tkinter
from tkinter import filedialog
import threading

def safe_remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def force_copy_file(input_path, output_path):
    safe_remove_file(output_path)
    shutil.copyfile(input_path, output_path)

# Keep a reference to the ctypes function pointer to avoid deallocation
run_askdirectory_ctypes = None
result_askdirectory_queue = queue.Queue()
askdirectory_initialdir = ""

def run_askdirectory():
    root = tkinter.Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    folder_path = filedialog.askdirectory(initialdir=askdirectory_initialdir)
    result_askdirectory_queue.put(folder_path)
    root.destroy()
    return 0

def get_folder_path(initialdir):
    global run_askdirectory_ctypes
    global askdirectory_initialdir

    askdirectory_initialdir = initialdir

    if platform.system() == "Darwin":  # macOS
        import ctypes
        if run_askdirectory_ctypes is None:
            run_askdirectory_ctypes = ctypes.PYFUNCTYPE(ctypes.c_int)(run_askdirectory)
        ctypes.pythonapi.Py_AddPendingCall(run_askdirectory_ctypes, None)
    else:  # Windows and other platforms
        main_thread = threading.Thread(target=run_askdirectory)
        main_thread.start()
        main_thread.join()

    # Wait for the result from the main thread
    folder_path = result_askdirectory_queue.get()

    folder_path = folder_path.replace("¥", os.path.sep).replace("\\", os.path.sep).replace("/", os.path.sep)
    return folder_path


# Keep a reference to the ctypes function pointer to avoid deallocation
run_askaudiofile_ctypes = None
result_askaudiofile_queue = queue.Queue()
askaudiofile_initialdir = ""

if platform.system() == "Darwin":  # macOS
    audio_file_types = []
else:  # Windows and other platforms
    audio_file_types = [
        ("Audio files", "*.mp3;*.wav;*.ogg;*.flac"),
        ("MP3 files", "*.mp3"),
        ("WAV files", "*.wav"),
        ("OGG files", "*.ogg"),
        ("FLAC files", "*.flac"),
        ("All files", "*.*"),
    ]

def run_askaudiofile():
    root = tkinter.Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()

    audio_file = filedialog.askopenfilename(
        title="Open audio file",
        filetypes=audio_file_types,
        #initialdir=askaudiofile_initialdir,
    )
    result_askaudiofile_queue.put(audio_file)
    result_askaudiofile_queue.put("")
    root.destroy()
    return 0

def get_audio_path(initialdir):
    global run_askaudiofile_ctypes
    global askaudiofile_initialdir

    askaudiofile_initialdir = initialdir or ""

    if platform.system() == "Darwin":  # macOS
        import ctypes
        if run_askaudiofile_ctypes is None:
            run_askaudiofile_ctypes = ctypes.PYFUNCTYPE(ctypes.c_int)(run_askaudiofile)
        ctypes.pythonapi.Py_AddPendingCall(run_askaudiofile_ctypes, None)
    else:  # Windows and other platforms
        main_thread = threading.Thread(target=run_askaudiofile)
        main_thread.start()
        main_thread.join()

    # Wait for the result from the main thread
    audio_file: str = result_askaudiofile_queue.get()

    audio_file = audio_file.replace("¥", os.path.sep).replace("\\", os.path.sep).replace("/", os.path.sep)
    return audio_file

# 動画ファイルを選択するダイアログを表示する
# Keep a reference to the ctypes function pointer to avoid deallocation
run_askvideofile_ctypes = None
result_askvideofile_queue = queue.Queue()
askvideofile_initialdir = ""

if platform.system() == "Darwin":  # macOS
    video_file_types = []
else:
    video_file_types = [
        ("Video files", "*.mp4;*.mkv;*.avi;*.webm"),
        ("MP4 files", "*.mp4"),
        ("MKV files", "*.mkv"),
        ("AVI files", "*.avi"),
        ("WebM files", "*.webm"),
        ("All files", "*.*"),
    ]

def run_askvideofile():
    root = tkinter.Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()

    video_file = filedialog.askopenfilename(
        title="Open video file",
        filetypes=video_file_types,
        #initialdir=askvideofile_initialdir,
    )
    result_askvideofile_queue.put(video_file)
    result_askvideofile_queue.put("")
    root.destroy()
    return 0

def get_video_path(initialdir):
    global run_askvideofile_ctypes
    global askvideofile_initialdir

    askvideofile_initialdir = initialdir or ""

    if platform.system() == "Darwin":  # macOS
        import ctypes
        if run_askvideofile_ctypes is None:
            run_askvideofile_ctypes = ctypes.PYFUNCTYPE(ctypes.c_int)(run_askvideofile)
        ctypes.pythonapi.Py_AddPendingCall(run_askvideofile_ctypes, None)
    else:  # Windows and other platforms
        main_thread = threading.Thread(target=run_askvideofile)
        main_thread.start()
        main_thread.join()

    # Wait for the result from the main thread
    video_file: str = result_askvideofile_queue.get()

    video_file = video_file.replace("¥", os.path.sep).replace("\\", os.path.sep).replace("/", os.path.sep)
    return video_file


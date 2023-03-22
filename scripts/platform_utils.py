import os
import platform
import queue
import tkinter
from tkinter import filedialog
import threading

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

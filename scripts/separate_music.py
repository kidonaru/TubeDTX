
import platform
import subprocess as sp

from scripts.debug_utils import debug_args

@debug_args
def separate_music(model, output_dir, input_path, jobs):
    if platform.system() == "Windows":
        cmd = ["venv\Scripts\python", "-m", "demucs.separate", "-o", output_dir, "-n", model, "-j", str(jobs)]
    else:
        cmd = ["python3", "-m", "demucs.separate", "-o", output_dir, "-n", model, "-j", str(jobs)]
    cmd.append(input_path)
    print(" ".join(cmd))

    p = sp.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise Exception(f'{p.stderr}\n{p.stdout}\n{" ".join(cmd)}\n')

    print(p.stdout)
    print(f"Music separation is complete. {output_dir}")


import os
import platform
import shutil
import subprocess as sp

from scripts.debug_utils import debug_args
from scripts.platform_utils import force_copy_file
from scripts.media_utils import get_tmp_dir, get_tmp_file_path

@debug_args
def separate_music(model, input_path, output_dir, jobs, drums_only):
    # 全角文字が入ってるとコンバートに失敗するので作業ディレクトリに移動する
    tmp_dir = get_tmp_dir()
    tmp_input_path = get_tmp_file_path(os.path.splitext(input_path)[1])
    force_copy_file(input_path, tmp_input_path)

    if platform.system() == "Windows":
        cmd = ["venv\Scripts\python", "-m", "demucs.separate", "-o", tmp_dir, "-n", model, "-j", str(jobs)]
    else:
        cmd = ["python3", "-m", "demucs.separate", "-o", tmp_dir, "-n", model, "-j", str(jobs)]
    cmd.append(tmp_input_path)
    print(" ".join(cmd))

    p = sp.run(cmd, capture_output=True, text=True)

    if p.returncode != 0:
        raise Exception(f'{p.stderr}\n{p.stdout}\n{" ".join(cmd)}\n')

    # 出力先に移動
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if drums_only:
        files = ["drums.wav"]
    else:
        files = ["drums.wav", "bass.wav", "other.wav", "vocals.wav"]

    output_files = []
    for file in files:
        basename_without_ext = os.path.splitext(os.path.basename(tmp_input_path))[0]
        tmp_output_path = os.path.join(tmp_dir, model, basename_without_ext, file)
        output_path = os.path.join(output_dir, file)
        force_copy_file(tmp_output_path, output_path)
        output_files.append(output_path)

    # 一時ファイルの削除
    os.remove(tmp_input_path)
    shutil.rmtree(os.path.join(tmp_dir, model, basename_without_ext))

    print(p.stdout)
    print(f"Music separation is complete. {output_dir}")

    return output_files

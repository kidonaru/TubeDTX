# TubeDTX

TubeDTXは、YouTubeの動画からDTX譜面を作成するアプリケーションです。


## 概要

このアプリケーションでは、動画のダウンロード、プレビューファイルの作成、ドラム音の分離、MIDIへ変換、DTXファイルへの変換といったDTX譜面作成に必要な一通りの工程を行えます。


## 機能

1. 動画ファイルのダウンロード、開始/終了時間の修正、クリッピング
1. サビ時間の推定、プレビュー音声ファイルの作成
1. 音声ファイルからドラム音の抽出、BPMの推定
1. ドラム音をMIDIへ変換
1. MIDIをDTXフォーマットへ変換


## 未実装箇所

1. 採譜の精度
   - 現状ハイハットクローズ、バスドラム、スネア、一部タムの採譜にのみ対応しています
1. ノーツの編集
   - 作成機能のみで編集はできません。DTXCreatorを使用して編集してください
1. 可変BPMの対応


## インストール方法


### Windows

1. [Python 3.10.6](https://www.python.org/downloads/release/python-3106/)をインストールしてください。
   "Windows installer (64-bit)"からインストーラーをダウンロードできます。
   インストール時に "Add Python to PATH" にチェックを入れてください。
1. [git](https://git-scm.com/download/win)の最新をインストールします。
1. コマンドプロンプトを起動して任意のディレクトリに移動します。
   `C:\tools`などがおすすめです。
   ```
   mkdir C:\tools
   cd C:\tools
   ```
1. TubeDTXリポジトリをクローンします。
   ```
   git clone https://github.com/kidonaru/TubeDTX.git
   ```
1. `setup.bat`を実行してセットアップを行います。
   ```
   cd TubeDTX
   setup.bat
   ```
   `All complate!!! plass any key...`と表示されれば成功です。
1. `run.bat`を実行します。 (エクスプローラからの起動も可能です)
   ```
   run.bat
   ```
   `Running on local URL:  http://127.0.0.1:7860`と表示されれば成功です。
   ブラウザで http://127.0.0.1:7860 にアクセスするとアプリ画面が表示されます。


### Mac

1. gitとPython 3.10とtkinterをインストールしてください
   ```
   brew install git python@3.10 python-tk@3.10
   ```
1. コンソールを起動して任意のディレクトリに移動します。
   ```
   cd ~
   ```
1. TubeDTXリポジトリをクローンします。
   ```
   git clone https://github.com/kidonaru/TubeDTX.git
   ```
1. `setup.sh`を実行してセットアップを行います、
   ```
   cd TubeDTX
   ./setup.sh
   ```
   `All complate!!! plass any key...`と表示されれば成功です。
1. `run.sh`を実行します。 (Finderからの起動も可能です)
   ```
   ./run.sh
   ```
   `Running on local URL:  http://127.0.0.1:7860`と表示されれば成功です。
   ブラウザで http://127.0.0.1:7860 にアクセスするとアプリ画面が表示されます。


### 更新手順

クローンしたTubeDTXを最新にしたい場合は、Windows環境は`update.bat`を、Macは`update.sh`を実行すると最新に更新されます。


## 使い方

各作業フローごとにタブが分かれています。

"0. Workspace"タブから一つづつ工程を進めていくと譜面ができます。

使い方の参考動画: https://www.youtube.com/watch?v=f9Dzy4mn3mI


1. 譜面のディレクトリを開く
   - "0. Workspace"タブを開きます
   - "Select"ボタンを押して、作成する譜面を格納するディレクトリを選択します
   - DTXManiaの譜面格納フォルダにDTXFiles.workなどを作ってそこを指定すると確認しやすいです
   - "New Score from YouTube URL"に新しい譜面を作成する元となるYouTube動画のURLを入力してください
   - "New"ボタンを押すと、新規で譜面ディレクトリが作成されます
1. 動画ファイルのダウンロードと変換
   - "1. Download Movie"タブを開きます
   - "Download & Convert"ボタンを押して、動画をダウンロードして、変換を行います
   - 必要に応じて、動画の切り取り時間やクリップサイズを調整して"Convert"ボタンを押します
1. プレビュー音声ファイルの作成
   - "2. Create Preview File"タブを開きます
   - "Create"ボタンを押して、サビ時間を推定してプレビュー用の音声ファイルを作成します
   - 必要に応じて開始時間などを調整して、"Create"ボタンを押して更新します
1. ドラム音の分離
   - "3. Separate Music"タブを開きます
   - "Separate"ボタンを押して、BGMからドラム音の分離を開始します
   - 1分以上かかるのでしばらく待ちます
1. MIDIへの変換
   - "4. Convert to MIDI"タブを開きます
   - "Convert"ボタンを押して、分離した音声ファイルをMIDIに変換します
1. DTXへの変換
   - "5. Convert to DTX"タブを開きます
   - 必要に応じて、ヘッダー情報などを調整します
   - "Convert"ボタンを押して、MIDIファイルをDTXに変換します
1. アプリ上で確認
   - DTXManiaの譜面に対応したアプリを起動して譜面を確認します
   - 問題がなければDTXCreatorで譜面を編集して完成させてください


### Batch処理

複数のタブの処理を一括で実行したり、複数譜面に対して一括で変換をかけたりなどができます。


#### 新規譜面を一括で変換する

- "0. Workspace"タブ内の"Base"タブを開きます
- "New Score from YouTube URL"に新規作成したい譜面のURLを入れて、"New"ボタンで譜面ディレクトリを作成します
- "0. Workspace"タブ内の"Batch"タブを開きます
- 全てのタブ名にチェックを入れます
- "Skip Converted"のチェックを入れて、既存の譜面は変換しないようにします
- "Batch Convert All Score"を押すと、ワークスペース中の新規譜面に対して変換処理が走ります


## 注意事項

このアプリケーションは、趣味の範囲での使用目的で作成されており、商用利用は推奨されません。


## 補足


### バスドラムの位置がずれる場合

"5. Convert to DTX"タブの"Chips 1"タブを開いてBassDrumのOffsetを変えるとバスドラムのチップ位置を調整できます。
"Base"タブの"BGM Offset Time"を調整するのも有効です。

ある程度一致させたらDTXCreatorで手動調整してください。


### チップ音のコピー機能

TubeDTXをクローンしたディレクトリ内のresourcesフォルダにチップ音ファイルを配置すると、変換時に譜面フォルダに自動的にコピーされます。

`chips\bd.xa`の指定をすると`TubeDTX\resources\chips\bd.xa`のファイルがコピーされます。


### デフォルト設定機能

チップ音を自前のファイル名にしたい場合などは、一度譜面を作ったら譜面ディレクトリ内の`tube_dtx_config.json`をコピーししてresourcesフォルダに配置すると、次回以降その設定がデフォルトとして読み込まれます。

特定の設定項目以外は変えたくない場合は、jsonを編集して不要な項目を削除すれば、削除した項目はアプリ側のデフォルト設定値になります。


### UIをダークモードにする

http://127.0.0.1:7860/?__theme=dark でアクセスすればダークモードになります


### Windows版 GPU版のインストール

NVIDIAのGPUを使用している場合はGPU版もインストール可能ですが、オススメはしません。トラブルの起きやすいところなので。

一応手順のメモ。

1. PowerShell を管理者として開いて下記コマンドを入力します。
   ```
   Set-ExecutionPolicy Unrestricted
   ```
1. CUDA 11.7をインストールします。
1. 管理者ではないPowerShellを開いて、下記コマンドを実行します。
   ```
   cd C:\tools\TubeDTX
   Remove-Item -Recurse -Force venv
   python.exe -m venv venv
   .\venv\Scripts\activate

   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
   pip install --upgrade -r requirements.txt
   ```
1. `run.bat`を実行


## 質問など

@kidonaruまでDMしてください
可能な範囲で答えます

https://twitter.com/kidonaru


## Credits

- DTXMania - https://dtxmania.net/
- Demucs - https://github.com/facebookresearch/demucs
- Wizard Notes - https://www.wizard-notes.com/
- ChatGPT - https://openai.com/blog/chatgpt

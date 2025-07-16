# multi_core演習
gem5 シミュレーションによるCPU/キャッシュ性能評価
このプロジェクトは、gem5 シミュレータを使用して、異なるCPUおよびキャッシュ構成下でのSPLASH-2ベンチマークの実行時間を評価するためのものです。

1. プロジェクト概要
本プロジェクトは、以下の主要なスクリプトで構成されています。

run_simulation.py: gem5 シミュレーションを実行し、指定されたCPUおよびキャッシュ構成でSPLASH-2ベンチマークを実行します。

collect_results.py: シミュレーション結果ディレクトリから stats.txt ファイルを読み込み、各ベンチマークの実行時間（sim_seconds）を抽出し、ベンチマークごとに個別のCSVファイルとして集計します。

filtered_data.csv (または data.csv): シミュレーションに用いるCPUおよびキャッシュ構成パラメータを定義したCSVファイル。

2. 目的
異なるCPUクロック周波数、L1/L2キャッシュサイズ、L1/L2アソシアティビティ、L2レイテンシの組み合わせが、SPLASH-2ベンチマークの実行時間にどのような影響を与えるかを評価します。特に、シミュレーション時間の予測と、その予測に基づいた長時間のシミュレーションのスキップ機能も含まれています。

3. 前提条件
このプロジェクトを実行するには、以下のソフトウェアと環境が必要です。

Linux 環境: gem5 は通常 Linux 環境で動作します。

gem5 シミュレータ: build/ALPHA/gem5.opt がビルド済みであること。

SPLASH-2 ベンチマーク: コンパイル済みであり、スクリプトで指定されたパス（例: ./splash2/fft/FFT）に配置されていること。

Python 3: スクリプトの実行に必要です。

pandas ライブラリ: Pythonスクリプト内でCSVファイルの読み書きに使用します。

pip install pandas

4. セットアップ
4.1. gem5 のビルド
gem5 のソースコードがあるディレクトリに移動し、以下のコマンドでビルドします。

scons build/ALPHA/gem5.opt -j$(nproc)

4.2. SPLASH-2 ベンチマークの準備
SPLASH-2ベンチマークのソースコードをダウンロードし、コンパイルしてください。コンパイル後、実行ファイルが run_simulation.py 内で指定されているパス（例: ./splash2/fft/FFT, ./splash2/fmm/FMM など）に配置されていることを確認してください。

特に fmm ベンチマークの場合、入力ファイルも必要です。
例: ./splash2/fmm/inputs/input.2048.p{CORE}

4.3. 入力パラメータCSVファイルの準備
run_simulation.py が読み込む filtered_data.csv (または data.csv) を make_data.py スクリプトを実行して、用意してください。実行後のCSVファイルには、以下の列が含まれています。

Core Number

CPU clock (GHz)

L1 Cache Size (KB)

L1 Associativity

L2 Cache Size (KB)

L2 Associativity

L2 latency (cycles)

5. シミュレーションの実行
run_simulation.py スクリプトを実行して、gem5 シミュレーションを開始します。

python run_simulation.py

このスクリプトは、filtered_data.csv に定義された各構成と、run_simulation.py 内で定義された各ベンチマークに対してシミュレーションを実行します。

シミュレーションの進行状況と、予測される実行時間、スキップされたシミュレーションに関するメッセージがターミナルに表示されます。

各シミュレーションの結果は、./results_simulations ディレクトリ内の、構成とベンチマーク名に基づいたサブディレクトリに保存されます（例: results_simulations/core16_L1-16KB-A32_L2-2048KB-A64_Lat2_Bench-fft/stats.txt）。

各シミュレーションの完了後、stats.txt から抽出された sim_seconds の値がターミナルに表示されます。

6. 結果の集計
シミュレーションが完了したら、collect_results.py スクリプトを実行して結果を集計します。

python collect_results.py

このスクリプトは、./results_simulations ディレクトリ内のすべてのシミュレーション結果を走査し、各ベンチマークの実行時間（sim_seconds）を抽出します。

集計された結果は、./simulation_summaries_by_benchmark ディレクトリ内に、ベンチマークごとに個別のCSVファイルとして保存されます（例: simulation_summaries_by_benchmark/fft_summary.csv）。

各CSVファイルには、シミュレーションパラメータと sim_seconds (s) の列が含まれ、実行時間でソートされています。

7. トラブルシューティング
7.1. gem5 実行ファイルが見つからない
GEM5_PATH が gem5.opt の正しいパスを指しているか確認してください。

gem5 が scons build/ALPHA/gem5.opt で正常にビルドされているか確認してください。

7.2. se.py: error: option -n: invalid integer value: '16.0'
これは、run_simulation.py がCSVから読み込んだ数値を浮動小数点数として gem5 に渡しているために発生します。

run_simulation.py の core_num, l1_size_kb, l1_assoc, l2_size_kb, l2_assoc, l2_latency_cycles の各行で、int() を使って明示的に整数に変換していることを確認してください。最新のスクリプトでは修正済みです。

7.3. AttributeError: Class Root has no parameter exit_on_work_items
これは gem5 のバージョン間の互換性の問題です。

./configs/example/se.py ファイルを開き、root.exit_on_work_items = True の行をコメントアウトまたは削除してください。

7.4. stats.txt が生成されない、または空である
run_simulation.py の実行時に表示される gem5 STDOUT や gem5 STDERR のメッセージを注意深く確認してください。gem5 内部で致命的なエラーが発生している可能性があります。

ベンチマーク実行ファイル（例: ./splash2/fft/FFT）が存在し、実行可能であるか確認してください。

fmm ベンチマークの場合、入力ファイル（例: ./splash2/fmm/inputs/input.2048.p{CORE}）が存在するか確認してください。

7.5. collect_results.py がエラーになる、または結果が見つからない
BASE_RESULTS_DIR (./results_simulations) にシミュレーション結果のディレクトリが正しく保存されているか確認してください。

ディレクトリ名が正規表現のパターンと一致しているか確認してください。

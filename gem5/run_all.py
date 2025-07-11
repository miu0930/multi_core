import pandas as pd
import subprocess
import os
import math
import re # stats.txtを解析するために正規表現モジュールをインポート

# ===============================================================
# パラメータ設定 (Parameter Settings)
# ===============================================================
GEM5_PATH = "./build/ALPHA/gem5.opt"
GEM5_CONFIG_SCRIPT = "./configs/example/se.py"
INPUT_PARAMETERS_CSV = './filtered_data.csv' # または './data.csv'
BASE_RESULTS_DIR = "./results_simulations" # 元のディレクトリ名に戻す

# SPLASH-2 ベンチマーク定義
# 各ベンチマークに固有の skip_threshold_seconds を追加
BENCHMARKS = {
    "fmm": {
        "CMD": "./splash2/fmm/FMM",
        "OPTIONS_FORMAT": "< ./splash2/fmm/inputs/input.2048.p{CORE}",
        "skip_threshold_seconds": 900 # 例: 15分 (900秒)
    },
    "ocean": {
        "CMD": "./splash2/ocean/contiguous_partitions/OCEAN",
        "OPTIONS_FORMAT": "-n130 -p{CORE}",
        "skip_threshold_seconds": 1200 # 例: 20分 (1200秒)
    },
    "raytrace": {
        "CMD": "./splash2/raytrace/RAYTRACE",
        "OPTIONS_FORMAT": "-p{CORE} ./splash2/raytrace/inputs/teapot.env",
        "skip_threshold_seconds": 1800 # 例: 30分 (1800秒)
    },
    "cholesky": {
        "CMD": "./splash2/cholesky/CHOLESKY",
        "OPTIONS_FORMAT": "-p{CORE} ./splash2/cholesky/inputs/d750.O",
        "skip_threshold_seconds": 2400 # 例: 40分 (2400秒)
    },
    "fft": {
        "CMD": "./splash2/fft/FFT",
        "OPTIONS_FORMAT": "-p{CORE}",
        "skip_threshold_seconds": 60 # 例: 1分 (60秒) - FFTは速いため
    },
    "lu": {
        "CMD": "./splash2/lu/contiguous_blocks/LU",
        "OPTIONS_FORMAT": "-p{CORE}",
        "skip_threshold_seconds": 1500 # 例: 25分 (1500秒)
    },
    "radix": {
        "CMD": "./splash2/radix/RADIX",
        "OPTIONS_FORMAT": "-p{CORE}",
        "skip_threshold_seconds": 600 # 例: 10分 (600秒)
    }
}

# 資料17ページの実行時間目安データ (変更なし)
BASE_EXEC_TIMES = {
    ("fmm", 1): 309.104, ("fmm", 2): 329.282, ("fmm", 4): 350.246,
    ("fmm", 8): 394.418, ("fmm", 16): 530.571, ("fmm", 32): 593.797,
    ("ocean", 1): 234.342, ("ocean", 2): 247.708, ("ocean", 4): 286.173,
    ("ocean", 8): 357.542, ("ocean", 16): 450.171, ("ocean", 32): 676.673,
    ("raytrace", 1): 851.609, ("raytrace", 2): 885.676, ("raytrace", 4): 960.032,
    ("raytrace", 8): 1064.767, ("raytrace", 16): 1224.448, ("raytrace", 32): 1430.432,
    ("cholesky", 1): 1116.745, ("cholesky", 2): 841.407, ("cholesky", 4): 877.697,
    ("cholesky", 8): 1094.574, ("cholesky", 16): 1456.641, ("cholesky", 32): 2261.436,
    ("fft", 1): 2.518, ("fft", 2): 2.724, ("fft", 4): 3.094,
    ("fft", 8): 4.149, ("fft", 16): 9.150, ("fft", 32): 37.852,
    ("lu", 1): 788.856, ("lu", 2): 799.849, ("lu", 4): 832.486,
    ("lu", 8): 908.172, ("lu", 16): 1039.936, ("lu", 32): 1257.743,
    ("radix", 1): 209.293, ("radix", 2): 223.159, ("radix", 4): 231.191,
    ("radix", 8): 257.971, ("radix", 16): 301.007, ("radix", 32): 416.257
}
BASE_CPU_FREQ_GHZ = 0.72
BASE_L1_SIZE_KB = 16
BASE_L1_ASSOC = 4
BASE_L2_SIZE_KB = 512
BASE_L2_ASSOC = 8

# CPUクロックがこれより低い構成はシミュレーションをスキップする (GHz)
MIN_CPU_FREQ_TO_CONSIDER_GHZ = 0.7

# ===============================================================
# シミュレーション実行ロジック (Simulation Execution Logic)
# ===============================================================
def run_simulation():
    # gem5実行ファイルの存在チェック (Check for gem5 executable)
    if not os.path.exists(GEM5_PATH):
        print(f"エラー: gem5実行ファイルが見つかりません。パスを確認してください: {GEM5_PATH}")
        print("gem5をビルドまたはパスを修正してください。")
        return

    # gem5設定スクリプトの存在チェック (Check for gem5 config script)
    if not os.path.exists(GEM5_CONFIG_SCRIPT):
        print(f"エラー: gem5設定スクリプトが見つかりません。パスを確認してください: {GEM5_CONFIG_SCRIPT}")
        return

    try:
        df_params = pd.read_csv(INPUT_PARAMETERS_CSV)
    except FileNotFoundError:
        print(f"エラー: 入力パラメータCSVファイルが見つかりません: {INPUT_PARAMETERS_CSV}")
        print("前のステップでこのファイルが正しく生成されたか確認してください。")
        return
    except Exception as e:
        print(f"CSVファイルの読み込み中にエラーが発生しました: {e}")
        return

    # 結果ディレクトリの作成 (Create results directory)
    os.makedirs(BASE_RESULTS_DIR, exist_ok=True)

    total_simulations = len(df_params) * len(BENCHMARKS)
    current_sim_count = 0

    for index, row in df_params.iterrows():
        # CSVから読み込んだ値を適切な型に変換 (Convert values read from CSV to appropriate types)
        core_num = int(row['Core Number'])
        cpu_clock_ghz = float(row['CPU clock (GHz)']) # CPUクロックはfloatのまま
        l1_size_kb = int(row['L1 Cache Size (KB)'])
        l1_assoc = int(row['L1 Associativity'])
        l2_size_kb = int(row['L2 Cache Size (KB)'])
        l2_assoc = int(row['L2 Associativity'])
        # L2 latencyはCSVでfloat('inf')になる可能性があるので、int()変換前にチェック
        l2_latency_cycles_raw = row['L2 latency (cycles)']
        l2_latency_cycles = int(l2_latency_cycles_raw) if l2_latency_cycles_raw != float('inf') else float('inf')


        if l2_latency_cycles == float('inf'):
            print(f"スキップ: L2レイテンシが無限大の構成 (Core={core_num}, L1={l1_size_kb}KB, L2={l2_size_kb}KB)。")
            continue

        if cpu_clock_ghz < MIN_CPU_FREQ_TO_CONSIDER_GHZ:
            print(f"スキップ: CPUクロックが低すぎます ({cpu_clock_ghz}GHz < {MIN_CPU_FREQ_TO_CONSIDER_GHZ}GHz)。構成: Core={core_num}, L1={l1_size_kb}KB, L2={l2_size_kb}KB。")
            continue


        for bench_name, bench_info in BENCHMARKS.items():
            current_sim_count += 1
            
            # ベンチマーク固有の実行時間しきい値を取得
            current_skip_threshold_seconds = bench_info.get("skip_threshold_seconds") 
            if current_skip_threshold_seconds is None:
                # 定義されていない場合は、スキップしない、またはデフォルト値を適用
                current_skip_threshold_seconds = float('inf') # 基本的にスキップしない

            # 実行時間予測とスキップ判定
            predicted_time_seconds = None
            base_time_key = (bench_name, core_num)
            if base_time_key in BASE_EXEC_TIMES:
                base_time = BASE_EXEC_TIMES[base_time_key]
                if cpu_clock_ghz > 0:
                    predicted_time_seconds = base_time * (BASE_CPU_FREQ_GHZ / cpu_clock_ghz)
                else:
                    predicted_time_seconds = float('inf')

                # 予測時間がベンチマーク固有のしきい値を超える場合はスキップ
                if predicted_time_seconds is not None and predicted_time_seconds >= current_skip_threshold_seconds:
                    print(f"\n({current_sim_count}/{total_simulations}) スキップ: {bench_name} (Core={core_num}, L1={l1_size_kb}KB, L2={l2_size_kb}KB, Clock={cpu_clock_ghz}GHz)")
                    print(f"  予測される実行時間が長すぎます ({predicted_time_seconds:.2f}秒 >= {current_skip_threshold_seconds}秒)。")
                    continue
                elif predicted_time_seconds is not None and predicted_time_seconds == float('inf'):
                    print(f"\n({current_sim_count}/{total_simulations}) スキップ: {bench_name} (Core={core_num}, L1={l1_size_kb}KB, L2={l2_size_kb}KB, Clock={cpu_clock_ghz}GHz)")
                    print(f"  CPU周波数が0のため、実行時間は無限大と予測されます。")
                    continue

            cmd_base = bench_info['CMD']
            # ベンチマーク実行ファイルの存在チェック (Check for benchmark executable)
            if not os.path.exists(cmd_base):
                print(f"エラー: ベンチマーク実行ファイルが見つかりません。パスを確認してください: {cmd_base}")
                print(f"このシミュレーションはスキップされます: {bench_name} (Core={core_num}, L1={l1_size_kb}KB, L2={l2_size_kb}KB)")
                continue

            cmd_options = bench_info['OPTIONS_FORMAT'].format(CORE=core_num)

            # 各シミュレーションの出力ディレクトリを生成
            out_dir_name = (
                f"core{core_num}_L1-{l1_size_kb}KB-A{l1_assoc}_"
                f"L2-{l2_size_kb}KB-A{l2_assoc}_Lat{l2_latency_cycles}_Bench-{bench_name}"
            )
            full_out_dir = os.path.join(BASE_RESULTS_DIR, out_dir_name)
            os.makedirs(full_out_dir, exist_ok=True)

            gem5_command_args = [
                GEM5_PATH,
                "-d", full_out_dir,
                GEM5_CONFIG_SCRIPT,
                "-n", str(core_num), # intに変換したcore_numを使用
                "--cpu-type=detailed",
                "--cpu-clock=" + str(cpu_clock_ghz) + "GHz",
                "--mem-type=SimpleMemory",
                "--caches",
                "--l2cache",
                "--l1d_size=" + str(l1_size_kb) + "kB", # intに変換したl1_size_kbを使用
                "--l1d_assoc=" + str(l1_assoc),         # intに変換したl1_assocを使用
                "--l2_size=" + str(l2_size_kb) + "kB",   # intに変換したl2_size_kbを使用
                "--l2_assoc=" + str(l2_assoc),           # intに変換したl2_assocを使用
                "--l2_latency=" + str(l2_latency_cycles), # intに変換したl2_latency_cyclesを使用
                "-c", cmd_base
            ]
            
            print(f"\n--- シミュレーション開始 ({current_sim_count}/{total_simulations}) ---")
            print(f"  設定: {out_dir_name}")
            if predicted_time_seconds is not None:
                print(f"  予測実行時間: {predicted_time_seconds:.2f}秒。")
            print(f"  出力ディレクトリ: {full_out_dir}")

            try:
                # fmmベンチマークは入力リダイレクトが必要なため、shell=Trueで実行
                if bench_name == "fmm":
                    full_command_str = " ".join(gem5_command_args) + f" {cmd_options}"
                    print(f"  コマンド: {full_command_str}")
                    result = subprocess.run(
                        full_command_str,
                        shell=True,
                        executable='/bin/bash', # 明示的にbashを使用
                        capture_output=True,
                        text=True,
                        check=False
                    )
                else:
                    # その他のベンチマークは -o オプションで引数を渡す
                    gem5_command_args.extend(["-o", cmd_options])
                    print(f"  コマンド: {' '.join(gem5_command_args)}")
                    result = subprocess.run(
                        gem5_command_args,
                        capture_output=True,
                        text=True,
                        check=False
                    )

                if result.returncode != 0:
                    print(f"エラー: gem5シミュレーションが非ゼロの終了コードで終了しました: {result.returncode}")
                    if result.stdout: print(f"  gem5 STDOUT:\n{result.stdout}")
                    if result.stderr: print(f"  gem5 STDERR:\n{result.stderr}")
                    print("上記gem5の出力メッセージを確認してください。")
                    continue # 次のシミュレーションへ

                # stats.txtから実行時間を読み込む (Read execution time from stats.txt)
                stats_file_path = os.path.join(full_out_dir, 'stats.txt')
                sim_seconds = "N/A"
                if os.path.exists(stats_file_path) and os.path.getsize(stats_file_path) > 0:
                    with open(stats_file_path, 'r') as f:
                        for line in f:
                            # sim_secondsの行を正規表現で検索 (Search for sim_seconds line with regex)
                            match = re.match(r'\s*sim_seconds\s+([0-9.]+)', line)
                            if match:
                                sim_seconds = float(match.group(1))
                                break
                    if sim_seconds == "N/A":
                        print(f"警告: '{stats_file_path}' から 'sim_seconds' が見つかりませんでした。")
                else:
                    print(f"警告: '{stats_file_path}' が見つからないか、空です。")

                print(f"  実行時間 (sim_seconds): {sim_seconds} 秒")

            except FileNotFoundError:
                print(f"エラー: コマンド '{gem5_command_args[0]}' が見つかりません。gem5へのパスが正しいか確認してください。")
            except Exception as e:
                print(f"予期せぬエラーが発生しました: {e}")

            print(f"--- シミュレーション終了 ({current_sim_count}/{total_simulations}) ---\n")

    print("\nすべてのシミュレーション実行が完了しました。")
    print(f"結果は '{BASE_RESULTS_DIR}' ディレクトリ以下に保存されています。")
    print("次に、結果集計スクリプトを実行してください。")

if __name__ == "__main__":
    run_simulation()

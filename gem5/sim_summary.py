import pandas as pd
import os
import re

# ===============================================================
# パラメータ設定
# ===============================================================
# シミュレーション結果が保存されているベースディレクトリ
BASE_RESULTS_DIR = "./results_simulations"
# 集計結果を保存するCSVファイル名
OUTPUT_SUMMARY_CSV = "./simulation_summary.csv"

# ===============================================================
# stats.txt から情報を抽出する関数
# ===============================================================
def extract_stats(stats_file_path):
    stats = {}
    try:
        with open(stats_file_path, 'r') as f:
            for line in f:
                # 'sim_ticks' や 'sim_insts' などの行を抽出
                match = re.match(r'\s*(\S+)\s+(\S+)\s+#\s*(.*)', line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    try:
                        # 数値に変換できるものは変換
                        if '.' in value:
                            stats[key] = float(value)
                        else:
                            stats[key] = int(value)
                    except ValueError:
                        stats[key] = value # 数値でない場合はそのまま文字列として保持

    except FileNotFoundError:
        print(f"警告: stats.txt が見つかりません: {stats_file_path}")
    except Exception as e:
        print(f"stats.txt の読み込み中にエラーが発生しました ({stats_file_path}): {e}")
    return stats

# ===============================================================
# メインの集計ロジック
# ===============================================================
def collect_simulation_results():
    all_results = []

    if not os.path.exists(BASE_RESULTS_DIR):
        print(f"エラー: 結果ディレクトリが見つかりません: {BASE_RESULTS_DIR}")
        print("まずシミュレーションを実行して結果を生成してください。")
        return

    # ベースディレクトリ以下のサブディレクトリを走査
    for dir_name in os.listdir(BASE_RESULTS_DIR):
        full_dir_path = os.path.join(BASE_RESULTS_DIR, dir_name)

        if os.path.isdir(full_dir_path):
            # ディレクトリ名からパラメータをパース
            # 例: core8_L1-16KB-A4_L2-512KB-A8_Lat2_Bench-fmm
            params = {}
            match = re.match(r'core(\d+)_L1-(\d+)KB-A(\d+)_L2-(\d+)KB-A(\d+)_Lat(\w+)_Bench-(\w+)', dir_name)
            if match:
                params['Core Number'] = int(match.group(1))
                params['L1 Cache Size (KB)'] = int(match.group(2))
                params['L1 Associativity'] = int(match.group(3))
                params['L2 Cache Size (KB)'] = int(match.group(4))
                params['L2 Associativity'] = int(match.group(5))
                params['L2 latency (cycles)'] = float(match.group(6)) if match.group(6) == 'inf' else int(match.group(6))
                params['Benchmark'] = match.group(7)
            else:
                print(f"警告: 不明なディレクトリ形式をスキップします: {dir_name}")
                continue
            
            # CPUクロックは別途stats.txtか元のパラメータCSVから取得する必要がある
            # 今回はディレクトリ名に含まれていないため、stats.txtからsim_freqなどを使って推測するか、
            # もしくは元のパラメータCSVと結合して取得する必要があります。
            # ここではディレクトリ名にないため、一時的に空か、または仮の値とします。
            # run_simulations.pyのOUTDIR生成時にCPUクロックを含める変更を加えていたので、
            # その情報もディレクトリ名から抽出するようにすれば、より正確です。
            # 現状のディレクトリ名フォーマットではCPUクロックは抽出できないため、
            # stats.txtからsystem.clk_domain.clock (tick/cycle) または sim_freq (tick/s) を使うのが一般的です。
            # CPUクロック (GHz) = (sim_freq / system.clk_domain.clock) / 1e9
            # しかし、手軽さのため、ここでは元のパラメータCSVとマージすることを推奨します。

            stats_file_path = os.path.join(full_dir_path, "stats.txt")
            extracted_stats = extract_stats(stats_file_path)

            if extracted_stats:
                # 抽出した統計情報を結果に追加
                result_row = {
                    'Core Number': params['Core Number'],
                    # 'CPU clock (GHz)': CPUクロックは別途取得またはマージ
                    'L1 Cache Size (KB)': params['L1 Cache Size (KB)'],
                    'L1 Associativity': params['L1 Associativity'],
                    'L2 Cache Size (KB)': params['L2 Cache Size (KB)'],
                    'L2 Associativity': params['L2 Associativity'],
                    'L2 latency (cycles)': params['L2 latency (cycles)'],
                    'Benchmark': params['Benchmark'],
                    'sim_ticks (ps)': extracted_stats.get('sim_ticks'),
                    'sim_seconds (s)': extracted_stats.get('sim_seconds'), # 秒単位の実行時間
                    'sim_insts': extracted_stats.get('sim_insts'),
                    # 各コアのサイクル数やキャッシュミス情報などを追加する場合は、ループ処理が必要
                    # 例: 'system.cpu0.numCycles', 'system.cpu0.dcache.overall_miss_rate::total' など
                    'L2_overall_accesses': extracted_stats.get('system.l2.overall_accesses::total'),
                    'L2_overall_misses': extracted_stats.get('system.l2.overall_misses::total'),
                    'L2_demand_miss_rate': extracted_stats.get('system.l2.demand_miss_rate::total'),
                    # CPUクロック (GHz) を stats.txt から推測する場合 (sim_freqとsystem.clk_domain.clockから)
                    # sim_freq は通常 1e12 ticks/s (1THz)
                    # system.clk_domain.clock は クロック周期 (ticks/cycle)
                    # CPU_Freq_Hz = sim_freq / system.clk_domain.clock
                    # CPU_Freq_GHz = CPU_Freq_Hz / 1e9
                    'CPU clock (GHz)': (extracted_stats.get('sim_freq') / extracted_stats.get('system.clk_domain.clock', 1)) / 1e9 if extracted_stats.get('sim_freq') and extracted_stats.get('system.clk_domain.clock') else None
                }
                all_results.append(result_row)

    # DataFrameを作成してCSVに保存
    if all_results:
        df_summary = pd.DataFrame(all_results)
        # コラムの並び順を調整（必要であれば）
        # 例えば、'Core Number', 'CPU clock (GHz)', 'L1 Cache Size (KB)', ... の順にしたい場合
        # 必要なコラムをリストで指定して並べ替える
        ordered_columns = [
            'Core Number', 'CPU clock (GHz)', 'L1 Cache Size (KB)', 'L1 Associativity',
            'L2 Cache Size (KB)', 'L2 Associativity', 'L2 latency (cycles)', 'Benchmark',
            'sim_ticks (ps)', 'sim_seconds (s)', 'sim_insts',
            'L2_overall_accesses', 'L2_overall_misses', 'L2_demand_miss_rate'
        ]
        # 実際にDataFrameに存在するコラムのみでソート
        final_columns = [col for col in ordered_columns if col in df_summary.columns]
        df_summary = df_summary[final_columns]
        
        # 結果をsim_seconds (s)でソートして最短の構成を見つけやすくすることも可能
        df_summary = df_summary.sort_values(by=['Benchmark', 'sim_seconds (s)']).reset_index(drop=True)

        df_summary.to_csv(OUTPUT_SUMMARY_CSV, index=False)
        print(f"\n集計結果を '{OUTPUT_SUMMARY_CSV}' に保存しました。")
        print(f"集計されたシミュレーション数: {len(df_summary)}")
    else:
        print("集計対象のシミュレーション結果が見つかりませんでした。")

# スクリプトの実行
if __name__ == "__main__":
    collect_simulation_results()
import pandas as pd
import os
import re

# ===============================================================
# パラメータ設定
# ===============================================================
BASE_RESULTS_DIR = "./results_simulations"
OUTPUT_SUMMARY_CSV = "./simulation_summary.csv"

# ===============================================================
# stats.txt から情報を抽出する関数
# ===============================================================
def extract_stats(stats_file_path):
    stats = {}
    try:
        with open(stats_file_path, 'r') as f:
            for line in f:
                match = re.match(r'\s*(\S+)\s+(\S+)\s+#\s*(.*)', line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    try:
                        stats[key] = float(value) if '.' in value else int(value)
                    except ValueError:
                        stats[key] = value
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

    for dir_name in os.listdir(BASE_RESULTS_DIR):
        full_dir_path = os.path.join(BASE_RESULTS_DIR, dir_name)

        if os.path.isdir(full_dir_path):
            # 修正済みの正規表現（小数もOK）
            match = re.match(
                r'core([\d.]+)_L1-([\d.]+)KB-A([\d.]+)_L2-([\d.]+)KB-A([\d.]+)_Lat([\d.]+)_Bench-(\w+)',
                dir_name
            )
            if match:
                try:
                    params = {
                        'Core Number': int(float(match.group(1))),
                        'L1 Cache Size (KB)': int(float(match.group(2))),
                        'L1 Associativity': int(float(match.group(3))),
                        'L2 Cache Size (KB)': int(float(match.group(4))),
                        'L2 Associativity': int(float(match.group(5))),
                        'L2 latency (cycles)': float(match.group(6)),
                        'Benchmark': match.group(7)
                    }
                except Exception as e:
                    print(f"パラメータ変換時にエラー: {dir_name}, {e}")
                    continue
            else:
                print(f"警告: 不明なディレクトリ形式をスキップします: {dir_name}")
                continue

            stats_file_path = os.path.join(full_dir_path, "stats.txt")
            extracted_stats = extract_stats(stats_file_path)

            if extracted_stats:
                result_row = {
                    'Core Number': params['Core Number'],
                    'L1 Cache Size (KB)': params['L1 Cache Size (KB)'],
                    'L1 Associativity': params['L1 Associativity'],
                    'L2 Cache Size (KB)': params['L2 Cache Size (KB)'],
                    'L2 Associativity': params['L2 Associativity'],
                    'L2 latency (cycles)': params['L2 latency (cycles)'],
                    'Benchmark': params['Benchmark'],
                    'sim_ticks': extracted_stats.get('sim_ticks'),
                    'sim_seconds (s)': extracted_stats.get('sim_seconds'),
                    'sim_insts': extracted_stats.get('sim_insts'),
                    'L2_overall_accesses': extracted_stats.get('system.l2.overall_accesses::total'),
                    'L2_overall_misses': extracted_stats.get('system.l2.overall_misses::total'),
                    'L2_demand_miss_rate': extracted_stats.get('system.l2.demand_miss_rate::total'),
                    'CPU clock (GHz)': (
                        (extracted_stats.get('sim_freq') / extracted_stats.get('system.clk_domain.clock', 1)) / 1e9
                        if extracted_stats.get('sim_freq') and extracted_stats.get('system.clk_domain.clock') else None
                    )
                }
                all_results.append(result_row)

    if all_results:
        df_summary = pd.DataFrame(all_results)

        ordered_columns = [
            'Core Number', 'CPU clock (GHz)', 'L1 Cache Size (KB)', 'L1 Associativity',
            'L2 Cache Size (KB)', 'L2 Associativity', 'L2 latency (cycles)', 'Benchmark',
            'sim_ticks', 'sim_seconds (s)', 'sim_insts',
            'L2_overall_accesses', 'L2_overall_misses', 'L2_demand_miss_rate'
        ]
        final_columns = [col for col in ordered_columns if col in df_summary.columns]
        df_summary = df_summary[final_columns]
        df_summary = df_summary.sort_values(by=['Benchmark', 'sim_seconds (s)']).reset_index(drop=True)
        df_summary.to_csv(OUTPUT_SUMMARY_CSV, index=False)
        print(f"\n✅ 集計結果を '{OUTPUT_SUMMARY_CSV}' に保存しました。")
        print(f"✅ 集計されたシミュレーション数: {len(df_summary)}")
    else:
        print("⚠️ 集計対象のシミュレーション結果が見つかりませんでした。")

# スクリプト実行
if __name__ == "__main__":
    collect_simulation_results()

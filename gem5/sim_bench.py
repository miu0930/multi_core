import pandas as pd
import os
import re

# ===============================================================
# パラメータ設定 (Parameter Settings)
# ===============================================================
BASE_RESULTS_DIR = "./results_simulations"
OUTPUT_SUMMARY_BASE_DIR = "./simulation_summaries_by_benchmark" # ベンチマークごとの出力ディレクトリ

# ===============================================================
# stats.txt から情報を抽出する関数 (Function to extract information from stats.txt)
# ===============================================================
def extract_stats(stats_file_path):
    stats = {}
    try:
        with open(stats_file_path, 'r') as f:
            for line in f:
                # 正規表現でキーと値、コメントを抽出
                match = re.match(r'\s*(\S+)\s+(\S+)\s+#\s*(.*)', line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    try:
                        # 数値に変換できる場合は変換
                        stats[key] = float(value) if '.' in value else int(value)
                    except ValueError:
                        # 数値に変換できない場合は文字列として保持
                        stats[key] = value
    except FileNotFoundError:
        print(f"警告: stats.txt が見つかりません: {stats_file_path}")
    except Exception as e:
        print(f"stats.txt の読み込み中にエラーが発生しました ({stats_file_path}): {e}")
    return stats

# ===============================================================
# メインの集計ロジック (Main aggregation logic)
# ===============================================================
def collect_simulation_results():
    all_results = []

    if not os.path.exists(BASE_RESULTS_DIR):
        print(f"エラー: 結果ディレクトリが見つかりません: {BASE_RESULTS_DIR}")
        print("まずシミュレーションを実行して結果を生成してください。")
        return

    # ベンチマークごとの出力ディレクトリを作成 (Create output directory for benchmark-specific summaries)
    os.makedirs(OUTPUT_SUMMARY_BASE_DIR, exist_ok=True)
    print(f"集計結果は '{OUTPUT_SUMMARY_BASE_DIR}' ディレクトリに保存されます。")

    for dir_name in os.listdir(BASE_RESULTS_DIR):
        full_dir_path = os.path.join(BASE_RESULTS_DIR, dir_name)

        if os.path.isdir(full_dir_path):
            # ディレクトリ名からパラメータを抽出 (Extract parameters from directory name)
            # 小数点を含む数値も考慮した正規表現
            match = re.match(
                r'core([\d.]+)_L1-([\d.]+)KB-A([\d.]+)_L2-([\d.]+)KB-A([\d.]+)_Lat([\d.]+)_Bench-(\w+)',
                dir_name
            )
            if match:
                try:
                    # 抽出した値を適切な型に変換 (Convert extracted values to appropriate types)
                    params = {
                        'Core Number': int(float(match.group(1))),
                        'L1 Cache Size (KB)': int(float(match.group(2))),
                        'L1 Associativity': int(float(match.group(3))),
                        'L2 Cache Size (KB)': int(float(match.group(4))),
                        'L2 Associativity': int(float(match.group(5))),
                        'L2 latency (cycles)': float(match.group(6)), # レイテンシはfloatのまま
                        'Benchmark': match.group(7)
                    }
                except ValueError as e:
                    print(f"警告: ディレクトリ名 '{dir_name}' からパラメータ変換時にエラーが発生しました: {e}")
                    continue
                except Exception as e:
                    print(f"予期せぬエラー: ディレクトリ名 '{dir_name}' の解析中に問題が発生しました: {e}")
                    continue
            else:
                print(f"警告: 不明なディレクトリ形式をスキップします: {dir_name}")
                continue

            stats_file_path = os.path.join(full_dir_path, "stats.txt")
            extracted_stats = extract_stats(stats_file_path)

            if extracted_stats:
                # 必要な情報のみを抽出 (Extract only the necessary information)
                result_row = {
                    'Core Number': params['Core Number'],
                    'L1 Cache Size (KB)': params['L1 Cache Size (KB)'],
                    'L1 Associativity': params['L1 Associativity'],
                    'L2 Cache Size (KB)': params['L2 Cache Size (KB)'],
                    'L2 Associativity': params['L2 Associativity'],
                    'L2 latency (cycles)': params['L2 latency (cycles)'],
                    'sim_seconds (s)': extracted_stats.get('sim_seconds'),
                    'Benchmark': params['Benchmark'] # 後でグループ化するために必要
                }
                all_results.append(result_row)

    if all_results:
        df_summary = pd.DataFrame(all_results)

        # ベンチマークごとにグループ化してCSVを生成 (Group by benchmark and generate CSVs)
        for bench_name, group_df in df_summary.groupby('Benchmark'):
            output_csv_path = os.path.join(OUTPUT_SUMMARY_BASE_DIR, f"{bench_name}_summary.csv")

            # 出力する列の順序を定義 (Define the order of columns for output)
            ordered_columns = [
                'Core Number', 'L1 Cache Size (KB)', 'L1 Associativity',
                'L2 Cache Size (KB)', 'L2 Associativity', 'L2 latency (cycles)',
                'sim_seconds (s)'
            ]
            
            # 実際のDataFrameに存在する列のみを選択し、順序を適用 (Select existing columns and apply order)
            final_columns = [col for col in ordered_columns if col in group_df.columns]
            group_df = group_df[final_columns]

            # sim_secondsでソート (Sort by sim_seconds)
            group_df = group_df.sort_values(by='sim_seconds (s)').reset_index(drop=True)
            
            group_df.to_csv(output_csv_path, index=False)
            print(f"✅ ベンチマーク '{bench_name}' の集計結果を '{output_csv_path}' に保存しました。")
            print(f"   集計されたシミュレーション数: {len(group_df)}")
    else:
        print("⚠️ 集計対象のシミュレーション結果が見つかりませんでした。")

    print("\nすべての集計処理が完了しました。")

# スクリプト実行 (Execute script)
if __name__ == "__main__":
    collect_simulation_results()

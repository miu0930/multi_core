import pandas as pd
import os

# ===============================================================
# パラメータ設定 (Parameter Settings)
# ===============================================================
INPUT_CSV_PATH = "./simulation_summary.csv"  # 既に集計されたCSVファイルのパス
OUTPUT_SUMMARY_BASE_DIR = "./simulation_summaries_by_benchmark"  # 出力先ディレクトリ

# ===============================================================
# メインの処理 (Main Processing Logic)
# ===============================================================
def split_summary_by_benchmark():
    if not os.path.exists(INPUT_CSV_PATH):
        print(f"❌ 入力ファイルが見つかりません: {INPUT_CSV_PATH}")
        return

    # 出力ディレクトリ作成
    os.makedirs(OUTPUT_SUMMARY_BASE_DIR, exist_ok=True)
    print(f"出力ディレクトリ: {OUTPUT_SUMMARY_BASE_DIR}")

    try:
        df = pd.read_csv(INPUT_CSV_PATH)
    except Exception as e:
        print(f"❌ CSVの読み込み中にエラーが発生しました: {e}")
        return

    if 'Benchmark' not in df.columns:
        print("❌ 'Benchmark' 列が存在しません。分割できません。")
        return

    for bench_name, group_df in df.groupby('Benchmark'):
        output_csv_path = os.path.join(OUTPUT_SUMMARY_BASE_DIR, f"{bench_name}_summary.csv")

        # 列の順序指定（存在する列のみ）
        ordered_columns = [
            'Core Number', 'L1 Cache Size (KB)', 'L1 Associativity',
            'L2 Cache Size (KB)', 'L2 Associativity', 'L2 latency (cycles)',
            'sim_ticks'
        ]
        final_columns = [col for col in ordered_columns if col in group_df.columns]

        # 列の並び替え + sim_ticksでソート
        group_df = group_df[final_columns + ['Benchmark'] if 'Benchmark' in group_df.columns else final_columns]
        group_df = group_df.sort_values(by='sim_ticks', ascending=True).reset_index(drop=True)

        # CSV出力
        group_df.to_csv(output_csv_path, index=False)
        print(f"✅ {bench_name}: {len(group_df)} 件 → {output_csv_path}")

    print("\n🎉 ベンチマークごとの分割が完了しました。")

# スクリプト実行
if __name__ == "__main__":
    split_summary_by_benchmark()

import pandas as pd
import os

# ===============================================================
# パラメータ設定 (Parameter Settings)
# ===============================================================
INPUT_CSV_PATH = "./result/simulation_summary.csv"  # 既に集計されたCSVファイルのパス
OUTPUT_SUMMARY_BASE_DIR = "./result/simulation_summaries_by_benchmark"  # 出力先ディレクトリ
BENCHMARK_STATS_PATH = "./result/benchmark_stats_summary.csv"  # 統計出力ファイル

# ===============================================================
# ベンチマーク統計出力 (Benchmark Statistics Summary)
# ===============================================================
def summarize_benchmark_stats(df):
    # FFT を除外（大小文字無視）
    df = df[~df['Benchmark'].str.lower().str.contains('fft')]

    # 統計量の計算
    stats = (
        df.groupby('Benchmark')['sim_ticks']
        .agg(['count', 'mean', 'std', 'min'])
        .rename(columns={
            'count': '試行数',
            'mean': '平均(sim_ticks)',
            'std': '標準偏差(sim_ticks)',
            'min': '最小(sim_ticks)'
        })
    )
    stats['変動係数(CV)'] = stats['標準偏差(sim_ticks)'] / stats['平均(sim_ticks)']

    # 結果表示
    print("\n📊 ベンチマークごとの統計サマリ（FFT除外）:")
    print(stats.sort_values(by='平均(sim_ticks)'))

    # CSV出力（オプション）
    stats.to_csv(BENCHMARK_STATS_PATH)
    print(f"\n📄 統計サマリを出力しました → {BENCHMARK_STATS_PATH}")

# ===============================================================
# メインの処理 (Main Processing Logic)
# ===============================================================
def split_summary_by_benchmark():
    if not os.path.exists(INPUT_CSV_PATH):
        print(f"❌ 入力ファイルが見つかりません: {INPUT_CSV_PATH}")
        return

    os.makedirs(OUTPUT_SUMMARY_BASE_DIR, exist_ok=True)
    print(f"出力ディレクトリ: {OUTPUT_SUMMARY_BASE_DIR}")

    try:
        df = pd.read_csv(INPUT_CSV_PATH)
    except Exception as e:
        print(f"❌ CSVの読み込み中にエラーが発生しました: {e}")
        return

    if 'BCE' not in df.columns:
        print("❌ 'BCE' 列が存在しません。フィルタ処理を実行できません。")
        return
    df = df[df['BCE'] < 128]

    if 'Benchmark' not in df.columns:
        print("❌ 'Benchmark' 列が存在しません。分割できません。")
        return

    for bench_name, group_df in df.groupby('Benchmark'):
        output_csv_path = os.path.join(OUTPUT_SUMMARY_BASE_DIR, f"{bench_name}_summary.csv")

        # 出力列の順序（BCEは残す、Benchmarkは出力から除く）
        ordered_columns = [
            'Core Number', 'L1 Cache Size (KB)', 'L1 Associativity',
            'L2 Cache Size (KB)', 'L2 Associativity', 'L2 latency (cycles)',
            'sim_ticks', 'BCE'
        ]
        final_columns = [col for col in ordered_columns if col in group_df.columns]

        # 列の並び替え + sim_ticksでソート
        group_df = group_df[final_columns]
        group_df = group_df.sort_values(by='sim_ticks', ascending=True).reset_index(drop=True)

        # CSV出力
        group_df.to_csv(output_csv_path, index=False)
        print(f"✅ {bench_name}: {len(group_df)} 件 → {output_csv_path}")

    # FFTを除いた統計サマリの出力
    summarize_benchmark_stats(df)

    print("\n🎉 全処理が完了しました。")

# スクリプト実行
if __name__ == "__main__":
    split_summary_by_benchmark()
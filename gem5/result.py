import pandas as pd
import os

INPUT_CSV_PATH = "./result/simulation_summary.csv"
BEST_CONFIG_OUTPUT = "./result/best_general_config_normalized3_filtered_no_count.csv"

def find_best_general_config_normalized():
    if not os.path.exists(INPUT_CSV_PATH):
        print(f"❌ 入力ファイルが見つかりません: {INPUT_CSV_PATH}")
        return

    df = pd.read_csv(INPUT_CSV_PATH)

    required_cols = ['Benchmark', 'sim_ticks', 'BCE']
    config_cols = [
        'Core Number', 'L1 Cache Size (KB)', 'L1 Associativity',
        'L2 Cache Size (KB)', 'L2 Associativity', 'L2 latency (cycles)', 'BCE'
    ]
    for col in required_cols + config_cols:
        if col not in df.columns:
            print(f"❌ 欠損列: {col}")
            return

    df = df[(df['BCE'] < 128) & (~df['Benchmark'].str.lower().str.contains("fft|lu"))]

    df['normalized'] = df.groupby('Benchmark')['sim_ticks'].transform(lambda x: x / x.min())

    result = (
        df.groupby(config_cols)['normalized']
        .agg(['count', 'mean'])
        .reset_index()
        .rename(columns={
            'count': '試行数',
            'mean': '平均(正規化)'
        })
    )

    result = result[result['試行数'] == 3]

    result = result.drop(columns=['試行数'])

    result = result.sort_values(by='平均(正規化)').reset_index(drop=True)

    result.to_csv(BEST_CONFIG_OUTPUT, index=False)
    print(f"✅ 試行数3で平均(正規化)に基づく最良構成を出力しました → {BEST_CONFIG_OUTPUT}")
    print("\n🏅 上位5構成（平均(正規化)が低い）:")
    print(result.head(5))

if __name__ == "__main__":
    find_best_general_config_normalized()

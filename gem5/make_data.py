import pandas as pd
import math

# 対象のCore数リスト
CPU_CORES = (2, 4, 8, 16, 32)

# ファイルパス
L1_csv = '../cacti_time/L1/L1_sorted_result.csv'
L2_csv = '../cacti_time/L2/L2_sorted_result.csv'
data_csv = './data.csv'

# L2サイズの計算式を修正し、可能なL2サイズのリストを返すように変更
def get_possible_L2_sizes(L1_size, Core_num):
    # BCEコストの計算
    core_bce_cost = Core_num # コア1つあたり1BCE
    l1_bce_cost = L1_size / 2 # L1キャッシュサイズ2KBあたり1BCE

    # L2に割り当て可能なBCEの最大値
    remaining_bce_for_l2 = 128 - core_bce_cost - l1_bce_cost # 制約はハードウェアコスト128BCE以下

    # L2サイズ (KB) の最大値を計算
    l2_size_kb = 32 * remaining_bce_for_l2 # L2キャッシュサイズ32KBあたり1BCE

    possible_l2_sizes = []
    if l2_size_kb <= 0:
        return possible_l2_sizes # 空のリストを返す

    # 2の累乗で、かつ最大L2サイズ以下のL2サイズを全てリストアップ
    # ここを1024KB (2^10) から開始
    for exponent in range(10, 12): # 2^10=1024KB, ..., 2^11=2048KB (L2_dfの最大を考慮し適宜調整)
        current_l2_size = 2 ** exponent
        if current_l2_size <= l2_size_kb:
            possible_l2_sizes.append(current_l2_size)
        else:
            break # 最大値を超えたらループを終了

    # 最大L2サイズが2の累乗でない場合も、そのサイズ以下の最大の2の累乗を含める
    # ビット演算を行うため、l2_size_kbを整数に変換
    if l2_size_kb > 0 and (int(l2_size_kb) & (int(l2_size_kb) - 1)) != 0: # 2の累乗でない場合
        closest_power_of_2 = 2 ** math.floor(math.log2(l2_size_kb))
        # closest_power_of_2 が1024KB以上の場合のみ追加
        if closest_power_of_2 not in possible_l2_sizes and closest_power_of_2 >= 1024:
            possible_l2_sizes.append(closest_power_of_2)
            possible_l2_sizes.sort() # ソートして順序を保つ

    return possible_l2_sizes

# CSV読み込み
L1_df = pd.read_csv(L1_csv)
L2_df = pd.read_csv(L2_csv)

# 出力データの初期化（毎回新しいDataFrameを作成）
data = pd.DataFrame(columns=[
    'Core Number', 'CPU clock (GHz)', 'L1 Cache Size (KB)', 'L1 Associativity',
    'L2 Cache Size (KB)', 'L2 Associativity', 'L2 latency (cycles)', 'Total BCE Cost'
])

rows = []

# 各Core数とL1構成に対してループ
for core in CPU_CORES:
    for _, l1_row in L1_df.iterrows():
        L1_size = l1_row['Cache Size (KB)']
        L1_assoc = l1_row['Associativity']
        L1_access_time_ns = l1_row['Access Time (ns)']

        # CPU周波数 (GHz) の計算
        # L1データキャッシュのアクセス時間の逆数、小数点第二位以下は切り捨て
        if L1_access_time_ns <= 0:
            cpu_frequency_ghz = 0.0
            print(f"[警告] L1アクセス時間が0以下です: Core={core}, L1_size={L1_size}, L1_assoc={L1_assoc}. CPU周波数を0に設定します。")
        else:
            cpu_frequency_hz = 1 / (L1_access_time_ns * 1e-9)
            cpu_frequency_ghz = math.floor(cpu_frequency_hz / 1e9 * 10) / 10

        # CPUクロックサイクル時間 (ns) の計算
        # CPU周波数が0の場合、クロックサイクル時間は無限大となる
        if cpu_frequency_ghz <= 0:
            cpu_clock_cycle_time_ns = float('inf')
            print(f"[警告] 計算されたCPU周波数が0です: Core={core}, L1_size={L1_size}, L1_assoc={L1_assoc}. クロックサイクル時間を無限大に設定します。")
        else:
            cpu_clock_cycle_time_ns = 1 / cpu_frequency_ghz # 1GHz = 1nsサイクル時間

        # L2サイズの候補リストを取得
        possible_L2_sizes = get_possible_L2_sizes(L1_size, core)
        if not possible_L2_sizes:
            print(f"[警告] L2サイズの候補がありません: Core={core}, L1_size={L1_size}. このL1構成はスキップします。")
            continue

        # 各L2サイズ候補に対してループ
        for L2_size in possible_L2_sizes:
            # L2_df から対応するサイズのエントリを抽出
            match = L2_df[L2_df['Cache Size (KB)'] == L2_size]
            if match.empty:
                # このL2サイズがL2_dfに存在しない場合はスキップ
                continue

            # 複数候補がある場合は全て書き込む（連想度が異なるため）
            for _, l2_row in match.iterrows():
                L2_assoc = l2_row['Associativity']
                L2_access_time_ns = l2_row['Access Time (ns)']

                # L2レイテンシの計算
                # L2レイテンシ = Ceil (L2共有キャッシュ・アクセス時間 / CPUクロックサイクル時間)
                if cpu_clock_cycle_time_ns == float('inf') or cpu_clock_cycle_time_ns <= 0:
                    l2_latency_cycles = float('inf')
                    print(f"[警告] CPUクロックサイクル時間が不正なためL2レイテンシを計算できません。Core={core}, L1_size={L1_size}, L1_assoc={L1_assoc}, L2_size={L2_size}, L2_assoc={L2_assoc}")
                else:
                    l2_latency_cycles = math.ceil(L2_access_time_ns / cpu_clock_cycle_time_ns)

                # 総BCEコストの計算
                total_bce_cost = core + (L1_size / 2) + (L2_size / 32) # コア数 + L1_BCE + L2_BCE

                new_row = {
                    'Core Number': int(core), # intにキャスト
                    'CPU clock (GHz)': cpu_frequency_ghz, # floatのまま
                    'L1 Cache Size (KB)': int(L1_size), # intにキャスト
                    'L1 Associativity': int(L1_assoc), # intにキャスト
                    'L2 Cache Size (KB)': int(L2_size), # intにキャスト
                    'L2 Associativity': int(L2_assoc), # intにキャスト
                    'L2 latency (cycles)': int(l2_latency_cycles) if l2_latency_cycles != float('inf') else l2_latency_cycles, # 無限大以外はintにキャスト
                    'Total BCE Cost': int(total_bce_cost), # intにキャスト
                }

                rows.append(new_row)

# データフレームにまとめて追加
if rows:
    data = pd.concat([data, pd.DataFrame(rows)], ignore_index=True)
data.to_csv(data_csv, index=False)

print(f"[完了] {len(rows)}件を {data_csv} に書き込みました。")
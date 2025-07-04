import os
import re
import csv

# 入出力設定
result_dir = "generated_cfgs"
csv_filename = "cacti_results.csv"
sortcsv_filename = "sorted_redult.csv"

results = []

# ファイルごとに処理
for fname in os.listdir(result_dir):
    if not fname.endswith(".txt"):
        continue

    match = re.match(r"cache_(\d+)k_a(\d+)_b(\d+)\.txt", fname)
    if not match:
        continue
    cache_kb, assoc, block = map(int, match.groups())
    filepath = os.path.join(result_dir, fname)

    with open(filepath, "r") as f:
        content = f.read()

    # Access time 抽出
    access_match = re.search(r"Access time\s*\(ns\):\s*([\d.]+)", content)
    access_time = float(access_match.group(1)) if access_match else None

    # Read Energy 抽出
    energy_match = re.search(r"Read Energy\s*\(nJ\):\s*([\d.]+)", content)
    read_energy = float(energy_match.group(1)) if energy_match else None

    results.append({
        "Cache Size (KB)": cache_kb,
        "Associativity": assoc,
        "Block Size (B)": block,
        "Access Time (ns)": access_time,
        "Read Energy (nJ)": read_energy
    })

# CSV出力
with open(csv_filename, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

# sortした結果を出力
results.sort(key=lambda x: (x["Cache Size (KB)"], x["Associativity"], x["Block Size (B)"]))
with open(sortcsv_filename, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"✅ {csv_filename} に {len(results)} 件のデータを出力しました。")

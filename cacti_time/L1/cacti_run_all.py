import os
import subprocess
from itertools import product

# ===== 設定パラメータ =====
cache_sizes_kb = [2, 4, 8, 16, 32, 64, 128]  # KB単位
assoc_list = [2, 4, 8, 16, 32, 64]
block_sizes = [32]

# ===== ヘルパー関数 =====
def replace_line(text, startswith, new_line):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(startswith):
            lines[i] = new_line
            break
    return "\n".join(lines)

# ===== 準備 =====
template_file = "base.cfg"
output_dir = "generated_cfgs"
os.makedirs(output_dir, exist_ok=True)

with open(template_file, "r") as f:
    template = f.read()

total = len(cache_sizes_kb) * len(assoc_list) * len(block_sizes)
count = 0

# ===== 全組み合わせを処理 =====
for cs_kb, assoc, blk in product(cache_sizes_kb, assoc_list, block_sizes):
    cs_bytes = cs_kb * 1024
    cfg_content = template

    # 置換
    cfg_content = replace_line(cfg_content, "-size (bytes)", f"-size (bytes) {cs_bytes}")
    cfg_content = replace_line(cfg_content, "-block size (bytes)", f"-block size (bytes) {blk}")
    cfg_content = replace_line(cfg_content, "-associativity", f"-associativity {assoc}")

    # ファイル名作成
    base_name = f"cache_{cs_kb}k_a{assoc}_b{blk}"
    cfg_path = os.path.join(output_dir, f"{base_name}.cfg")
    result_path = os.path.join(output_dir, f"{base_name}.txt")

    # 書き込み
    with open(cfg_path, "w") as f:
        f.write(cfg_content)

    # CACTI 実行
    print(f"[{count+1}/{total}] Running: ./cacti -infile {cfg_path}")
    with open(result_path, "w") as outfile:
        subprocess.run(["./cacti", "-infile", cfg_path], stdout=outfile)

    count += 1

print(f"\n✅ 完了！{total}通りの組み合わせに対して .cfg と .txt を生成しました。")

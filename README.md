# Multi-Core CPU Performance Evaluation using gem5 📊

gem5シミュレータを用いて、異なるCPUおよびキャッシュ構成がアプリケーションの実行性能に与える影響を評価するプロジェクトです。
SPLASH-2ベンチマークを使用し、Pythonスクリプトによる自動化されたシミュレーション環境を構築しました。

## 🧪 Overview
キャッシュパラメータやクロック周波数を変化させ、ベンチマークの実行時間（`sim_seconds`）を計測・比較します。

* **Target:** SPLASH-2 Benchmarks (FFT, FMM)
* **Simulator:** gem5 (build/ALPHA/gem5.opt)
* **Parameters:**
    * CPU Clock Frequency
    * L1/L2 Cache Size & Associativity
    * L2 Latency

## 🛠️ Technologies
* **Language:** Python 3 (Automation Scripts), C/C++ (Benchmarks)
* **Libraries:** pandas (Data aggregation)
* **Environment:** Linux

## 📂 Scripts
* `make_data.py`: シミュレーション条件（キャッシュ構成等）の定義ファイル作成
* `run_simulation.py`: 定義に基づきgem5シミュレーションを一括実行
* `collect_results.py`: `stats.txt` から実行時間を抽出しCSVへ集計

## 🚀 Usage

```bash
# 1. Generate parameter CSV
python make_data.py

# 2. Run gem5 simulations
python run_simulation.py

# 3. Aggregate results
python collect_results.py

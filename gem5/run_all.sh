#!/bin/bash

# ===============================================================
#  parameters
# ===============================================================
CPU_CORES = (2 4 8 16 32)
L1_CACHE_SIZES = (2 4 8 16 32 64 128) # in KB
L2_CACHE_SIZES = (32 64 128 256 512 1024 2048) # in KB
L1_ASSOCS = (2 4 8 16 32 64) # L1 associativity
L2_ASSOCS = (2 4 8 16 32 64) # L2 associativity

BENCHMARKS = ( "fmm" "ocean" "raytrace" "cholesky" "fft" "lu" "radix" )

# Run simulations for all combinations of parameters
for CORE in "${CPU_CORES[@]}"; do
    for BENCHMARK in "${BENCHMARKS[@]}"; do
        # ===============================================================
        # set CMD and CMD_OPTIONS
        # ===============================================================
        case "$BENCHMARK" in
            "fmm")
                CMD="./splash2/fmm/FMM < ./splash2/fmm/inputs/input.2048.p" + "$CORE"
                CMD_OPTIONS=""
                ;;
            "ocean")
                CMD="./splash2/ocean/contiguous_partitions/OCEAN"
                CMD_OPTIONS="-n130 -p" + "$CORE"
                ;;
            "raytrace")
                CMD="./splash2/raytrace/RAYTRACE"
                CMD_OPTIONS="-p" + "$CORE" " ./splash2/raytrace/inputs/teapot.env"
                # 入力データの準備が必要：teapot.envの1行目と2行目を以下の通り変更
                # geometry /home/ubuntu/gem5/splash2/raytrace/inputs/teapot.geo
                # rlfile /home/ubuntu/gem5/splash2/raytrace/inputs/teapot.rl
                ;;
            "cholesky")
                CMD="./splash2/cholesky/CHOLESKY"
                CMD_OPTIONS="-p" + "$CORE" " ./splash2/cholesky/inputs/d750.O"
                ;;
            "fft")
                CMD="./splash2/fft/FFT"
                CMD_OPTIONS="-p" + "$CORE"
                ;;
            "lu")
                CMD="../splash2/lu/contiguous_blocks/LU"
                CMD_OPTIONS="-p" + "$CORE"
                ;;
            "radix")
                CMD="./splash2/radix/RADIX"
                CMD_OPTIONS="-p" + "$CORE"
                ;;
            *)
    
        L1_CACHE_SIZE = +"kB"   # kBを付けるの注意
        L2_CACHE_SIZE = +"kB"   # kBを付けるの注意

        # ===============================================================
        # run simulation command
        # ===============================================================
        echo "Running simulations for $CORE CPU cores..."
        ./build/ALPHA/gem5.opt -d "$OUTDIR" \
            se.py -n "$CORE" \
            --cpu-type=detailed --cpu-clock="$CPU_FREC" \
            --mem-type=SimpleMemory --caches --l2cache \
            --l1d_size="$L1_CACHE_SIZE" --l1d_assoc="$L1_ASSOC" \
            --l2_size="$L2_CACHE_SIZE" --l2_assoc="$L2_ASSOC" --l2_latency="$L2_LATENCY" \
            -c "$CMD" -o "$CMD_OPTIONS"
    done
done

# ここでは結果集計しない（Pythonスクリプトで実施）
echo "Simulation runs completed. Now run: python3 collect_stats.py"
#!/bin/bash

# Set the measurement interval
interval=2

# Set the log file name
output_dir="system_metrics"
mkdir -p "$output_dir"

cur_date=""
new_date=""
output_file=""

while true; do

    sleep $interval

    new_date=$(date +"%Y-%m-%d")
    if [ "$new_date" != "$cur_date" ]; then
        cur_date="$new_date"
        output_file="$output_dir/system_metrics_$cur_date.log"

        # Print log header
        echo "timestamp,procs_r,procs_b,swap_si,swap_so,io_bi,io_bo,system_in,system_cs,cpu_us,cpu_sy,cpu_id,cpu_wa,cpu_st,mem_total,mem_used,mem_free,mem_shared,mem_buffcache,mem_available" > "$output_file"
    fi

    # [ 1] : time           : YYYY/MM/DD hh:mm:ss
    curr_time=$(date +"%Y-%m-%d %H:%M:%S")

    # [ 1] : procs_r        : 実行待ちのプロセス数(実行待ちキューにあるプロセス数)
    # [ 2] : procs_b        : ブロックされたプロセス数(入出力などでブロックされているプロセス数)
    # [ 3] : mem_swapd      : invalid : スワップされたメモリサイズ(仮想メモリがスワップ領域に置き換えられたサイズ)[KB]
    # [ 4] : mem_free       : invalid : 空きメモリサイズ(物理メモリ中の空きメモリサイズ)[KB]
    # [ 5] : mem_buff       : invalid : バッファに用いられるメモリの量[KB]
    # [ 6] : mem_cache      : invalid : キャッシュに用いられるメモリの量[KB]
    # [ 7] : swap_si        : スワップイン(秒間のスワップイン量、スワップ領域からメモリへの読み込み)[KB/s]
    # [ 8] : swap_so        : スワップアウト(秒間のスワップアウト量、メモリからスワップ領域への書き込み)[KB/s]
    # [ 9] : io_bi          : ブロックデバイスからの読み取り(秒間のブロックデバイスからの読み取り量)[block/s]
    # [10] : io_bo          : ブロックデバイスへの書き込み(秒間のブロックデバイスへの書き込み量)[block/s]
    # [11] : system_in      : 割り込み(秒間の割り込み数)
    # [12] : system_cs      : コンテキストスイッチ(秒間のプロセスコンテキストスイッチ数)
    # [13] : cpu_us         : ユーザーモードで消費されたCPU時間の割合
    # [14] : cpu_sy         : システムモードで消費されたCPU時間の割合
    # [15] : cpu_id         : アイドル状態のCPU時間の割合
    # [16] : cpu_wa         : IO待ち状態のCPU時間の割合
    # [17] : cpu_st         : 仮想マシンのハイパーバイザーによるスティール時間の割合
    vmstat_result=$(vmstat 1 1 | awk 'NR == 3 { print $1","$2","$7","$8","$9","$10","$11","$12","$13","$14","$15","$16","$17","$18 }')

    # [ 2] : mem_total      : メモリの総量[KB]
    # [ 3] : mem_used       : 使用中のメモリの量[KB]
    # [ 4] : mem_free       : 未使用のメモリの量[KB]
    # [ 5] : mem_shared     : シェアメモリの量[KB]
    # [ 6] : mem_buffcache  : バッファメモリの量[KB]
    # [ 7] : mem_available  : 利用可能なメモリの量[KB]
    free_result=$(free | awk 'NR == 2 { print $2","$3","$4","$5","$6","$7 }')

    #echo "$(date +"%Y-%m-%d %H:%M:%S")$vmstat_result,$free_result" >> "$output_file"
    echo "$curr_time,$vmstat_result$free_result" >> "$output_file"

done

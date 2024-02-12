#!/bin/bash

# Set the measurement interval
# If you want to change it from "1", you need to divide each CPU parameter by that time.
interval=1

# Set the log file name
output_dir="system_metrics"
mkdir -p "$output_dir"

cur_date=""
new_date=""
output_file=""

#cpu_num=`grep physical.id /proc/cpuinfo | sort -u | wc -l`
cpu_num=`nproc`

stat=`cat /proc/stat | awk 'NR == 1'`
pre_cpu_us=0
pre_cpu_sy=0
pre_cpu_id=0
pre_cpu_wa=0
pre_cpu_st=0
pre_cpu_gu=0
cur_cpu_us=`echo $stat | awk '{ print $2  }'`
cur_cpu_sy=`echo $stat | awk '{ print $4  }'`
cur_cpu_id=`echo $stat | awk '{ print $5  }'`
cur_cpu_wa=`echo $stat | awk '{ print $6  }'`
cur_cpu_st=`echo $stat | awk '{ print $9  }'`
cur_cpu_gu=`echo $stat | awk '{ print $10 }'`

mem_total=`cat /proc/meminfo | awk 'NR == 1 { print $2 }'`

while true; do

    sleep $interval

    new_date=$(date +"%Y-%m-%d")
    if [ "$new_date" != "$cur_date" ]; then
        cur_date="$new_date"
        output_file="$output_dir/system_metrics_$cur_date.log"
        
        # Print log header
        echo "time,cpu_us,cpu_sy,cpu_id,cpu_wa,cpu_st,cpu_gu,cpu_usage_rate,mem_total,mem_used,mem_free,mem_shared,mem_buffcache,mem_available,mem_usage_rate" > "$output_file"

        find ./$output_dir -type f -name "system_metrics_*.log" -mtime +30 | xargs rm -f
    fi

    # [ 1] : time           : YYYY/MM/DD hh:mm:ss
    curr_time=$(date +"%Y-%m-%d %H:%M:%S")

    # [ 2] : cpu_us         : ユーザーモードで消費されたCPU時間の割合
    # [ 3] : cpu_sy         : システムモードで消費されたCPU時間の割合
    # [ 4] : cpu_id         : アイドル状態のCPU時間の割合
    # [ 5] : cpu_wa         : IO待ち状態のCPU時間の割合
    # [ 6] : cpu_st         : 仮想マシンのハイパーバイザーによるスティール時間の割合
    # [ 7] : cpu_gu         : 仮想マシンのCPU時間の割合
    # [ 8] : cpu_usage_rate : CPU使用率(100-cpu_id)
    stat=`cat /proc/stat | awk 'NR == 1'`
    pre_cpu_us=$cur_cpu_us
    pre_cpu_sy=$cur_cpu_sy
    pre_cpu_id=$cur_cpu_id
    pre_cpu_wa=$cur_cpu_wa
    pre_cpu_st=$cur_cpu_st
    pre_cpu_gu=$cur_cpu_gu
    cur_cpu_us=`echo $stat | awk '{ print $2  }'`
    cur_cpu_sy=`echo $stat | awk '{ print $4  }'`
    cur_cpu_id=`echo $stat | awk '{ print $5  }'`
    cur_cpu_wa=`echo $stat | awk '{ print $6  }'`
    cur_cpu_st=`echo $stat | awk '{ print $9  }'`
    cur_cpu_gu=`echo $stat | awk '{ print $10 }'`
    cpu_stat=$((cur_cpu_us-pre_cpu_us))","$((cur_cpu_sy-pre_cpu_sy))","$((cur_cpu_id-pre_cpu_id))","$((cur_cpu_wa-pre_cpu_wa))","$((cur_cpu_st-pre_cpu_st))","$((cur_cpu_gu-pre_cpu_gu))","$((100-(cur_cpu_id-pre_cpu_id)/cpu_num))

    # [ 9] : mem_total      : メモリの総量[KB]
    # [10] : mem_used       : 使用中のメモリの量[KB]
    # [11] : mem_free       : 未使用のメモリの量[KB]
    # [12] : mem_shared     : シェアメモリの量[KB]
    # [13] : mem_buffcache  : バッファメモリの量[KB]
    # [14] : mem_available  : 利用可能なメモリの量[KB]
    # [15] : mem_usage_rate : Memory使用率(mem_used/mem_total*100)
    free_result=$(free | awk 'NR == 2 { print $3","$4","$5","$6","$7 }')
    mem_used=`echo $free_result | cut -d "," -f 1`
    mem_stat=$mem_total","$free_result","$((100*mem_used/mem_total))

    echo "$curr_time,$cpu_stat,$mem_stat" >> "$output_file"
    #echo "$curr_time,$cpu_stat,$mem_stat"

done

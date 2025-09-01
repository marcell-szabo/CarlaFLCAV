#!/bin/bash

custom_exit_handler() {
    stop_monitoring
}

set -e

restart_blockchain() {
    cd $HOME/fabric-samples/test-network
    ./network.sh down
    ./network.sh up createChannel -c mychannel -ca
    ./network.sh deployCC -ccn basic -ccp ../CARLA_weight_publish/chaincode-go/ -ccl go
    ./network.sh createChannel -ca -c reputationchannel
    ./network.sh deployCC -c reputationchannel -ccn reputationCC -ccp ../CARLA_reputation/chaincode-go/ -ccl go
    echo Blockchain redeployed successfully!
}

reset_results() {
    cd $HOME/CarlaFLCAV/FLYolo
    cp -R fedmodels $simulation_dir/fedmodels
    rm -R fedmodels
}

get_historic_balance() {
    echo "Get historic balances of vehicles"
    directory_path="$HOME/CarlaFLCAV/FLYolo/raw_data/$town/"
    for dir in "$directory_path"vehicle*/; do
        if [ -d "$dir" ]; then
            basename_dir=$(basename $dir)
            echo "Matching Dir: $basename_dir"
            cd $HOME/fabric-samples/CARLA_reputation/application-gateway-go
            touch "$simulation_dir/$basename_dir.txt"
            ./reputationPublish query -owner=$basename_dir > "$simulation_dir/$basename_dir.txt"  
        fi
    done
}

# Function to start the monitoring in the background
start_monitoring() {
    echo "Monitoring started in the background."
    # Add CSV header
    echo "Timestamp, CPU Utilization (%), GPU Utilization (%), GPU used memory (MiB)" > $output_file

    # Monitor indefinitely
    while true; do
        timestamp=$(date +%T)
        cpu_utilization=$(top -n 1 -b | grep "Cpu(s)" | awk '{print $2}' | cut -d "%" -f1)
        gpu_utilization=$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits | awk -F ', ' '{print $1 "," $2}')
        echo "$timestamp, $cpu_utilization, $gpu_utilization" >> $output_file
        sleep 60
    done &
    pid=$!  # Get the process ID of the background job
}

# Function to stop the monitoring
stop_monitoring() {
    if [ -z "$pid" ]; then
        echo "Monitoring is not running."
    else
        end_time=$(date)
        echo "Monitoring stopped at $end_time."
        kill "$pid"  # Stop the background job
        pid=""  # Clear the process ID
    fi
}


delete_yolo_subfolders_in_raw_data() {
    parent_dir="$HOME/CarlaFLCAV/FLYolo/raw_data/$town"

    # Check if the parent directory exists
    if [ -d "$parent_dir" ]; then
        # Iterate through subdirectories
        for sub_dir in "$parent_dir"/*; do
            if [ -d "$sub_dir/yolo" ]; then
                rsync -a "$sub_dir/yolo/" "$sub_dir"
                rm -r "$sub_dir/yolo"
            fi
        done
    else
        echo "Parent directory does not exist: $parent_dir"
    fi
}

trap custom_exit_handler ERR

float_array=(1 10 100)
# Iterate over the float array elements
for r in "${float_array[@]}"; do
    for s in "${float_array[@]}"; do
        if [ "$s" -ne 10 ]; then
            continue
        # elif { [ "$r" -eq 0 ] || [ "$r" -eq 1 ] || [ "$r" -eq 10 ] || [ "$r" -eq 100 ]; } && { [ "$s" -eq 1 ] || [ "$s" -eq 10 ] || [ "$s" -eq 100 ]; }; then
        #     continue
        # elif  { [ "$r" -eq 0 ] && [ "$s" -eq 50 ]; }; then
        #     continue
        fi

        simulation_dir="$HOME/results/sim_$(date +%s)"
        output_file="$simulation_dir/utilization_data.csv"
        start_time=""
        end_time=""
        pid=""
        town="town02"
        directory_to_check="$HOME/CarlaFLCAV/FLYolo/fedmodels"
        if [ -d "$directory_to_check" ]; then
            # Directory exists, so delete it
            rm -r "$directory_to_check"
            echo "Directory deleted: $directory_to_check"
        fi
        delete_yolo_subfolders_in_raw_data
        mkdir $simulation_dir
        touch $output_file
        touch "$simulation_dir/r_$r-s_$s"
        restart_blockchain
        start_monitoring
        cd $HOME/CarlaFLCAV/FLYolo
        source ../venv/bin/activate
        python3 flcav_yolo.py -s $s -r $r
        stop_monitoring
        get_historic_balance
        reset_results
        deactivate
    done
done

# # Check command-line arguments
# if [ $# -eq 0 ]; then
#     echo "Usage: $0 <start|stop>"
#     exit 1
# fi

# # Main script logic
# case $1 in
#     "start")
#         if [ -n "$start_time" ]; then
#             echo "Monitoring is already running."
#         else
#             start_time=$(date)
#             start_monitoring
#         fi
#         ;;
#     "stop")
#         if [ -z "$start_time" ]; then
#             echo "Monitoring is not running."
#         else
#             stop_monitoring
#         fi
#         ;;
#     *)
#         echo "Usage: $0 <start|stop>"
#         exit 1
#         ;;
# esac

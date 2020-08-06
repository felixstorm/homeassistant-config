#!/usr/bin/with-contenv bashio

echo "[$(date)][Info] HDD Tools start"

CONFIG_PATH=/data/options.json

HDD_PATH="$(jq --raw-output '.hdd_path' $CONFIG_PATH)"
echo "[$(date)][Info] Configuration - disk path: $HDD_PATH" 

CHECK_PERIOD="$(jq --raw-output '.check_period' $CONFIG_PATH)"
echo "[$(date)][Info] Configuration - check period: $CHECK_PERIOD" 

OUTPUT_FILE="$(jq --raw-output '.output_file' $CONFIG_PATH)"
echo "[$(date)][Info] Configuration - output file: $OUTPUT_FILE" 

mkdir -p /share/hdd_tools/scripts/
cp /opt/main.sh /share/hdd_tools/scripts/main.sh

echo "[$(date)][Info] Init run"
/share/hdd_tools/scripts/main.sh

echo "[$(date)][Info] Cron tab update"
sed -i "s/TIME_TOKEN/$CHECK_PERIOD/g" /etc/cron.d/cron

echo "[$(date)][Info] Apply cron tab"
crontab /etc/cron.d/cron

if [ -b $HDD_PATH ]; then 
    echo "[$(date)][Info] Device $HDD_PATH found - staring CRON"    
    crond -f
else
    echo "[$(date)][Info] Device $HDD_PATH not found - exiting"    
    exit 1
fi

echo $(date) "HDD Tools exit"
CONFIG_PATH=/data/options.json

HDD_PATH="$(jq --raw-output '.hdd_path' $CONFIG_PATH)"
OUTPUT_FILE="$(jq --raw-output '.output_file' $CONFIG_PATH)"

SMARTCTL_OUTPUT=$(/usr/sbin/smartctl -a $HDD_PATH)
echo "$SMARTCTL_OUTPUT" > /share/hdd_tools/${OUTPUT_FILE}

ATTRIBUTES=$(echo "$SMARTCTL_OUTPUT" | egrep -o '^[0-9 ]+.*[0-9]+$' | awk '{print "\"" $2 "\":\"" $(NF) "\"," }' | awk '{print tolower($0)}' | tr -d '\n') 

function Sensor {
       if [ "$5" = "raw" ]; then
              MAIN_VALUE=$(echo "$SMARTCTL_OUTPUT" | grep $4 | awk '{print $(NF)}')
       else
              MAIN_VALUE=$(echo "$SMARTCTL_OUTPUT" | grep $4 | awk '{printf "%d",$5;}') # strip leading zeros
       fi
       API_CALL_BODY='{"state": "'"$MAIN_VALUE"'", "attributes": {"unit_of_measurement":"'"$2"'","friendly_name":"'"$3"'",'"${ATTRIBUTES::-1}"'}}'

       echo "[$(date)][Info] Sensor value: $MAIN_VALUE"
       echo "[$(date)][Debug] API call body: $API_CALL_BODY" > /proc/1/fd/1 2>/proc/1/fd/2

       curl -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
              -s \
              -o /dev/null \
              -H "Content-Type: application/json" \
              -d "$API_CALL_BODY" \
              -w "[$(date)][Info] Sensor update response code: %{http_code}\n" \
              http://supervisor/core/api/states/sensor.$1
}

Sensor hdd_endurance_remaining "%" "HDD Endurance Remaining" Wear_Leveling_Count
Sensor hdd_temp "°C" "HDD Temperature" Temperature_Cel raw

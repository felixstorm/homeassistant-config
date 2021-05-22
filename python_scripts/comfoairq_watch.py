comfoairq_sensors = [
    'comfoairq_power_usage',
    'comfoairq_power_usage_filtered',
    'comfoairq_bypass_state',
    'comfoairq_days_to_replace_filter',
    'comfoairq_exhaust_airflow',
    'comfoairq_exhaust_airflow_filtered',
    'comfoairq_exhaust_humidity',
    'comfoairq_exhaust_humidity_filtered',
    'comfoairq_exhaust_temperature',
    'comfoairq_inside_humidity',
    'comfoairq_inside_humidity_filtered',
    'comfoairq_inside_temperature',
    'comfoairq_outside_humidity',
    'comfoairq_outside_humidity_filtered',
    'comfoairq_outside_temperature',
    'comfoairq_supply_airflow',
    'comfoairq_supply_airflow_filtered',
    'comfoairq_supply_humidity',
    'comfoairq_supply_humidity_filtered',
    'comfoairq_supply_temperature',
]

last_updated = hass.states.get('sensor.{}'.format(comfoairq_sensors[0])).last_updated
now = hass.states.get('sensor.time').last_updated
diff_minutes = (now - last_updated).total_seconds() / 60

logger.info("ComfoAirQ {} last updated: {} (now: {}, diff_minutes: {})".format(comfoairq_sensors[0], last_updated, now, diff_minutes))

if diff_minutes > 15:
    for sensor in comfoairq_sensors:
        hass.states.set('sensor.{}'.format(sensor), 'unavailable')
    logger.warning("Set states of sensors to unavailable: {}".format(comfoairq_sensors))

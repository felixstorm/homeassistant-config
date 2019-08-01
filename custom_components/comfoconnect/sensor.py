"""Platform to control a Zehnder ComfoAir Q350/450/600 ventilation unit."""
import logging

from homeassistant.const import CONF_RESOURCES, TEMP_CELSIUS
from homeassistant.helpers.dispatcher import dispatcher_connect
from homeassistant.helpers.entity import Entity

from . import (
    ATTR_AIR_FLOW_EXHAUST, ATTR_AIR_FLOW_SUPPLY, ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE, ATTR_OUTSIDE_HUMIDITY, ATTR_OUTSIDE_TEMPERATURE,
    DOMAIN, SIGNAL_COMFOCONNECT_UPDATE_RECEIVED, ComfoConnectBridge,
    ATTR_SUPPLY_TEMPERATURE, ATTR_SUPPLY_HUMIDITY, ATTR_EXHAUST_TEMPERATURE,
    ATTR_EXHAUST_HUMIDITY, ATTR_DAYS_TO_REPLACE_FILTER, ATTR_BYPASS_STATE)

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the ComfoConnect fan platform."""
    from pycomfoconnect import (
        SENSOR_TEMPERATURE_EXTRACT, SENSOR_HUMIDITY_EXTRACT,
        SENSOR_TEMPERATURE_OUTDOOR, SENSOR_HUMIDITY_OUTDOOR,
        SENSOR_FAN_SUPPLY_FLOW, SENSOR_FAN_EXHAUST_FLOW,
        SENSOR_TEMPERATURE_SUPPLY, SENSOR_HUMIDITY_SUPPLY,
        SENSOR_TEMPERATURE_EXHAUST, SENSOR_HUMIDITY_EXHAUST,
        SENSOR_DAYS_TO_REPLACE_FILTER, SENSOR_BYPASS_STATE)

    global SENSOR_TYPES
    SENSOR_TYPES = {
        ATTR_CURRENT_TEMPERATURE: [
            'Inside Temperature',
            TEMP_CELSIUS,
            'mdi:thermometer',
            SENSOR_TEMPERATURE_EXTRACT
        ],
        ATTR_CURRENT_HUMIDITY: [
            'Inside Humidity',
            '%',
            'mdi:water-percent',
            SENSOR_HUMIDITY_EXTRACT
        ],
        ATTR_OUTSIDE_TEMPERATURE: [
            'Outside Temperature',
            TEMP_CELSIUS,
            'mdi:thermometer',
            SENSOR_TEMPERATURE_OUTDOOR
        ],
        ATTR_OUTSIDE_HUMIDITY: [
            'Outside Humidity',
            '%',
            'mdi:water-percent',
            SENSOR_HUMIDITY_OUTDOOR
        ],
        ATTR_AIR_FLOW_SUPPLY: [
            'Supply airflow',
            'm³/h',
            'mdi:air-conditioner',
            SENSOR_FAN_SUPPLY_FLOW
        ],
        ATTR_AIR_FLOW_EXHAUST: [
            'Exhaust airflow',
            'm³/h',
            'mdi:air-conditioner',
            SENSOR_FAN_EXHAUST_FLOW
        ],
        ATTR_SUPPLY_TEMPERATURE: [
            'Supply Temperature',
            TEMP_CELSIUS,
            'mdi:thermometer',
            SENSOR_TEMPERATURE_SUPPLY
        ],
        ATTR_SUPPLY_HUMIDITY: [
            'Supply Humidity',
            '%',
            'mdi:water-percent',
            SENSOR_HUMIDITY_SUPPLY
        ],
        ATTR_EXHAUST_TEMPERATURE: [
            'Exhaust Temperature',
            TEMP_CELSIUS,
            'mdi:thermometer',
            SENSOR_TEMPERATURE_EXHAUST
        ],
        ATTR_EXHAUST_HUMIDITY: [
            'Exhaust Humidity',
            '%',
            'mdi:water-percent',
            SENSOR_HUMIDITY_EXHAUST
        ],
        ATTR_DAYS_TO_REPLACE_FILTER: [
            'Days to replace filter',
            'days',
            None,
            SENSOR_DAYS_TO_REPLACE_FILTER
        ],
        ATTR_BYPASS_STATE: [
            'Bypass State',
            '%',
            'mdi:percent',
            SENSOR_BYPASS_STATE
        ],
    }

    ccb = hass.data[DOMAIN]

    sensors = []
    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type not in SENSOR_TYPES:
            _LOGGER.warning("Sensor type: %s is not a valid sensor.",
                            sensor_type)
            continue

        sensors.append(
            ComfoConnectSensor(
                hass,
                name="%s %s" % (ccb.name, SENSOR_TYPES[sensor_type][0]),
                ccb=ccb,
                sensor_type=sensor_type
            )
        )

    add_entities(sensors, True)


class ComfoConnectSensor(Entity):
    """Representation of a ComfoConnect sensor."""

    def __init__(self, hass, name, ccb: ComfoConnectBridge,
                 sensor_type) -> None:
        """Initialize the ComfoConnect sensor."""
        self._ccb = ccb
        self._sensor_type = sensor_type
        self._sensor_id = SENSOR_TYPES[self._sensor_type][3]
        self._name = name

        # Register the requested sensor
        self._ccb.comfoconnect.register_sensor(self._sensor_id)

        def _handle_update(var):
            if var == self._sensor_id and self.hass is not None:    # HACK: prevent errors if an update is signaled before Entity is fully initialized
                _LOGGER.debug('Dispatcher update for %s.', var)
                self.schedule_update_ha_state()

        # Register for dispatcher updates
        dispatcher_connect(
            hass, SIGNAL_COMFOCONNECT_UPDATE_RECEIVED, _handle_update)

    @property
    def state(self):
        """Return the state of the entity."""
        try:
            return self._ccb.data[self._sensor_id]
        except KeyError:
            return None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return SENSOR_TYPES[self._sensor_type][2]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return SENSOR_TYPES[self._sensor_type][1]

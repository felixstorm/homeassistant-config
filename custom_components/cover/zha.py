"""
Covers on Zigbee Home Automation networks.
"""
import logging
import asyncio
import random
from homeassistant.components import cover, zha
from homeassistant.const import STATE_UNKNOWN

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['zha']


async def async_setup_platform(hass, config, async_add_devices,
                               discovery_info=None):
    """Set up the Zigbee Home Automation covers."""
    discovery_info = zha.get_discovery_info(hass, discovery_info)
    if discovery_info is None:
        return

    caps = await zha.safe_read(discovery_info['endpoint'].window_covering, 
                               ['current_position_lift_percentage', 'current_position_tilt_percentage'], 
                               allow_cache=True)
    current_position_lift_percentage = caps.get('current_position_lift_percentage')
    _LOGGER.debug("current_position_lift_percentage for %s is %s", discovery_info['unique_id'], current_position_lift_percentage)
    discovery_info['supports_set_position'] = (current_position_lift_percentage is not None and current_position_lift_percentage <= 100)
    current_position_tilt_percentage = caps.get('current_position_tilt_percentage')
    _LOGGER.debug("current_position_tilt_percentage for %s is %s", discovery_info['unique_id'], current_position_tilt_percentage)
    discovery_info['supports_set_tilt_position'] = (current_position_tilt_percentage is not None and current_position_tilt_percentage <= 100)

    # async def safe(coro):
    #     """Run coro, catching ZigBee delivery errors, and ignoring them."""
    #     import zigpy.exceptions
    #     try:
    #         await coro
    #     except zigpy.exceptions.DeliveryError as exc:
    #         _LOGGER.warning("Ignoring error during setup: %s", exc)

    # from zigpy.zcl.clusters.closures import WindowCovering
    # in_clusters = discovery_info['in_clusters']
    # cluster = in_clusters[WindowCovering.cluster_id]
    # await safe(cluster.bind())
    # await safe(cluster.configure_reporting(0x0008, 1, 600, 1))    # current_position_lift_percentage
    # await safe(cluster.configure_reporting(0x0009, 1, 600, 1))    # current_position_tilt_percentage

    async_add_devices([ZhaCover(**discovery_info)], update_before_add=True)


class ZhaCover(zha.Entity, cover.CoverDevice):
    """Representation of a ZHA cover."""

    def __init__(self, **kwargs):
        """Initialize the ZHA cover."""
        super().__init__(**kwargs)
        self._current_position_lift = None
        self._current_position_tilt = None
        self._supported_features = cover.SUPPORT_OPEN | cover.SUPPORT_CLOSE | cover.SUPPORT_STOP
        if kwargs.get('supports_set_position'):
            self._supported_features |= cover.SUPPORT_SET_POSITION
        if kwargs.get('supports_set_tilt_position'):
            self._supported_features |= cover.SUPPORT_SET_TILT_POSITION

    def attribute_updated(self, attribute, value):
        """Handle attribute updates on this cluster."""
        _LOGGER.debug("Attribute updated: %s, 0x%04x = %s", self.entity_id, attribute, value)
        if attribute == 0x0008:    # current_position_lift_percentage
            self.update_lift(value)
        if attribute == 0x0009:    # current_position_tilt_percentage
            self.update_tilt(value)
        self.async_schedule_update_ha_state()


    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        await self._endpoint.window_covering.down_close()

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self._endpoint.window_covering.up_open()

    async def async_stop_cover(self, **kwargs):
        """Stop any movements."""
        await self._endpoint.window_covering.stop()

    async def async_set_cover_position(self, **kwargs):
        """Go to position."""
        if cover.ATTR_POSITION not in kwargs:
            return
        await self._endpoint.window_covering.go_to_lift_percentage(100 - kwargs.get(cover.ATTR_POSITION))

    async def async_set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        if cover.ATTR_TILT_POSITION not in kwargs:
            return
        await self._endpoint.window_covering.go_to_tilt_percentage(100 - kwargs.get(cover.ATTR_TILT_POSITION))


    # @property
    # def should_poll(self) -> bool:
    #     """Let zha handle polling."""
    #     return False

    @property
    def current_cover_position(self):
        """Return the current position of ZHA cover."""
        if self._current_position_lift is not None:
            return self._current_position_lift
        return STATE_UNKNOWN

    @property
    def current_cover_tilt_position(self):
        """Return current position of ZHA cover tilt."""
        if self._current_position_tilt is not None:
            return self._current_position_tilt
        return STATE_UNKNOWN

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self._current_position_lift is not None:
            return bool(self.current_cover_position == 0)

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._supported_features


    async def async_update(self):
        """Retrieve latest state."""
        _LOGGER.debug("*** update called for %s", self.entity_id)
        await asyncio.sleep(random.uniform(0, 10.0))    # random delay to distribute load on zigbee stick & network as long as we poll devices
        _LOGGER.debug("      update delay done for %s", self.entity_id)
        zha_attrs = await zha.safe_read(self._endpoint.window_covering, 
                                        ['current_position_lift_percentage', 'current_position_tilt_percentage'], 
                                        allow_cache=False)
        self.update_lift(zha_attrs.get('current_position_lift_percentage'))
        self.update_tilt(zha_attrs.get('current_position_tilt_percentage'))
        _LOGGER.debug("      update finished for %s", self.entity_id)

    def update_lift(self, zha_position_lift_percentage):
        if zha_position_lift_percentage is not None:
            if zha_position_lift_percentage <= 100:
                self._current_position_lift = 100 - zha_position_lift_percentage
            else:
                self._current_position_lift = None

    def update_tilt(self, zha_position_tilt_percentage):
        if zha_position_tilt_percentage is not None:
            if zha_position_tilt_percentage <= 100:
                self._current_position_tilt = 100 - zha_position_tilt_percentage
            else:
                self._current_position_tilt = None

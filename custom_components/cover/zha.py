"""
Covers on Zigbee Home Automation networks.
"""
import logging
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

    # caps = await zha.safe_read(discovery_info['endpoint'].window_covering, ['window_covering_type', 'config_status'])
    # discovery_info['window_covering_type'] = caps.get('window_covering_type')
    # discovery_info['config_status'] = caps.get('config_status')

    async_add_devices([ZhaCover(**discovery_info)], update_before_add=True)


class ZhaCover(zha.Entity, cover.CoverDevice):
    """Representation of a ZHA cover."""

    def __init__(self, **kwargs):
        """Initialize the ZHA cover."""
        super().__init__(**kwargs)
        self._supported_features = 0
        self._current_position = None

        self._supported_features |= cover.SUPPORT_OPEN
        self._supported_features |= cover.SUPPORT_CLOSE
        self._supported_features |= cover.SUPPORT_STOP
        self._supported_features |= cover.SUPPORT_SET_POSITION
        self._supported_features |= cover.SUPPORT_SET_TILT_POSITION

        # covering_type = kwargs.get('window_covering_type')
        # config_status = kwargs.get('config_status')
        # if covering_type in (0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x08, 0x09):
        #     self._supported_features |= cover.SUPPORT_OPEN
        #     self._supported_features |= cover.SUPPORT_CLOSE
        #     self._supported_features |= cover.SUPPORT_STOP
        #     if config_status & 0b1000:
        #         self._supported_features |= cover.SUPPORT_SET_POSITION
        # if covering_type in (0x06, 0x07, 0x08) and config_status & 0b10000:
        #     self._supported_features |= cover.SUPPORT_SET_TILT_POSITION


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
        await self._endpoint.window_covering.go_to_lift_percentage(kwargs.get(ATTR_POSITION))


    @property
    def supported_features(self):
        """Flag supported features."""
        return self._supported_features

    @property
    def current_cover_position(self):
        """Return the current position of ZHA cover."""
        if self._current_position is not None:
            # if self._current_position <= 5:
            #     return 0
            # elif self._current_position >= 95:
            #     return 100
            return self._current_position

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self._current_position is not None:
            return bool(self.current_cover_position == 0)

    async def async_update(self):
        """Retrieve latest state."""
        zha_position = (await zha.safe_read(self._endpoint.window_covering, ['current_position_lift_percentage'])).get('current_position_lift_percentage')
        if zha_position is not None:
            if zha_position <= 100:
                self._current_position = 100 - zha_position
            else:
                self._current_position = None

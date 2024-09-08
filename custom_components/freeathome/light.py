""" Support for Free@Home lights dimmers """
import logging
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ColorMode, LightEntity)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# 'switch' will receive discovery_info={'optional': 'arguments'}
# as passed in above. 'light' will receive discovery_info=None
async def async_setup_entry(hass, config_entry, async_add_devices, discovery_info=None):
    """ switch/light specific code."""

    _LOGGER.info('FreeAtHome setup light')

    sysap = hass.data[DOMAIN][config_entry.entry_id]

    devices = sysap.get_devices('light')

    for device_object in devices:
        async_add_devices([FreeAtHomeLight(device_object)])


class FreeAtHomeLight(LightEntity):
    """ Free@home light """
    light_device = None
    _name = ''
    _state = None
    _brightness = None
    _is_dimmer = None

    def __init__(self, device):
        self.light_device = device
        self._name = self.light_device.name
        self._state = self.light_device.state
        self._is_dimmer = self.light_device.is_dimmer()
        if self.light_device.brightness is not None:
            self._brightness = int(float(self.light_device.brightness) * 2.55)
        else:
            self._brightness = None

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def device_info(self):
        """Return device id."""
        return self.light_device.device_info

    @property
    def unique_id(self):
        """Return the ID """
        return self.light_device.serialnumber + '/' + self.light_device.channel_id

    @property
    def should_poll(self):
        """Return that polling is not necessary."""
        return False

    @property
    def color_mode(self) -> str | None:
        """Return the color mode of the light."""                
        if self._is_dimmer:
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF
    
    @property
    def supported_color_modes(self) -> set[str] | None:
        """Flag supported color modes."""
        if self._is_dimmer:
            return {ColorMode.BRIGHTNESS}
        return {ColorMode.ONOFF}    

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    @property
    def brightness(self):
        """Brightness of this light between 0..255."""
        return self._brightness

    async def async_added_to_hass(self):
        """Register callback to update hass after device was changed."""

        async def after_update_callback(device):
            """Call after device was updated."""
            await self.async_update_ha_state(True)

        self.light_device.register_device_updated_cb(after_update_callback)

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on.
        """
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            self.light_device.set_brightness(int(self._brightness / 2.55))

        await self.light_device.turn_on()
        self._state = True

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        await self.light_device.turn_off()
        self._state = False

    async def async_update(self):
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self.light_device.is_on()
        if self.light_device.brightness is not None:
            self._brightness = int(float(self.light_device.get_brightness()) * 2.55)

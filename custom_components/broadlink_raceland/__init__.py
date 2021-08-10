"""The Broadlink-Raceland integration."""
from __future__ import annotations

from dataclasses import dataclass, field

from .device import BroadlinkDevice
#from .heartbeat import BroadlinkHeartbeat


from homeassistant import core
import logging


from .const import DOMAIN
from .services import setup_service

_LOGGER = logging.getLogger(__name__)



@dataclass
class BroadlinkData:
    """Class for sharing data within the Broadlink integration."""

    devices: dict = field(default_factory=dict)
    platforms: dict = field(default_factory=dict)
    #heartbeat: BroadlinkHeartbeat | None = None
    heartbeat: None = None


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Broadlink-Raceland component."""
    await setup_service(hass, config)
    return True



async def async_setup_entry(hass, entry):
    """Set up a Broadlink device from a config entry."""
    data = hass.data[DOMAIN]
    _LOGGER.info("Entered async_setup_entry. Data is %s", data)
    
    #if data.heartbeat is None:
        #data.heartbeat = BroadlinkHeartbeat(hass)
        #hass.async_create_task(data.heartbeat.async_setup())

    device = BroadlinkDevice(hass, entry)
    return await device.async_setup()


# async def async_unload_entry(hass, entry):
#     """Unload a config entry."""
#     data = hass.data[DOMAIN]

#     device = data.devices.pop(entry.entry_id)
#     result = await device.async_unload()

#     if not data.devices:
#         await data.heartbeat.async_unload()
#         data.heartbeat = None

#     return result

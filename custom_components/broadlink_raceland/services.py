import logging
import broadlink as blk
from broadlink.exceptions import (
    AuthenticationError,
    BroadlinkException,
    NetworkTimeoutError,
)

import errno
import socket

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_TIMEOUT, CONF_TYPE
from homeassistant.config_entries import ConfigFlow
from homeassistant import data_entry_flow
from .const import DEFAULT_TIMEOUT, DOMAIN, DOMAINS_AND_TYPES


_LOGGER = logging.getLogger(__name__)


async def setup_service(hass, config):
    async def handle_register_broadlink_devices(call):
        """Handle calls to register_broadlink_devices."""
        _LOGGER.info("Scanning local network for broadlink devices")

        errors = {}
        try:
            # devices = blk.discover(timeout=DEFAULT_TIMEOUT)
            device = blk.hello(host="192.168.1.166")
        except NetworkTimeoutError:
            errors["base"] = "cannot_connect"
            err_msg = "Device not found"

        except OSError as err:
            if err.errno in {errno.EINVAL, socket.EAI_NONAME}:
                errors["base"] = "invalid_host"
                err_msg = "Invalid hostname or IP address"
            elif err.errno == errno.ENETUNREACH:
                errors["base"] = "cannot_connect"
                err_msg = str(err)
            else:
                errors["base"] = "unknown"
                err_msg = str(err)

        else:
            ##Testing--------
            # for device in devices:
            _LOGGER.info("Found the devices: %s", device)
            device.timeout = DEFAULT_TIMEOUT
            await async_check_device(device)
            return await async_step_auth(device)
        _LOGGER.error(err_msg)
        # for device in devices:
        #    _LOGGER.info("Found the device: %s", device)

    # Register service
    hass.services.async_register(
        DOMAIN, "register_broadlink_devices", handle_register_broadlink_devices
    )


async def async_check_device(device, raise_on_progress=True):
    """Check device model"""
    _LOGGER.info("Checking device")
    supported_types = set.union(*DOMAINS_AND_TYPES.values())
    if device.type not in supported_types:
        _LOGGER.error(
            "Unsupported device: %s. If it worked before, please open "
            "an issue at https://github.com/home-assistant/core/issues",
            hex(device.devtype),
        )
        raise data_entry_flow.AbortFlow(
            "not_supported"
        )  # """Exception to indicate a flow needs to be aborted."""


async def async_step_auth(device):
    """Authenticate to the device."""
    _LOGGER.info("Running Device Authentication for %s", device.model)
    errors = {}
    try:
        device.auth()

    except AuthenticationError:
        errors["base"] = "invalid_auth"
        # await self.async_set_unique_id(device.mac.hex())
        # return await self.async_step_reset(errors=errors)

    except NetworkTimeoutError as err:
        errors["base"] = "cannot_connect"
        err_msg = str(err)

    except BroadlinkException as err:
        errors["base"] = "unknown"
        err_msg = str(err)

    except OSError as err:
        if err.errno == errno.ENETUNREACH:
            errors["base"] = "cannot_connect"
            err_msg = str(err)
        else:
            errors["base"] = "unknown"
            err_msg = str(err)

    else:
        if device.is_locked:
            return await async_step_unlock(device)
        return await async_step_finish(device)

    _LOGGER.error(
        "Failed to authenticate to the device at %s: %s", device.host[0], err_msg
    )


async def async_step_unlock(device):
    """Unlock the device.

    The authentication succeeded, but the device is locked.
    We can unlock to prevent authorization errors.
    """
    # await self.hass.async_add_executor_job(device.set_lock, False)
    errors = {}

    try:
        device.set_lock(False)

    except NetworkTimeoutError as err:
        errors["base"] = "cannot_connect"
        err_msg = str(err)

    except BroadlinkException as err:
        errors["base"] = "unknown"
        err_msg = str(err)

    except OSError as err:
        if err.errno == errno.ENETUNREACH:
            errors["base"] = "cannot_connect"
            err_msg = str(err)
        else:
            errors["base"] = "unknown"
            err_msg = str(err)

    else:
        return await async_step_finish(device)

    _LOGGER.error("Failed to unlock the device at %s: %s", device.host[0], err_msg)


async def async_step_finish(device):
    """Choose a name for the device and create config entry."""

    # Abort reauthentication flow.
    # self._abort_if_unique_id_configured(
    #    updates={CONF_HOST: device.host[0], CONF_TIMEOUT: device.timeout}
    # ) Implement a way to check if the device is already configured

    _LOGGER.info("Running step finish %s", device.model)

    return ConfigFlow.async_create_entry(
        ConfigFlow,
        title=device.name,
        data={
            CONF_HOST: device.host[0],
            CONF_MAC: device.mac.hex(),
            CONF_TYPE: device.devtype,
            CONF_TIMEOUT: device.timeout,
        },
    )

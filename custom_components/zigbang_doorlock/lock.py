from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [ZigbangLockEntity(coordinator, device)
                for device in coordinator.data]
    async_add_entities(entities, True)


class ZigbangLockEntity(CoordinatorEntity, LockEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, device: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self._device_id = device.get("device_id")
        self._attr_name = device.get("name", "Doorlock")
        self._attr_unique_id = f"{self._device_id}_lock"

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def _device_data(self) -> dict[str, Any]:
        return next(
            (device for device in self.coordinator.data if device.get(
                "device_id") == self._device_id),
            {},
        )

    @property
    def is_locked(self) -> bool:
        return self._attr_is_locked

    async def async_lock(self, **kwargs: Any) -> None:
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        await self.coordinator.async_unlock(self._device_id)

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device_data.get("name"),
            "model": self._device_data.get("model"),
            "manufacturer": "Zigbang Doorlock",
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_locked = bool(self._device_data.get("locked", True))
        self.async_write_ha_state()

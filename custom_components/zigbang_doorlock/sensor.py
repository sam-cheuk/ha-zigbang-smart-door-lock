from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for device in coordinator.data:
        entities.append(ZigbangBatterySensor(coordinator, device))
        entities.append(ZigbangMessageSensor(coordinator, device))
    async_add_entities(entities, True)


class ZigbangBatterySensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, device: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self._device_id = device.get("device_id")
        self._attr_name = f"{device.get('name', 'Doorlock')} Battery"
        self._attr_unique_id = f"{self._device_id}_battery"
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_class = "battery"

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def _device_data(self) -> dict[str, Any]:
        return next(
            (device for device in self.coordinator.data if device.get("device_id") == self._device_id),
            {},
        )

    @property
    def native_value(self) -> int:
        return int(self._device_data.get("battery", 0))

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device_data.get("name"),
            "model": self._device_data.get("model"),
            "manufacturer": "Zigbang Doorlock",
        }


class ZigbangMessageSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, device: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self._device_id = device.get("device_id")
        self._attr_name = f"{device.get('name', 'Doorlock')} Message"
        self._attr_unique_id = f"{self._device_id}_message"

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def _device_data(self) -> dict[str, Any]:
        return next(
            (device for device in self.coordinator.data if device.get("device_id") == self._device_id),
            {},
        )

    @property
    def native_value(self) -> str:
        return str(self._device_data.get("msgText", ""))

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device_data.get("name"),
            "model": self._device_data.get("model"),
            "manufacturer": "Zigbang Doorlock",
        }

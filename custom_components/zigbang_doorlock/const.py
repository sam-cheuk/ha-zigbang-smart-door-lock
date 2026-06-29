from __future__ import annotations

from typing import Final

DOMAIN: Final = "zigbang_doorlock"
PLATFORMS: Final = ["lock", "sensor"]
SCAN_INTERVAL: Final = 60

CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_IMEI: Final = "imei"

PUSH_TOKEN: Final = None
FCM_SENDER_ID: Final = "404305338948"

DEFAULT_IMEI: Final = None

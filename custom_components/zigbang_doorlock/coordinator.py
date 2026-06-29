from __future__ import annotations

import logging
import asyncio
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_PASSWORD, CONF_USERNAME, CONF_IMEI, PUSH_TOKEN, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class ZigbangClient:
    def __init__(self, username: str, password: str, imei: str | None = None, push_token: str | None = None) -> None:
        self.username = username
        self.password = password
        self.imei = imei or str(uuid.getnode())
        self.push_token = push_token or ""
        self._session: aiohttp.ClientSession | None = None
        self._member_id: str | None = None
        self._auth_token: str | None = None
        self._auth_code: str | None = None
        self._headers = {
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "acceptLanguage": "en_US",
            "Host": "iot.samsung-ihp.com:8088",
            "User-Agent": "okhttp/4.2.1",
            "Authorization": "CUL ",
        }
        self._auth_body = {
            "apiVer": "v20",
            "authNumber": "",
            "countryCd": "KR",
            "locale": "en_US",
            "locationAgreeYn": "N",
            "mobileNum": "",
            "osVer": "13",
            "overwrite": True,
            "pushToken": self.push_token,
            "timeZone": int(datetime.now().astimezone().tzinfo.utcoffset(None).total_seconds() / 3600),
        }
        self._base_url = "https://iot.samsung-ihp.com:8088/openhome/"
        self._auth_lock = asyncio.Lock()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(base_url=self._base_url)
        return self._session

    async def async_get_devices(self) -> list[dict[str, Any]]:
        await self._ensure_authenticated()
        url = "v20/doorlockctrl/membersdoorlocklist?createDate={}&favoriteYn=A&hashData=&memberId={}"
        response = await self._request(url.format(self._createdate(), self._member_id), "GET")
        devices: list[dict[str, Any]] = []
        for item in response.get("doorlockVOList", []):
            status = item.get("doorlockStatusVO", {})
            history = item.get("recentHistoryVOList", {})
            devices.append(
                {
                    "device_id": item.get("deviceId"),
                    "name": item.get("deviceNm"),
                    "model": item.get("productId"),
                    "locked": status.get("locked", True),
                    "battery": status.get("battery", 0),
                    "rgstDt": history.get("rgstDt"),
                    "msgText": history.get("msgText", ""),
                }
            )
        return devices

    async def async_unlock(self, device_id: str) -> None:
        await self._ensure_authenticated()
        payload = {
            "createDate": self._createdate(),
            "deviceId": device_id,
            "open": True,
            "isSecurityMode": False,
            "memberId": self._member_id,
            "securityModeRptEndDt": "",
            "securityModeRptStartDt": "",
        }
        self._add_hash(payload)
        await self._request("v20/doorlockctrl/open", "PUT", data=payload)

    async def _ensure_authenticated(self) -> None:
        if self._auth_token and self._member_id:
            return
        async with self._auth_lock:
            if self._auth_token and self._member_id:
                return
            await self._get_appver()
            body = {**self._auth_body, "createDate": self._createdate(), "loginId": self.username,
                    "pwd": self._hash(self.password), "imei": self.imei}
            self._add_hash(body)
            response = await self._request("v10/user/login", "PUT", data=body, skip_auth=True)
            self._auth_token = response["authToken"]
            self._auth_code = response["authCode"]
            self._member_id = response["memberId"]
            self._headers["Authorization"] = f"CUL {self._auth_token}"
            self._headers["AuthCode"] = self._auth_code

    async def _get_appver(self) -> None:
        if "Authorization" in self._headers:
            self._headers["Authorization"] = "CUL "
        if "AuthCode" in self._headers:
            self._headers.pop("AuthCode", None)
        response = await self._request(
            "v20/appsetting/getappver?createDate={}&hashData=&osTypeCd=ADR%20".format(
                self._createdate()),
            "GET",
            skip_auth=True,
        )
        self._auth_body["appVer"] = response["AppVersionList"][0]["osAppVer"]
        self._auth_body["osTypeCd"] = response["AppVersionList"][0]["osTypeCd"]

    async def _request(self, url: str, method: str, data: dict[str, Any] | None = None, skip_auth: bool = False) -> dict[str, Any]:
        session = await self._get_session()
        kwargs = {"headers": self._headers}
        if method in {"PUT", "POST"} and data is not None:
            kwargs["json"] = data
        try:
            async with session.request(method, url, **kwargs) as response:
                if response.status == 401 and not skip_auth and url != "v10/user/login":
                    self._auth_token = None
                    self._member_id = None
                    self._headers.pop("AuthCode", None)
                    self._headers["Authorization"] = "CUL "
                    await self._ensure_authenticated()
                    async with session.request(method, url, **kwargs) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as err:
            if err.status == 401:
                raise ConfigEntryAuthFailed("Authentication failed") from err
            raise UpdateFailed(f"Request failed: {err}") from err
        except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Network error: {err}") from err

    def _add_hash(self, data: dict[str, Any]) -> None:
        data["hashData"] = self._hash(
            "".join(str(value) for value in data.values()))

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha512(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _createdate() -> str:
        return datetime.now().strftime("%Y%m%d%H%M%S")


class ZigbangDataUpdateCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.client = ZigbangClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            imei=entry.data.get(CONF_IMEI),
            push_token=entry.data.get(PUSH_TOKEN),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            return await self.client.async_get_devices()
        except ConfigEntryAuthFailed:
            raise
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Unable to fetch Zigbang data: {err}") from err

    async def async_unlock(self, device_id: str) -> None:
        await self.client.async_unlock(device_id)
        await self.async_request_refresh()

import datetime
import hashlib
import hmac
from collections import OrderedDict
from typing import Any, Dict, Optional

import httpx

from exeptions import FrekassaException


class FreeKassa:
    API_URL = "https://api.freekassa.ru/v1/"
    API_BALANCE_ROUTE = "balance"
    API_ORDERS_ROUTE = "orders"
    API_ORDERS_CREATE_ROUTE = "orders/create"

    def __init__(self, api_key: str, shop_id: str):
        self._api_key = api_key
        self._shop_id = shop_id

    def _set_nonce(self):
        self._nonce = int(datetime.datetime.now().timestamp())

    def _get_data(self, additional_fields: Dict[str, Any]) -> OrderedDict[str, Any]:
        data = OrderedDict({"shopId": self._shop_id, "nonce": self._nonce})
        data.update(additional_fields)
        data.update({"signature": self._get_signature(data=data)})

        return data

    def _get_url(self, route: str, **kwargs) -> str:
        url = f"{self.API_URL}{route}"
        for key, value in kwargs:
            url = url.replace(f"%{key}%", value)
        return url

    async def _request(
        self,
        route: str,
        additional_fields: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        self._set_nonce()
        if additional_fields is None:
            additional_fields = {}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url=self._get_url(route, **kwargs),
                    json=self._get_data(additional_fields),
                )
                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as exc:
                raise FrekassaException(status_code=exc.response.status_code, text=exc.response.json())

            except httpx.RequestError as exc:
                raise RuntimeError(f"Server or Network error {exc}")

    def _get_signature(self, data: Dict[str, Any]) -> str:
        cdata = dict(data)
        if "amount" in cdata:
            amount = cdata["amount"]

            fractional_part = f"{round(amount % 1, 2)}"[1:4] if amount % 1 > 0 else ""
            cdata["amount"] = f"{int(amount)}{fractional_part}"

        msg = "|".join(str(cdata[key]) for key in sorted(cdata))

        hash_object = hmac.new(key=self._api_key.encode(), msg=msg.encode(), digestmod=hashlib.sha256)

        return hash_object.hexdigest()

    async def get_balance(self):
        res = await self._request(self.API_BALANCE_ROUTE)

        return res

    async def create_order(
        self,
        payment_system_id: int,
        email: str,
        ip: str,
        amount: float,
        currency_code: str = "USD",
        payment_id: Optional[str] = None,
        tel: Optional[str] = None,
        success_url: Optional[str] = None,
        failure_url: Optional[str] = None,
        notification_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        additional_fields = {
            "i": payment_system_id,
            "email": email,
            "ip": ip,
            "amount": amount,
            "currency": currency_code,
        }

        if payment_id:
            additional_fields["paymentId"] = payment_id
        if tel:
            additional_fields["tel"] = tel
        if success_url:
            additional_fields["success_url"] = success_url
        if failure_url:
            additional_fields["failure_url"] = failure_url
        if notification_url:
            additional_fields["notification_url"] = notification_url
        res = await self._request(self.API_ORDERS_CREATE_ROUTE, additional_fields=additional_fields)

        return res

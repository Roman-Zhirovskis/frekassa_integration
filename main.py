import asyncio
from collections import OrderedDict
import datetime
import hashlib
import hmac

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
        self._set_nonce()

    def _set_nonce(self):
        self._nonce = int(datetime.datetime.now().timestamp())

    def _get_data(self, additional_fields=dict):
        data = OrderedDict({"shopId": self._shop_id, "nonce": self._nonce})
        data.update(additional_fields)
        data.update({"signature": self._get_signature(data=data)})

        return data

    def _get_url(self, route, **kwargs):
        url = f"{self.API_URL}{route}"
        for key, value in kwargs:
            url = url.replace(f"%{key}%", value)
        return url

    async def _request(self, route, additional_fields=None, **kwargs):
        self._set_nonce()
        if additional_fields is None:
            additional_fields = {}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url=self._get_url(route, **kwargs),
                    json=self._get_data(additional_fields),
                )
                return response.json()
            except httpx.RequestError as exc:
                raise FrekassaException(f"Ошибка при выполнении запроса: {exc}")

    def _get_signature(self, data):
        cdata = dict(data)
        if "amount" in cdata:
            amount = cdata["amount"]
            _ = f"{round(amount % 1, 2)}"[1:4] if amount % 1 > 0 else ""
            cdata["amount"] = f"{int(amount)}{_}"
        msg = "|".join([str(cdata.get(key)) for key in sorted(cdata.keys())])
        hash_object = hmac.new(
            key=self._api_key.encode(), msg=msg.encode(), digestmod=hashlib.sha256
        )
        return hash_object.hexdigest()

    async def get_balance(self):
        res = await self._request(self.API_BALANCE_ROUTE)
        print(res)
        return res

    async def create_order(
        self,
        payment_system_id: int,
        email: str,
        ip: str,
        amount: float,
        currency_code: str = "RUB",
        payment_id: str = None,
        tel: str = None,
        success_url: str = None,
        failure_url: str = None,
        notification_url: str = None,
    ):
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
        res = await self._request(
            self.API_ORDERS_CREATE_ROUTE, additional_fields=additional_fields
        )

        return res


# if __name__ == "__main__":
#     SHOP_ID = ""
#     API_KEY = ""
#     fk = FreeKassa(shop_id=SHOP_ID, api_key=API_KEY)
#     asyncio.run(fk.get_balance())
#     asyncio.run(
#         fk.create_order(
#             email="",
#             ip="",
#             amount=9.9,
#             currency_code="USD",
#             payment_system_id=36,
#         )
#     )

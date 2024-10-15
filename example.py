import asyncio
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, constr
from pydantic_settings import BaseSettings, SettingsConfigDict

from exeptions import FrekassaException
from main import FreeKassa


class FKsettings(BaseSettings):
    API_URL: str = Field(..., alias="API_KEY")
    SHOP_ID: str = Field(..., alias="SHOP_ID")

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


class PaymentOrder(BaseModel):
    payment_system_id: int
    email: EmailStr
    ip: str
    amount: float
    currency_code: str = "USD"  # type: ignore
    payment_id: Optional[str] = None
    tel: Optional[str] = None
    success_url: Optional[HttpUrl] = None
    failure_url: Optional[HttpUrl] = None
    notification_url: Optional[HttpUrl] = None


order = PaymentOrder(
    payment_system_id=36,
    email="test@example.com",
    ip="151.236.25.124",
    amount=9.9,
    tel="+1234567890",
)

if __name__ == "__main__":
    settings = FKsettings()
    fk = FreeKassa(shop_id=settings.SHOP_ID, api_key=settings.API_URL)
    order = PaymentOrder(
        payment_system_id=36,
        email="test@example.com",
        ip="151.236.25.124",
        amount=9.9,
        tel="+1234567890",
    )
    order.model_dump()
    try:
        asyncio.run(
            fk.create_order(
                email="tesslogun@gmail.com",
                ip="151.236.25.124",
                amount=9.9,
                currency_code="USD",
                payment_system_id=36,
            )
        )
    except FrekassaException as e:
        print(f"{e.message}")

    except RuntimeError as e:
        print(str(e))

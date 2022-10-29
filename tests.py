from lava_api.business import LavaBusinessAPI
import os
import random

SECRET_KEY = os.getenv("TEST_SECRET_KEY")
SHOP_ID = os.getenv("TEST_SHOP_ID")


def test_get_signature():
    api = LavaBusinessAPI(SECRET_KEY)
    fields = {
        "orderId": "6555215",
        "sum": 30,
        "shopId": SHOP_ID,
    }
    secret_key = "9de2257f00f5a8ca54b71197cd3b465e7bdfc8b3"

    signature = api.generate_signature(fields)

    assert signature == "d5e0f60d8566c908b58dd60dbf5812e78fc2784828da1a447b24797a220ce0d7"


async def create_test_invoice():
    api = LavaBusinessAPI(SECRET_KEY)
    info = await api.create_invoice(30, f"{random.randint(0, 999999):06d}", SHOP_ID, 120, "some_json_data", "Comment")
    print("Created invoice info:", info)


def test_generate_random_orderid():
    api = LavaBusinessAPI(SECRET_KEY)
    key = api.generate_random_order_id()
    print("Random orderid:", key)


async def main():
    test_get_signature()
    test_generate_random_orderid()
    await create_test_invoice()


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
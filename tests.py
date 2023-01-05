from lava_api.business import LavaBusinessAPI
import os
import random
import json

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

    signature = api.generate_signature(json.dumps(fields))

    print(f"Signature: {signature}")


async def create_test_invoice():
    api = LavaBusinessAPI(SECRET_KEY)
    info = await api.create_invoice(30, SHOP_ID, f"{random.randint(0, 999999):06d}", 120, "some_json_data", "Comment")
    print("Created invoice info:", info)


def test_generate_random_orderid():
    api = LavaBusinessAPI(SECRET_KEY)
    key = api.generate_random_order_id()
    print("Random orderid:", key)


async def test_get_balance():
    api = LavaBusinessAPI(SECRET_KEY)
    balance = await api.get_balance(SHOP_ID)
    print(balance)


async def test_payoff():
    api = LavaBusinessAPI(SECRET_KEY)
    id = await api.payoff(SHOP_ID, 5, "lava", "R10135783")
    print(id)


async def main():
    #test_get_signature()
    #test_generate_random_orderid()
    await create_test_invoice()
    #await test_get_balance()

    #await test_payoff()


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

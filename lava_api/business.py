"""
Python модуль для взаимодействия с Lava Business API
"""
import datetime
import random

import aiohttp
import json
import hmac
import hashlib
from collections import OrderedDict
from dataclasses import dataclass
from typing import List


class CreateInvoiceException(Exception):
    """
    При выставлении счета произошла неизвестная ошибка. Базовый класс для всех ошибок выставления счета
    """
    code: int
    message: str

    def __init__(self, description: str = "Error", message: str = "Error", code: int = -1):
        self.code = code
        self.message = message

        super().__init__(description)


class InvalidResponseException(CreateInvoiceException):
    """
    Не удалось обработать ответ, полученный от сервера.
    """


class InvalidParameterException(CreateInvoiceException):
    """
    Счет с таким айди уже существует.
    """


class InvalidSignatureException(CreateInvoiceException):
    """
    Ошибка при генерации сигнатуры.
    """



@dataclass
class InvoiceInfo:
    invoice_id: str    # айди счета
    amount: float    # сумма
    expired: str    # время, до которого активен счет, в формате YYYY-MM-dd HH:mm:ss
    status: int    # статус
    shop_id: str    # айди магазина, от лица которого был выставлен счет
    merchant_name: str    # название магазина, выставившего счет
    url: str    # URL для оплаты
    comment: str    # комментарий к счету
    include_service: List[str]    # методы оплаты, которые будут доступны пользователю
    exclude_service: List[str]    # методы, которые будут исключены из способов оплаты


class LavaBusinessAPI:
    """
    Отвечает за взаимодействие с Lava Business API
    """

    secret_key: str    # Секретный API ключ

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def generate_signature(self, fields: dict) -> str:
        """
        Генерирует сигнатуру, которая используется для подтверждения аутентификации и валидности пакетов.
        Используются заданные поля, отсортированные в алфавитном порядке по ключу.
        Шифрование происходит по алгоритму SHA256 с использованием секретного ключа.
        Подробнее: https://dev.lava.ru/api-invoice-sign

        :param fields: Словарь, содержащий поля, для которых будет сгенерирована сигнатура. Чаще всего - все поля запроса, за исключением самой сигнатуры.
        :return: Строка-хеш, состоящая из HEX чисел, длиной 64 символа
        """
        odict = OrderedDict(sorted(fields.items()))    # сортировка словаря по ключу

        # separators нужен для приведения выходного JSON к виду, получаемому в PHP. В PHP по умолчанию отсутствуют пробелы после разделителей.
        # Если не убрать пробелы, то строки, используемые при шифровании у клиента и на сервере будут разные, и сигнатуры совпадать не будут
        # json, получаемый в python без указания separators: {"orderId": "6555214", "shopId": "4d499d82-2b99-4a7e-be26-5742c41e69e7"}
        # json, получаемый в python с указанием separators:  {"orderId":"6555214","shopId":"4d499d82-2b99-4a7e-be26-5742c41e69e7"}
        # json, получаемый в php:                            {"orderId":"6555214","shopId":"4d499d82-2b99-4a7e-be26-5742c41e69e7"}
        msg = json.dumps(odict, separators=(',', ':'))
        digest = hmac.new(self.secret_key.encode("utf-8"), msg=msg.encode("utf-8"),
                          digestmod=hashlib.sha256)
        signature = digest.hexdigest()
        return signature

    @staticmethod
    def generate_random_order_id() -> str:
        """
        Генерирует уникальный айди счета используя текущее время и два случайных числа

        :return:
        """
        now = datetime.datetime.now()
        order_id = f"{now.strftime('%Y%m%d')}-{random.randint(0, 9999):04d}-{now.strftime('%H%M%S')}-{random.randint(0, 9999):04d}"
        return order_id

    async def create_invoice(self,
                             amount: float,
                             shop_id: str,
                             order_id: str = None,
                             expire: int = None,
                             custom_field: str = None,
                             comment: str = None,
                             webhook_url: str = None,
                             fail_url: str = None,
                             success_url: str = None,
                             include_service: List[str] = None,
                             exclude_service: List[str] = None
                             ) -> InvoiceInfo:
        """
        Выставляет счет с задаными параметрами (см. https://dev.lava.ru/api-invoice-create).

        :param amount: Сумма
        :param order_id: Айди счета (должен быть уникальным). Если не указан, то будет сгенерирован автоматически.
        :param shop_id: Айди магазина
        :param expire: Время жизни счета в минутах
        :param custom_field: Дополнительная информация, которая будет передана в Webhook после оплаты
        :param comment: Комментарий к платежу
        :param webhook_url: URL, на который будет отправлено уведомление об оплате (см. https://dev.lava.ru/business-webhook)
        :param fail_url: URL для переадресации после неудачной оплаты
        :param success_url: URL для переадресации после успешной оплаты
        :param include_service: Если указаны, то будут отображены только эти методы оплаты
        :param exclude_service: Если указаны, то эти методы будут исключены из списка доступных

        :return: Информация о выставленном счете
        """
        # если айди счета не указан, то генерируем случайный
        if order_id is None:
            order_id = self.generate_random_order_id()

        fields = {"orderId": order_id, "shopId": shop_id, "sum": amount}

        # если необязательные параметры указаны, то добавляем их к запросу
        if custom_field is not None:
            fields["customFields"] = custom_field
        if comment is not None:
            fields["comment"] = comment
        if webhook_url is not None:
            fields["hookUrl"] = webhook_url
        if fail_url is not None:
            fields["failUrl"] = fail_url
        if success_url is not None:
            fields["successUrl"] = success_url
        if expire is not None:
            fields["expire"] = expire
        if include_service is not None:
            fields["includeService"] = include_service
        if exclude_service is not None:
            fields["excludeService"] = exclude_service

        fields["signature"] = self.generate_signature(fields)

        async with aiohttp.ClientSession() as session:
            # заголовок Accept необходимо передавать со всеми запросами. Content-Type добавляется автоматически (см. https://dev.lava.ru/info)
            async with session.post('https://api.lava.ru/business/invoice/create', json=fields, headers={"Accept": "application/json"}) as response:
                try:
                    response_json = await response.json()

                    if (request_status := response_json.get("status", 0)) == 200:
                        invoice_data: dict = response_json.get("data", None)

                        if invoice_data is None:
                            print("Error while handling server response: ")
                            raise InvalidResponseException("No 'data' field")
                        try:
                            return InvoiceInfo(
                                invoice_data["id"],
                                invoice_data["amount"],
                                invoice_data["expired"],
                                invoice_data["status"],
                                invoice_data["shop_id"],
                                invoice_data.get("merchantName", "Merchant"),
                                invoice_data["url"],
                                invoice_data.get("comment", "Comment"),
                                include_service if (include_service := invoice_data.get("include_service", None)) is not None else [],
                                exclude_service if (exclude_service := invoice_data.get("exclude_service", None)) is not None else [],
                            )
                        except KeyError as ex:
                            print("Error while reading data from dictionary: ")
                            print(ex)
                            raise InvalidResponseException("Error while reading data from dictionary")

                    elif request_status == 422:
                        if isinstance((error := response_json.get('error', '')), dict):
                            raise InvalidParameterException(f"Invalid parameters: {', '.join(error.keys())}; Code: {request_status}; Message: {response_json.get('error', '')}", response_json.get('error', ''), request_status)
                        else:
                            print("Error while reading data from dictionary: ")
                            raise InvalidResponseException(f"Invalid 'error' field: {response_json.get('error', '')}", response_json.get('error', ''), request_status)
                    elif request_status == 401:
                        raise InvalidSignatureException(f"Invalid signature. Code: {request_status}; Message: {response_json.get('error', '')}", response_json.get('error', ''), request_status)
                    else:
                        raise CreateInvoiceException(f"Unexpected error. Code: {request_status}; Message: {response_json.get('error', '')}", response_json.get('error', ''), request_status)

                except (InvalidParameterException, InvalidSignatureException, CreateInvoiceException) as ex:
                    raise ex
                except Exception as ex:
                    print("Error while handling server response: ")
                    print(ex)
                    raise InvalidResponseException


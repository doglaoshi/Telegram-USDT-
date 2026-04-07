import json
import requests
import time

import pika
from pika import exceptions

import tronpy.exceptions
from tronpy.providers import HTTPProvider
from tronpy import Tron


credentials = pika.PlainCredentials('heijiang', 'heijiang')  # MQ账号和密码
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='',  # IP地址
    port=5672,  # 端口
    virtual_host='/',  # 虚拟主机
    credentials=credentials  # 登录凭证
))
channel = connection.channel()
apikey = [""]
client = Tron(HTTPProvider(api_key=apikey))


def get_data(block) -> None:
    """
    获取对应区块的交易信息
    :return: None
    """
    while True:
        try:
            block_list = client.get_block(block)
            if 'transactions' in block_list.keys():
                break
            else:
                return
        except tronpy.exceptions.BlockNotFound:
            time.sleep(1)
        except requests.exceptions as e:
            print(e)
    rabbitmq_connection(block_list, block)


def rabbitmq_connection(block_list, block):
    try:
        queue_name = 'heijiang'
        # 创建队列
        channel.queue_declare(queue=queue_name, durable=True)

        message_data = {
            "block_list": block_list,
        }
        # 将 Python 对象转换为 JSON 字符串
        message_json = json.dumps(message_data)
        message_bytes = message_json.encode()

        channel.basic_publish(exchange='', routing_key=queue_name, body=message_bytes)

        # 记录成功推送消息的日志
        print(f"Successfully sent data to RabbitMQ: blockNum: {block}")
    except pika.exceptions as e:
        print(e)


if __name__ == '__main__':
    # 获取最新的区块
    block = client.get_latest_block()['block_header']['raw_data']['number'] - 1
    while True:
        get_data(block)
        block += 1

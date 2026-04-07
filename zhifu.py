import json
import requests
import time
from pika.exceptions import AMQPError, ChannelClosedByBroker
import pika
from pika import exceptions

import tronpy.exceptions
from tronpy.providers import HTTPProvider
from tronpy import Tron
import pymongo
from pymongo.collection import Collection

teleclient = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
teleclient["admin"].authenticate("admin", "xxxx", mechanism='SCRAM-SHA-1')
mydb = teleclient['qukuailian']  # pyright: ignore[reportUndefinedVariable]
qukuai = mydb['qukuai']

mydb1 = teleclient['xxxx']#机器人用户名
shangtext = mydb1['shangtext']

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


def send_message_to_queue(message_data):
    try:
        # 发送消息到另一个队列
        message_json = json.dumps(message_data)  # 将字典转换为JSON字符串
        channel.basic_publish(exchange='', routing_key='tronweb_data', body=message_json)  # 发送消息
        print(f"Successfully sent data to RabbitMQ: {message_data}")
    except (AMQPError, ChannelClosedByBroker) as e:
        print(f"Failed to send data to RabbitMQ: {e}")


def search_address():
    dz1 = shangtext.find_one({'projectname': '充值地址'})['text']
    address = [dz1]

    return address


def callback(ch, method, properties, body) -> None:
    try:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        text = body.decode('utf-8')
        block_list = json.loads(text)
        block_list = block_list['block_list']
        transactions = block_list['transactions']
        number = block_list['block_header']['raw_data']['number']
        address_list = search_address()
        print(f"Data received successfully from RabbitMQ: blockNum: {number}")
        for trx in transactions:
            # "SUCCESS"表示交易成功，"OUT_OF_ENERGY"表示交易失败能量不足
            if trx["ret"][0]["contractRet"] == "SUCCESS":
                contract = trx["raw_data"]["contract"][0]
                contract_type = contract["type"]
                value = contract["parameter"]["value"]
                # 交易哈希
                txid = trx['txID']
                # 合约类型为智能合约
                if contract_type == "TriggerSmartContract":
                    contract_address = client.to_base58check_address(value["contract_address"])
                    data = value['data']
                    # 合约地址为USDT
                    if contract_address == 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t':
                        # 交易类型为USDT
                        transfer_type = 'USDT'

                        if data[:8] == "a9059cbb":
                            # 发起地址
                            from_address = client.to_base58check_address(value["owner_address"])
                            # 接收地址
                            to_address = client.to_base58check_address('41' + (data[8:72])[-40:])
                            # 交易金额，实际金额需要/1000000
                            quant = (int(data[-64:], 16))
                            if quant == 0:
                                continue
                            try:
                                # 获取该次交易的时间戳
                                timestamp = trx["raw_data"]["timestamp"]
                            except KeyError:
                                timestamp = int(round(time.time() * 1000))
                            message_data = {
                                "txid": txid,
                                "type": transfer_type,
                                "from_address": from_address,
                                "to_address": to_address,
                                "quant": quant,
                                "time": timestamp,
                                "number": number,
                                'state': 0
                            }
                            if message_data['to_address'] in address_list:
                                # send_message_to_queue(message_data)  # 发送消息到另一个队列
                                qukuai.insert_one(message_data)
                                print(f"Successfully pushed trading information to RabbitMQ: {transfer_type}")

    except (AMQPError, ChannelClosedByBroker) as e:
        print(f"Failed to receive data from RabbitMQ: {e}")


if __name__ == '__main__':
    # 启动消费者线程
    channel.basic_consume('heijiang', callback)
    channel.start_consuming()

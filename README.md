# Fakabot 发卡机器人使用说明
# 狗老师（@goulaoshi）
这是一个基于 Telegram 的**发卡机器人**，主要用于卖号与自主发卡。核心能力包含：

- 商品分类管理（一级/二级分类）
- 商品上架与库存管理（号包、协议号等）
- 用户下单购买后自动发货（自主发卡）
- 订单记录、用户记录、基础后台管理
- USDT 余额体系（含充值监听，可选开启）
- 自主后台上货可对接api自动更新

---


---

## 二、运行环境要求

- Python 3.10+（你当前 3.11 可用）
- MongoDB（本地默认 `127.0.0.1:27017`）
- RabbitMQ（用于区块监听数据流转）

---

## 三、安装依赖

项目里没有 `requirements.txt`，可以先手动安装当前代码用到的主要库：

```bash
pip3 install python-telegram-bot==13.15 pymongo pika tronpy pygtrans qrcode requests
```

> 说明：`bot.py` 使用的是 `python-telegram-bot` v13 风格 API（`Updater`、`Filters`），建议按上面版本安装。

---

## 四、启动前必须改的配置

请按下面文件逐项修改：

1. `bot.py`
   - 把 `Updater(token='token', ...)` 里的 `token` 改成你自己的机器人 Token

2. `mongo.py`
   - Mongo 连接与认证信息（账号/密码/数据库名）
   - 默认数据库集合初始化逻辑

3. `qukuai.py`
   - RabbitMQ 连接参数：`host`、账号密码等
   - TRON API Key（`apikey`）

4. `zhifu.py`
   - Mongo 连接与认证信息
   - RabbitMQ 连接参数
   - 充值地址来源（数据库中 `充值地址` 字段）

---

## 五、推荐启动顺序（发卡机器人）

### 1) 先启动机器人主程序<img width="470" height="876" alt="截屏2026-04-07 15 40 59" src="https://github.com/user-attachments/assets/9ddf6abd-5fa1-48ee-9e5a-ef07adc4ef73" />

<img width="470" height="876" alt="截屏2026-04-07 15 40 59" src="https://github.com/user-attachments/assets/5f4bb299-bb62-4c86-b20c-27794ce52238" />



```bash
python3 bot.py
```

### 2) 如需开启 USDT 充值监听，再启动这两个进程（可选）

终端 A（抓取区块并推送到 MQ）：

```bash
python3 qukuai.py
```

终端 B（消费 MQ 数据并入库）：

```bash
python3 zhifu.py
```

---

## 六、常见问题

- **Q：为什么 `python3 main.py` 报文件不存在？**  
  A：这个项目没有 `main.py`，入口是 `bot.py`。

- **Q：机器人启动后没反应？**  
  A：优先检查三项：`bot token`、Mongo 连接、是否已正确安装 `python-telegram-bot==13.15`。

- **Q：发卡相关功能在哪些代码里？**  
  A：主流程在 `bot.py`，数据库与集合定义在 `mongo.py`。发卡、分类、商品、订单等管理逻辑都在 `bot.py` 的回调和消息处理里。

- **Q：充值监听没数据？**  
  A：检查 RabbitMQ 参数、TRON API Key，以及数据库里 `充值地址` 是否正确。

---

## 七、最小可用启动（只跑发卡）

当你只想先运行卖号/发卡主功能，不开链上充值监听时，只需要：

```bash
python3 bot.py
```

即可。


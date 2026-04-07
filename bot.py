import asyncio
import datetime, qrcode, socket, struct, threading, hashlib, uuid
import telegram
import logging, os, shutil
from multiprocessing import Process
from telegram.ext import handler
from telegram.utils import helpers  # pyright: ignore[reportMissingImports]
from mongo import *
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler, \
    InlineQueryHandler
from telegram import InlineKeyboardMarkup, ForceReply, InlineKeyboardButton, Update, ChatMemberRestricted, \
    ChatPermissions, \
    ChatMemberRestricted, ChatMember, ChatMemberAdministrator, KeyboardButton, ReplyKeyboardMarkup, \
    InlineQueryResultArticle, InputTextMessageContent, InputMediaPhoto
import time, json, pickle, re
from threading import Timer
from decimal import Decimal
import zipfile
from pygtrans import Translate

import qukuai


def make_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Folder '{path}' created successfully")
    else:
        print(f"Folder '{path}' already exists")


def rename_directory(old_path, new_path):
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        print(f"Folder '{old_path}' renamed to '{new_path}'")
    else:
        print(f"Folder '{old_path}' does not exist")


def get_fy(fstext):
    fy_list = fyb.find_one({'text': fstext})
    if fy_list is None:
        client = Translate(target='en', domain='com')
        trans_text = client.translate(fstext.replace("\n", "\\n")).translatedText
        fanyibao('英文', fstext, trans_text.replace("\\n", "\n"))
        return trans_text.replace("\\n", "\n")
    else:
        fanyi = fy_list['fanyi']

        return fanyi


def inline_query(update: Update, context: CallbackContext):
    """Handle the inline query. This is run when you type: @botusername <query>"""
    query = update.inline_query.query
    if not query:  # empty query should not be handled

        hyy = shangtext.find_one({'projectname': '欢迎语'})['text']
        hyyys = shangtext.find_one({'projectname': '欢迎语样式'})['text']

        entities = pickle.loads(hyyys)

        keyboard = [[InlineKeyboardButton(context.bot.first_name, url=f'https://t.me/{context.bot.username}')]]
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                reply_markup=InlineKeyboardMarkup(keyboard),
                title=context.bot.first_name,
                input_message_content=InputTextMessageContent(
                    hyy, entities=entities
                )
            ),
        ]

        update.inline_query.answer(results=results, cache_time=0)
        return

    yh_list = update['inline_query']['from_user']
    user_id = yh_list['id']
    fullname = yh_list['full_name']

    if is_number(query):
        money = query
        money = float(money) if str(money).count('.') > 0 else int(money)
        user_list = user.find_one({'user_id': user_id})
        USDT = user_list['USDT']
        if USDT >= money:
            if money <= 0:
                url = helpers.create_deep_linked_url(context.bot.username, str(user_id))
                keyboard = [
                    [InlineKeyboardButton(context.bot.first_name, url=url)]
                ]
                fstext = f'''
⚠️操作失败，转账金额必须大于0
                '''

                hyy = shangtext.find_one({'projectname': '欢迎语'})['text']
                hyyys = shangtext.find_one({'projectname': '欢迎语样式'})['text']

                entities = pickle.loads(hyyys)

                results = [
                    InlineQueryResultArticle(
                        id=str(uuid.uuid4()),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        title=fstext,
                        input_message_content=InputTextMessageContent(
                            hyy, entities=entities
                        )
                    ),
                ]

                update.inline_query.answer(results=results, cache_time=0)
                return
            uid = generate_24bit_uid()
            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            zhuanz.insert_one({
                'uid': uid,
                'user_id': user_id,
                'fullname': fullname,
                'money': money,
                'timer': timer,
                'state': 0
            })
            # keyboard = [[InlineKeyboardButton("📥收款", callback_data=f'shokuan {user_id}:{money}')]]
            keyboard = [[InlineKeyboardButton("📥收款", callback_data=f'shokuan {uid}')]]
            fstext = f'''
转账 {query} U
            '''

            zztext = f'''
<b>转账给你 {query} U</b>

请在24小时内领取
            '''
            results = [
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    title=fstext,
                    description='⚠️您正在向对方转账U并立即生效',
                    input_message_content=InputTextMessageContent(
                        zztext, parse_mode='HTML'
                    )
                ),
            ]

            update.inline_query.answer(results=results, cache_time=0)
            return
        else:
            url = helpers.create_deep_linked_url(context.bot.username, str(user_id))
            keyboard = [
                [InlineKeyboardButton(context.bot.first_name, url=url)]
            ]
            fstext = f'''
⚠️操作失败，余额不足，💰当前余额：{USDT}U
            '''

            hyy = shangtext.find_one({'projectname': '欢迎语'})['text']
            hyyys = shangtext.find_one({'projectname': '欢迎语样式'})['text']

            entities = pickle.loads(hyyys)

            results = [
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    title=fstext,
                    input_message_content=InputTextMessageContent(
                        hyy, entities=entities
                    )
                ),
            ]

            update.inline_query.answer(results=results, cache_time=0)
            return
    uid = query.replace('redpacket ', '')
    hongbao_list = hongbao.find_one({'uid': uid})
    if hongbao_list is None:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="参数错误",
                input_message_content=InputTextMessageContent(
                    f"<b>错误</b>", parse_mode='HTML'
                )),
        ]

        update.inline_query.answer(results=results, cache_time=0)
        return
    yh_id = hongbao_list['user_id']
    if yh_id != user_id:

        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🧧这不是你的红包",
                input_message_content=InputTextMessageContent(
                    f"<b>🧧这不是你的红包</b>", parse_mode='HTML'
                )),
        ]

        update.inline_query.answer(results=results, cache_time=0)
    else:
        hbmoney = hongbao_list['hbmoney']
        hbsl = hongbao_list['hbsl']
        state = hongbao_list['state']
        if state == 1:
            results = [
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="🧧红包已领取完",
                    input_message_content=InputTextMessageContent(
                        f"<b>🧧红包已领取完</b>", parse_mode='HTML'
                    )),
            ]

            update.inline_query.answer(results=results, cache_time=0)
        else:
            qbrtext = []
            jiangpai = {'0': '🥇', '1': '🥈', '2': '🥉'}
            count = 0
            qb_list = list(qb.find({'uid': uid}, sort=[('money', -1)]))
            for i in qb_list:
                qbid = i['user_id']
                qbname = i['fullname'].replace('<', '').replace('>', '')
                qbtimer = i['timer'][-8:]
                qbmoney = i['money']
                if str(count) in jiangpai.keys():

                    qbrtext.append(
                        f'{jiangpai[str(count)]} <code>{qbmoney}</code>({qbtimer}) USDT💰 - <a href="tg://user?id={qbid}">{qbname}</a>')
                else:
                    qbrtext.append(
                        f'<code>{qbmoney}</code>({qbtimer}) USDT💰 - <a href="tg://user?id={qbid}">{qbname}</a>')
                count += 1
            qbrtext = '\n'.join(qbrtext)

            syhb = hbsl - len(qb_list)

            fstext = f'''
🧧 <a href="tg://user?id={user_id}">{fullname}</a> 发送了一个红包
💵总金额:{hbmoney} USDT💰 剩余:{syhb}/{hbsl}

{qbrtext}
            '''

            url = helpers.create_deep_linked_url(context.bot.username, str(user_id))
            keyboard = [
                [InlineKeyboardButton('领取红包', callback_data=f'lqhb {uid}')],
                [InlineKeyboardButton(context.bot.first_name, url=url)]
            ]

            results = [
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    title=f"💵总金额:{hbmoney} USDT💰 剩余:{syhb}/{hbsl}",
                    input_message_content=InputTextMessageContent(
                        fstext, parse_mode='HTML'
                    )
                ),
            ]

            update.inline_query.answer(results=results, cache_time=0)


def shokuan(update: Update, context: CallbackContext):
    query = update.callback_query
    # data = query.data.replace('shokuan ','')
    uid = query.data.replace('shokuan ', '')

    # fb_id = int(data.split(':')[0])
    # fb_money = data.split(':')[1]
    # fb_money = float(fb_money) if str((fb_money)).count('.') > 0 else int(standard_num(fb_money))
    fb_list = zhuanz.find_one({'uid': uid})
    fb_state = fb_list['state']
    if fb_state == 1:
        fstext = f'''
❌ 领取失败
        '''
        query.answer(fstext, show_alert=bool("true"))
        return
    fb_id = fb_list['user_id']
    fb_money = fb_list['money']
    yh_list = user.find_one({'user_id': fb_id})
    yh_usdt = yh_list['USDT']
    if yh_usdt < fb_money:
        fstext = f'''
❌ 领取失败.USDT 操作失败，余额不足
        '''
        zhuanz.update_one({'uid': uid}, {"$set": {"state": 1}})
        query.answer(fstext, show_alert=bool("true"))
        return

    now_money = standard_num(yh_usdt - fb_money)
    now_money = float(now_money) if str((now_money)).count('.') > 0 else int(standard_num(now_money))
    user.update_one({'user_id': fb_id}, {"$set": {'USDT': now_money}})

    zhuanz.update_one({'uid': uid}, {"$set": {"state": 1}})
    user_id = query.from_user.id
    username = query.from_user.username
    fullname = query.from_user.full_name.replace('<', '').replace('>', '')
    lastname = query.from_user.last_name
    timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    if user.find_one({'user_id': user_id}) is None:
        try:
            key_id = user.find_one({}, sort=[('count_id', -1)])['count_id']
        except:
            key_id = 0
        try:
            key_id += 1
            user_data(key_id, user_id, username, fullname, lastname, str(1), creation_time=timer,
                      last_contact_time=timer)
        except:
            for i in range(100):
                try:
                    key_id += 1
                    user_data(key_id, user_id, username, fullname, lastname, str(1), creation_time=timer,
                              last_contact_time=timer)
                    break
                except:
                    continue
    elif user.find_one({'user_id': user_id})['username'] != username:
        user.update_one({'user_id': user_id}, {'$set': {'username': username}})

    elif user.find_one({'user_id': user_id})['fullname'] != fullname:
        user.update_one({'user_id': user_id}, {'$set': {'fullname': fullname}})

    user_list = user.find_one({"user_id": user_id})
    USDT = user_list['USDT']

    now_money = standard_num(USDT + fb_money)
    now_money = float(now_money) if str((now_money)).count('.') > 0 else int(standard_num(now_money))
    user.update_one({'user_id': user_id}, {"$set": {'USDT': now_money}})
    fstext = f'''
<a href="tg://user?id={user_id}">{fullname}</a> 已领取 <b>{fb_money}</b> USDT
    '''
    url = helpers.create_deep_linked_url(context.bot.username, str(user_id))
    keyboard = [[InlineKeyboardButton(f"{context.bot.first_name}", url=url)]]
    try:
        query.edit_message_text(fstext, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        pass


def lqhb(update: Update, context: CallbackContext):
    query = update.callback_query
    uid = query.data.replace('lqhb ', '')
    user_id = query.from_user.id
    username = query.from_user.username
    fullname = query.from_user.full_name.replace('<', '').replace('>', '')
    lastname = query.from_user.last_name
    timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    if user.find_one({'user_id': user_id}) is None:
        try:
            key_id = user.find_one({}, sort=[('count_id', -1)])['count_id']
        except:
            key_id = 0
        try:
            key_id += 1
            user_data(key_id, user_id, username, fullname, lastname, str(1), creation_time=timer,
                      last_contact_time=timer)
        except:
            for i in range(100):
                try:
                    key_id += 1
                    user_data(key_id, user_id, username, fullname, lastname, str(1), creation_time=timer,
                              last_contact_time=timer)
                    break
                except:
                    continue
    elif user.find_one({'user_id': user_id})['username'] != username:
        user.update_one({'user_id': user_id}, {'$set': {'username': username}})

    elif user.find_one({'user_id': user_id})['fullname'] != fullname:
        user.update_one({'user_id': user_id}, {'$set': {'fullname': fullname}})

    user_list = user.find_one({"user_id": user_id})
    USDT = user_list['USDT']

    hongbao_list = hongbao.find_one({'uid': uid})
    fb_id = hongbao_list['user_id']
    fb_fullname = hongbao_list['fullname']
    hbmoney = hongbao_list['hbmoney']
    hbsl = hongbao_list['hbsl']
    state = hongbao_list['state']
    if state == 1:
        query.answer('红包已抢完', show_alert=bool("true"))
        return

    qhb_list = qb.find_one({"uid": uid, 'user_id': user_id})
    if qhb_list is not None:
        query.answer('你已领取该红包', show_alert=bool("true"))
        return
    qb_list = list(qb.find({'uid': uid}, sort=[('money', -1)]))

    syhb = hbsl - len(qb_list)
    # 以下是随机分配金额的代码
    remaining_money = hbmoney - sum(q['money'] for q in qb_list)  # 计算剩余红包总额
    if syhb > 1:
        # 多于一个红包剩余时，使用正态分布随机生成金额
        mean_money = remaining_money / syhb  # 计算每个红包的平均金额
        std_dev = mean_money / 3  # 标准差设定为平均金额的1/3
        money = standard_num(max(0.01, round(random.normalvariate(mean_money, std_dev), 2)))  # 使用正态分布生成金额，并保留两位小数
        money = float(money) if str(money).count('.') > 0 else int(money)
    else:
        # 如果只有一个红包剩余，直接将剩余金额分配给该红包
        money = round(remaining_money, 2)  # 将剩余金额保留两位小数
        money = float(money) if str(money).count('.') > 0 else int(money)

    # 将金额保存到数据库
    qb.insert_one({
        'uid': uid,
        'user_id': user_id,
        'fullname': fullname,
        'money': money,
        'timer': timer
    })

    user_money = standard_num(USDT + money)
    user_money = float(user_money) if str(user_money).count('.') > 0 else int(user_money)
    user.update_one({'user_id': user_id}, {"$set": {'USDT': user_money}})

    query.answer(f'领取红包成功，金额:{money}', show_alert=bool("true"))

    jiangpai = {'0': '🥇', '1': '🥈', '2': '🥉'}

    qb_list = list(qb.find({'uid': uid}, sort=[('money', -1)]))

    syhb = hbsl - len(qb_list)
    qbrtext = []
    count = 0
    for i in qb_list:
        qbid = i['user_id']
        qbname = i['fullname'].replace('<', '').replace('>', '')
        qbtimer = i['timer'][-8:]
        qbmoney = i['money']
        if str(count) in jiangpai.keys():

            qbrtext.append(
                f'{jiangpai[str(count)]} <code>{qbmoney}</code>({qbtimer}) USDT💰 - <a href="tg://user?id={qbid}">{qbname}</a>')
        else:
            qbrtext.append(f'<code>{qbmoney}</code>({qbtimer}) USDT💰 - <a href="tg://user?id={qbid}">{qbname}</a>')
        count += 1
    qbrtext = '\n'.join(qbrtext)

    fstext = f'''
🧧 <a href="tg://user?id={fb_id}">{fb_fullname}</a> 发送了一个红包
💵总金额:{hbmoney} USDT💰 剩余:{syhb}/{hbsl}

{qbrtext}
    '''
    if syhb == 0:
        url = helpers.create_deep_linked_url(context.bot.username, str(user_id))
        keyboard = [
            [InlineKeyboardButton(context.bot.first_name, url=url)]
        ]
        hongbao.update_one({'uid': uid}, {"$set": {'state': 1}})
    else:
        url = helpers.create_deep_linked_url(context.bot.username, str(user_id))
        keyboard = [
            [InlineKeyboardButton('领取红包', callback_data=f'lqhb {uid}')],
            [InlineKeyboardButton(context.bot.first_name, url=url)]
        ]
    try:
        query.edit_message_text(text=fstext, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    except:
        pass


def xzhb(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    uid = query.data.replace('xzhb ', '')
    hongbao_list = hongbao.find_one({'uid': uid})
    fb_id = hongbao_list['user_id']
    fb_fullname = hongbao_list['fullname']
    state = hongbao_list['state']
    hbmoney = hongbao_list['hbmoney']
    hbsl = hongbao_list['hbsl']
    timer = hongbao_list['timer']
    jiangpai = {'0': '🥇', '1': '🥈', '2': '🥉'}
    if state == 0:

        qb_list = list(qb.find({'uid': uid}, sort=[('money', -1)]))

        syhb = hbsl - len(qb_list)

        qbrtext = []
        count = 0
        for i in qb_list:
            qbid = i['user_id']
            qbname = i['fullname'].replace('<', '').replace('>', '')
            qbtimer = i['timer'][-8:]
            qbmoney = i['money']
            if str(count) in jiangpai.keys():

                qbrtext.append(
                    f'{jiangpai[str(count)]} <code>{qbmoney}</code>({qbtimer}) USDT💰 - <a href="tg://user?id={qbid}">{qbname}</a>')
            else:
                qbrtext.append(f'<code>{qbmoney}</code>({qbtimer}) USDT💰 - <a href="tg://user?id={qbid}">{qbname}</a>')
            count += 1
        qbrtext = '\n'.join(qbrtext)

        fstext = f'''
🧧 <a href="tg://user?id={fb_id}">{fb_fullname}</a> 发送了一个红包
🕦 时间:{timer}
💵 总金额:{hbmoney} USDT
状态:进行中
剩余:{syhb}/{hbsl}

{qbrtext}
        '''
        keyboard = [[InlineKeyboardButton('发送红包', switch_inline_query=f'redpacket {uid}')],
                    [InlineKeyboardButton('⭕️关闭', callback_data=f'close {user_id}')]]
        context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML',
                                 reply_markup=InlineKeyboardMarkup(keyboard))
    else:

        qb_list = list(qb.find({'uid': uid}, sort=[('money', -1)]))

        qbrtext = []
        count = 0
        for i in qb_list:
            qbid = i['user_id']
            qbname = i['fullname'].replace('<', '').replace('>', '')
            qbtimer = i['timer'][-8:]
            qbmoney = i['money']
            if str(count) in jiangpai.keys():

                qbrtext.append(
                    f'{jiangpai[str(count)]} <code>{qbmoney}</code>({qbtimer}) USDT💰 - <a href="tg://user?id={qbid}">{qbname}</a>')
            else:
                qbrtext.append(f'<code>{qbmoney}</code>({qbtimer}) USDT💰 - <a href="tg://user?id={qbid}">{qbname}</a>')
            count += 1
        qbrtext = '\n'.join(qbrtext)

        fstext = f'''
🧧 <a href="tg://user?id={fb_id}">{fb_fullname}</a> 发送了一个红包
🕦 时间:{timer}
💵 总金额:{hbmoney} USDT
状态:已结束
剩余:0/{hbsl}

{qbrtext}
        '''

        keyboard = [[InlineKeyboardButton('⭕️关闭', callback_data=f'close {user_id}')]]
        context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML',
                                 reply_markup=InlineKeyboardMarkup(keyboard))


def jxzhb(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    keyboard = [
        [InlineKeyboardButton('◾️进行中', callback_data='jxzhb'),
         InlineKeyboardButton('已结束', callback_data='yjshb')],

    ]

    for i in list(hongbao.find({'user_id': user_id, 'state': 0})):
        timer = i['timer'][-14:-3]
        hbsl = i['hbsl']
        uid = i['uid']
        qb_list = list(qb.find({'uid': uid}, sort=[('money', -1)]))
        syhb = hbsl - len(qb_list)
        hbmoney = i['hbmoney']
        keyboard.append(
            [InlineKeyboardButton(f'🧧[{timer}] {syhb}/{hbsl} - {hbmoney} USDT', callback_data=f'xzhb {uid}')])

    keyboard.append([InlineKeyboardButton('➕添加', callback_data='addhb')])
    keyboard.append([InlineKeyboardButton('关闭', callback_data=f'close {user_id}')])

    query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


def yjshb(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    keyboard = [
        [InlineKeyboardButton('️进行中', callback_data='jxzhb'),
         InlineKeyboardButton('◾已结束', callback_data='yjshb')],

    ]

    for i in list(hongbao.find({'user_id': user_id, 'state': 1})):
        timer = i['timer'][-14:-3]
        hbsl = i['hbsl']
        uid = i['uid']
        hbmoney = i['hbmoney']
        keyboard.append(
            [InlineKeyboardButton(f'🧧[{timer}] 0/{hbsl} - {hbmoney} USDT (over)', callback_data=f'xzhb {uid}')])

    keyboard.append([InlineKeyboardButton('➕添加', callback_data='addhb')])
    keyboard.append([InlineKeyboardButton('关闭', callback_data=f'close {user_id}')])

    query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


def addhb(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    fstext = f'''
💡 请回复你要发送的总金额()? 例如: <code>8.88</code>
    '''
    keyboard = [[InlineKeyboardButton('🚫取消', callback_data=f'close {user_id}')]]
    user.update_one({'user_id': user_id}, {"$set": {'sign': 'addhb'}})
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard),
                             parse_mode='HTML')


def start(update: Update, context: CallbackContext):
    us = update.effective_user
    chat_id = update.effective_chat.id
    user_id = us.id
    username = us.username
    fullname = us.full_name.replace('<', '').replace('>', '')
    lastname = us.last_name
    botusername = context.bot.username
    timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    if user.find_one({'user_id': user_id}) is None:
        try:
            key_id = user.find_one({}, sort=[('count_id', -1)])['count_id']
        except:
            key_id = 0
        try:
            key_id += 1
            user_data(key_id, user_id, username, fullname, lastname, str(1), creation_time=timer,
                      last_contact_time=timer)
        except:
            for i in range(100):
                try:
                    key_id += 1
                    user_data(key_id, user_id, username, fullname, lastname, str(1), creation_time=timer,
                              last_contact_time=timer)
                    break
                except:
                    continue
    elif user.find_one({'user_id': user_id})['username'] != username:
        user.update_one({'user_id': user_id}, {'$set': {'username': username}})

    elif user.find_one({'user_id': user_id})['fullname'] != fullname:
        user.update_one({'user_id': user_id}, {'$set': {'fullname': fullname}})
    for i in ['xxxx']:
        if username == i:
            user.update_one({'username': i}, {'$set': {'state': '4'}})
    user_list = user.find_one({"user_id": user_id})
    state = user_list['state']
    sign = user_list['sign']
    USDT = user_list['USDT']
    zgje = user_list['zgje']
    lang = user_list['lang']
    zgsl = user_list['zgsl']
    creation_time = user_list['creation_time']
    args = update.message.text.split(maxsplit=2)
    content = args[2] if len(args) == 3 else ""
    if len(args) == 2:
        if username is None:
            username = fullname
        else:
            username = f'<a href="https://t.me/{username}">{username}</a>'
        fstext = f'''
<b>您的ID:</b>  <code>{user_id}</code>
<b>您的用户名:</b>  {username} 
<b>注册日期:</b>  {creation_time}

<b>总购数量:</b>  {zgsl}

<b>总购金额:</b>  {standard_num(zgje)} USDT

<b>您的余额:</b>  {USDT} USDT
        '''

        keyboard = [[InlineKeyboardButton('🛒购买记录', callback_data=f'gmaijilu {user_id}')],
                    [InlineKeyboardButton('关闭', callback_data=f'close {user_id}')]]
        context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML',
                                 reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
        return

    hyy = shangtext.find_one({'projectname': '欢迎语'})['text']
    keylist = get_key.find({}, sort=[('Row', 1), ('first', 1)])
    yyzt = shangtext.find_one({'projectname': '营业状态'})['text']
    if yyzt == 0:
        if state != '4':
            return
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for i in keylist:
        projectname = i['projectname']
        if projectname == '中文服务':
            pass
        else:
            projectname = projectname if lang == 'zh' else get_fy(projectname)
        row = i['Row']
        first = i['first']
        keyboard[i["Row"] - 1].append(KeyboardButton(projectname))

    hyy = hyy if lang == 'zh' else get_fy(hyy)
    context.bot.send_message(chat_id=user_id, text=hyy, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True,
                                                                                         one_time_keyboard=False))
    if state == '4':
        keyboard = [
            [InlineKeyboardButton('用户列表', callback_data='yhlist'),
             InlineKeyboardButton('对话用户私发', callback_data='sifa')],
            [InlineKeyboardButton('充值地址设置', callback_data='settrc20'),
             InlineKeyboardButton('商品管理', callback_data='spgli')],
            [InlineKeyboardButton('欢迎语修改', callback_data='startupdate'),
             InlineKeyboardButton('菜单按钮', callback_data='addzdykey')],
            [InlineKeyboardButton('关闭', callback_data=f'close {user_id}')]
        ]
        jqrsyrs = len(list(user.find({})))
        numu = 0
        for i in list(user.find({"USDT": {"$gt": 0}})):
            USDT = i['USDT']

            numu += USDT

        fstext = f'''
当前机器人已有 {jqrsyrs}人 使用
总共余额：{standard_num(numu)} USDT
        '''
        context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def huifu(update: Update, context: CallbackContext):
    chat = update.effective_chat
    bot_id = context.bot.id
    if chat.type == 'private':
        user_id = update.effective_user.id
        user_list = user.find_one({"user_id": user_id})
        replymessage = update.message.reply_to_message
        text = replymessage.text
        del_message(update.message)
        messagetext = update.effective_message.text
        state = user_list['state']
        if state == '4' or state == '3':
            if '回复图文或图片视频文字' == text:
                if update.message.photo == [] and update.message.animation == None:
                    r_text = messagetext
                    sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'text': r_text}})
                    sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'file_id': ''}})
                    sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'send_type': 'text'}})
                    sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'state': 1}})
                    message_id = context.bot.send_message(chat_id=user_id, text=r_text)
                    time.sleep(3)
                    del_message(message_id)
                    message_id = context.user_data[f'wanfapeizhi{user_id}']
                    time.sleep(3)
                    del_message(message_id)

                else:
                    r_text = update.message.caption
                    try:
                        file = update.message.photo[-1].file_id
                        sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'text': r_text}})
                        sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'file_id': file}})
                        sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'send_type': 'photo'}})
                        sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'state': 1}})
                        message_id = context.bot.send_photo(chat_id=user_id, caption=r_text, photo=file)
                        time.sleep(3)
                        del_message(message_id)
                    except:
                        file = update.message.animation.file_id
                        sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'text': r_text}})
                        sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'file_id': file}})
                        sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'},
                                        {'$set': {'send_type': 'animation'}})
                        sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'state': 1}})
                        message_id = context.bot.sendAnimation(chat_id=user_id, caption=r_text, animation=file)
                        time.sleep(3)
                        del_message(message_id)
            elif '回复按钮设置' == text:
                text = messagetext
                message_id = context.user_data[f'wanfapeizhi{user_id}']
                del_message(message_id)
                keyboard = parse_urls(text)
                dumped = pickle.dumps(keyboard)
                sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'keyboard': dumped}})
                sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {'key_text': text}})
                try:
                    message_id = context.bot.send_message(chat_id=user_id, text='按钮设置成功',
                                                          reply_markup=InlineKeyboardMarkup(keyboard))
                    time.sleep(10)
                    del_message(message_id)

                except:
                    context.bot.send_message(chat_id=user_id, text=text)
                    message_id = context.bot.send_message(chat_id=user_id, text='按钮设置失败,请重新输入')
                    asyncio.sleep(10)
                    del_message(message_id)


def sifa(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    bot_id = context.bot.id
    fqdtw_list = sftw.find_one({'bot_id': bot_id, 'projectname': f'图文1🔽'})
    if fqdtw_list is None:
        sifatuwen(bot_id, '图文1🔽', '', '', '', b'\x80\x03]q\x00]q\x01a.', '')
        fqdtw_list = sftw.find_one({'bot_id': bot_id, 'projectname': f'图文1🔽'})
    state = fqdtw_list['state']
    if state == 1:
        keyboard = [[InlineKeyboardButton('图文设置', callback_data='tuwen'),
                     InlineKeyboardButton('按钮设置', callback_data='anniu'),
                     InlineKeyboardButton('查看图文', callback_data='cattu'),
                     InlineKeyboardButton('开启私发', callback_data='kaiqisifa')],
                    [InlineKeyboardButton('关闭❌', callback_data=f'close {user_id}')]]
        context.bot.send_message(chat_id=user_id, text='私发状态:已关闭🔴', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        keyboard = [[InlineKeyboardButton('图文设置', callback_data='tuwen'),
                     InlineKeyboardButton('按钮设置', callback_data='anniu'),
                     InlineKeyboardButton('查看图文', callback_data='cattu'),
                     InlineKeyboardButton('开启私发', callback_data='kaiqisifa')],
                    [InlineKeyboardButton('关闭❌', callback_data=f'close {user_id}')]]
        context.bot.send_message(chat_id=user_id, text='私发状态:已开启🟢', reply_markup=InlineKeyboardMarkup(keyboard))


def tuwen(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    context.user_data[f'key{user_id}'] = query.message
    message_id = context.bot.send_message(chat_id=user_id, text=f'回复图文或图片视频文字',
                                          reply_markup=ForceReply(force_reply=True))
    context.user_data[f'wanfapeizhi{user_id}'] = message_id


def cattu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    bot_id = context.bot.id
    fqdtw_list = sftw.find_one({'bot_id': bot_id, 'projectname': f'图文1🔽'})
    file_id = fqdtw_list['file_id']
    file_text = fqdtw_list['text']
    file_type = fqdtw_list['send_type']
    key_text = fqdtw_list['key_text']
    keyboard = pickle.loads(fqdtw_list['keyboard'])
    keyboard.append([InlineKeyboardButton('✅已读（点击销毁此消息）', callback_data=f'close {user_id}')])
    if fqdtw_list['text'] == '' and fqdtw_list['file_id'] == '':
        message_id = context.bot.send_message(chat_id=user_id, text='请设置图文后点击')
        time.sleep(3)
        del_message(message_id)
    else:
        try:
            context.bot.send_message(chat_id=user_id, text=key_text)
        except:
            pass
        if file_type == 'text':
            try:
                message_id = context.bot.send_message(chat_id=user_id, text=file_text,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
            except:
                message_id = context.bot.send_message(chat_id=user_id, text=file_text)
        else:
            if file_type == 'photo':
                try:
                    message_id = context.bot.send_photo(chat_id=user_id, caption=file_text, photo=file_id,
                                                        reply_markup=InlineKeyboardMarkup(keyboard))
                except:
                    message_id = context.bot.send_photo(chat_id=user_id, caption=file_text, photo=file_id)
            else:
                try:
                    message_id = context.bot.sendAnimation(chat_id=user_id, caption=file_text, animation=file_id,
                                                           reply_markup=InlineKeyboardMarkup(keyboard))
                except:
                    message_id = context.bot.sendAnimation(chat_id=user_id, caption=file_text, animation=file_id)
        time.sleep(3)
        del_message(message_id)


def anniu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    context.user_data[f'key{user_id}'] = query.message
    message_id = context.bot.send_message(chat_id=user_id, text=f'回复按钮设置',
                                          reply_markup=ForceReply(force_reply=True))
    context.user_data[f'wanfapeizhi{user_id}'] = message_id


def kaiqisifa(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    bot_id = context.bot.id
    job = context.job_queue.get_jobs_by_name(f'sifa')
    if job == ():
        sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {"state": 2}})
        keyboard = [
            [InlineKeyboardButton('图文设置', callback_data='tuwen'),
             InlineKeyboardButton('按钮设置', callback_data='anniu'),
             InlineKeyboardButton('查看图文', callback_data='cattu'),
             InlineKeyboardButton('开启私发', callback_data='kaiqisifa')],
            [InlineKeyboardButton('关闭❌', callback_data=f'close {user_id}')]]
        query.edit_message_text(text='私发状态:已开启🟢', reply_markup=InlineKeyboardMarkup(keyboard))
        context.job_queue.run_once(usersifa, 1, context={"user_id": user_id}, name=f'sifa')
        message_id = context.bot.send_message(chat_id=user_id, text='开启私发')
        context.user_data['sifa'] = message_id
    else:
        message_id = context.bot.send_message(chat_id=user_id, text='私发进行中')
        time.sleep(3)
        del_message(message_id)


def usersifa(context: CallbackContext):
    job = context.job
    bot_id = context.bot.id
    guanli_id = job.context['user_id']
    count = 0
    shibai = 0
    fqdtw_list = sftw.find_one({'bot_id': bot_id, 'projectname': f'图文1🔽'})
    file_id = fqdtw_list['file_id']
    file_text = fqdtw_list['text']
    file_type = fqdtw_list['send_type']
    key_text = fqdtw_list['key_text']
    keyboard = pickle.loads(fqdtw_list['keyboard'])

    keyboard.append([InlineKeyboardButton('✅已读（点击销毁此消息）', callback_data=f'close 12321')])
    for i in list(user.find({})):
        if file_type == 'text':
            try:

                message_id = context.bot.send_message(chat_id=i['user_id'], text=file_text,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
                count += 1
            except:
                shibai += 1
        else:
            if file_type == 'photo':
                try:

                    message_id = context.bot.send_photo(chat_id=i['user_id'], caption=file_text, photo=file_id,
                                                        reply_markup=InlineKeyboardMarkup(keyboard))
                    count += 1
                except:
                    shibai += 1
            else:
                try:

                    message_id = context.bot.sendAnimation(chat_id=i['user_id'], caption=file_text, animation=file_id,
                                                           reply_markup=InlineKeyboardMarkup(keyboard))
                    count += 1
                except:
                    shibai += 1
        time.sleep(3)
    sftw.update_one({'bot_id': bot_id, 'projectname': f'图文1🔽'}, {'$set': {"state": 1}})
    context.bot.send_message(chat_id=guanli_id, text=f'私发完毕\n成功:{count}\n失败:{shibai}')
    keyboard = [
        [InlineKeyboardButton('图文设置', callback_data='tuwen'),
         InlineKeyboardButton('按钮设置', callback_data='anniu'),
         InlineKeyboardButton('查看图文', callback_data='cattu'),
         InlineKeyboardButton('开启私发', callback_data='kaiqisifa')],
        [InlineKeyboardButton('关闭❌', callback_data=f'close {guanli_id}')]]
    context.bot.send_message(chat_id=guanli_id, text='私发状态:已关闭🔴', reply_markup=InlineKeyboardMarkup(keyboard))


def backstart(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    keyboard = [
        [InlineKeyboardButton('用户列表', callback_data='yhlist'),
         InlineKeyboardButton('对话用户私发', callback_data='sifa')],
        [InlineKeyboardButton('充值地址设置', callback_data='settrc20'),
         InlineKeyboardButton('商品管理', callback_data='spgli')],
        [InlineKeyboardButton('欢迎语修改', callback_data='startupdate'),
         InlineKeyboardButton('菜单按钮', callback_data='addzdykey')],
        [InlineKeyboardButton('关闭', callback_data=f'close {user_id}')]
    ]
    jqrsyrs = len(list(user.find({})))

    numu = 0
    for i in list(user.find({"USDT": {"$gt": 0}})):
        USDT = i['USDT']

        numu += USDT

    fstext = f'''
当前机器人已有 {jqrsyrs}人 使用
总共余额：{standard_num(numu)} USDT
    '''
    query.edit_message_text(text=fstext, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))


def gmaijilu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    lang = user.find_one({'user_id': user_id})['lang']
    df_id = int(query.data.replace('gmaijilu ', ''))
    jilu_list = list(gmjlu.find({'user_id': df_id}, sort=[('timer', -1)], limit=10))
    keyboard = []
    text_list = []
    count = 1
    for i in jilu_list:
        bianhao = i['bianhao']
        projectname = i['projectname']
        fhtext = i['text']
        projectname = projectname if lang == 'zh' else get_fy(projectname)
        keyboard.append([InlineKeyboardButton(f'{projectname}', callback_data=f'zcfshuo {bianhao}')])
        count += 1
    if lang == 'zh':

        if len(list(gmjlu.find({'user_id': df_id}))) > 10:
            keyboard.append([InlineKeyboardButton('下一页', callback_data=f'gmainext {df_id}:10')])
        keyboard.append([InlineKeyboardButton('返回', callback_data=f'backgmjl {df_id}')])
        try:
            query.edit_message_text(text='🛒您的购物记录', parse_mode='HTML',
                                    reply_markup=InlineKeyboardMarkup(keyboard))
        except:
            pass
    else:
        if len(list(gmjlu.find({'user_id': df_id}))) > 10:
            keyboard.append([InlineKeyboardButton('next page', callback_data=f'gmainext {df_id}:10')])
        keyboard.append([InlineKeyboardButton('return', callback_data=f'backgmjl {df_id}')])
        try:
            query.edit_message_text(text='🛒your shopping record', parse_mode='HTML',
                                    reply_markup=InlineKeyboardMarkup(keyboard))
        except:
            pass


def gmainext(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data.replace('gmainext ', '')
    page = data.split(":")[1]
    df_id = int(data.split(':')[0])
    user_id = query.from_user.id
    lang = user.find_one({'user_id': user_id})['lang']
    keyboard = []
    text_list = []
    jilu_list = list(gmjlu.find({"user_id": df_id}, sort=[("timer", -1)], skip=int(page), limit=10))
    count = 1
    for i in jilu_list:
        bianhao = i['bianhao']
        projectname = i['projectname']
        fhtext = i['text']
        projectname = projectname if lang == 'zh' else get_fy(projectname)
        keyboard.append([InlineKeyboardButton(f'{projectname}', callback_data=f'zcfshuo {bianhao}')])
        count += 1
    if lang == 'zh':
        if len(list(gmjlu.find({"user_id": df_id}, sort=[("timer", -1)], skip=int(page)))) > 10:
            if int(page) == 0:
                keyboard.append([InlineKeyboardButton('下一页', callback_data=f'gmainext {df_id}:{int(page) + 10}')])
            else:
                keyboard.append([InlineKeyboardButton('上一页', callback_data=f'gmainext {df_id}:{int(page) - 10}'),
                                 InlineKeyboardButton('下一页', callback_data=f'gmainext {df_id}:{int(page) + 10}')])
        else:
            keyboard.append([InlineKeyboardButton('上一页', callback_data=f'gmainext {df_id}:{int(page) - 10}')])

        keyboard.append([InlineKeyboardButton('返回', callback_data=f'backgmjl {df_id}')])
        try:
            query.edit_message_text(text='🛒您的购物记录', parse_mode='HTML',
                                    reply_markup=InlineKeyboardMarkup(keyboard))
        except:
            pass
    else:
        if len(list(gmjlu.find({"user_id": df_id}, sort=[("timer", -1)], skip=int(page)))) > 10:
            if int(page) == 0:
                keyboard.append([InlineKeyboardButton('next page', callback_data=f'gmainext {df_id}:{int(page) + 10}')])
            else:
                keyboard.append(
                    [InlineKeyboardButton('previous page', callback_data=f'gmainext {df_id}:{int(page) - 10}'),
                     InlineKeyboardButton('next page', callback_data=f'gmainext {df_id}:{int(page) + 10}')])
        else:
            keyboard.append([InlineKeyboardButton('previous page', callback_data=f'gmainext {df_id}:{int(page) - 10}')])

        keyboard.append([InlineKeyboardButton('Back', callback_data=f'backgmjl {df_id}')])
        try:
            query.edit_message_text(text='🛒Your shopping history', parse_mode='HTML',
                                    reply_markup=InlineKeyboardMarkup(keyboard))
        except:
            pass


def backgmjl(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    df_id = int(query.data.replace('backgmjl ', ''))
    df_list = user.find_one({'user_id': df_id})
    df_fullname = df_list['fullname']
    df_username = df_list['username']
    if df_username is None:
        df_username = df_fullname
    else:
        df_username = f'<a href="https://t.me/{df_username}">{df_username}</a>'
    creation_time = df_list['creation_time']
    zgsl = df_list['zgsl']
    zgje = df_list['zgje']
    USDT = df_list['USDT']
    lang = df_list['lang']
    if lang == 'en':

        fstext = f'''
<b>Your ID:</b>  <code>{df_id}</code>
<b>username:</b>  {df_username} 
<b>Registration date:</b>  {creation_time}

<b>Total purchase quantity:</b>  {zgsl}

<b>Total purchase amount:</b>  {standard_num(zgje)} USDT

<b> balance:</b>  {USDT} USDT
        '''

        keyboard = [[InlineKeyboardButton('🛒Purchase history', callback_data=f'gmaijilu {df_id}')]]
    else:
        fstext = f'''
<b>您的ID:</b>  <code>{df_id}</code>
<b>您的用户名:</b>  {df_username} 
<b>注册日期:</b>  {creation_time}

<b>总购数量:</b>  {zgsl}

<b>总购金额:</b>  {standard_num(zgje)} USDT

<b>您的余额:</b>  {USDT} USDT
            '''
        keyboard = [[InlineKeyboardButton('🛒购买记录', callback_data=f'gmaijilu {df_id}')]]

    query.edit_message_text(text=fstext, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML',
                            disable_web_page_preview=True)


def zcfshuo(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    lang = user.find_one({'user_id': user_id})['lang']
    bianhao = query.data.replace('zcfshuo ', '')
    gmjlu_list = gmjlu.find_one({'bianhao': bianhao})
    leixing = gmjlu_list['leixing']
    if leixing == '会员链接':
        text = gmjlu_list['text']

        context.bot.send_message(chat_id=user_id, text=text, disable_web_page_preview=True)

    else:
        zip_filename = gmjlu_list['text']
        fstext = gmjlu_list['ts']
        fstext = fstext if lang == 'zh' else get_fy(fstext)
        keyboard = [[InlineKeyboardButton('✅已读（点击销毁此消息）', callback_data=f'close {user_id}')]]
        context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML', disable_web_page_preview=True,
                                 reply_markup=InlineKeyboardMarkup(keyboard))

        query.message.reply_document(open(zip_filename, "rb"))


def yhlist(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    jilu_list = list(user.find({}, limit=10))
    keyboard = []
    text_list = []
    count = 1
    for i in jilu_list:
        df_id = i['user_id']
        df_username = i['username']
        df_fullname = i['fullname'].replace('<', '').replace('>', '')
        USDT = i['USDT']
        text_list.append(
            f'{count}. <a href="tg://user?id={df_id}">{df_fullname}</a> ID:<code>{df_id}</code>-@{df_username}-余额:{USDT}')
        count += 1
    if len(list(user.find({}))) > 10:
        keyboard.append([InlineKeyboardButton('下一页', callback_data=f'yhnext 10:{count}')])

    keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])

    text_list = '\n'.join(text_list)
    try:
        query.edit_message_text(text=text_list, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        pass


def yhnext(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data.replace('yhnext ', '')
    page = data.split(":")[0]
    count = int(data.split(":")[1])
    keyboard = []
    text_list = []
    jilu_list = list(user.find({}, skip=int(page), limit=10))
    for i in jilu_list:
        df_id = i['user_id']
        df_username = i['username']
        df_fullname = i['fullname'].replace('<', '').replace('>', '')
        USDT = i['USDT']
        text_list.append(
            f'{count}. <a href="tg://user?id={df_id}">{df_fullname}</a> ID:<code>{df_id}</code>-@{df_username}-余额:{USDT}')
        count += 1
    if len(list(user.find({}, skip=int(page)))) > 10:
        if int(page) == 0:
            keyboard.append([InlineKeyboardButton('下一页', callback_data=f'yhnext {int(page) + 10}:{count}')])
        else:
            keyboard.append([InlineKeyboardButton('上一页', callback_data=f'yhnext {int(page) - 10}:{count - 20}'),
                             InlineKeyboardButton('下一页', callback_data=f'yhnext {int(page) + 10}:{count}')])
    else:
        keyboard.append([InlineKeyboardButton('上一页', callback_data=f'yhnext {int(page) - 10}:{count - 20}')])

    text_list = '\n'.join(text_list)
    keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
    query.bot.edit_message_text(text=text_list, chat_id=query.message.chat_id,
                                message_id=query.message.message_id, reply_markup=InlineKeyboardMarkup(keyboard),
                                parse_mode='HTML')


def tjbaobiao(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id


def spgli(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    sp_list = list(fenlei.find({}))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]

    for i in sp_list:
        uid = i['uid']
        projectname = i['projectname']
        row = i['row']
        keyboard[row - 1].append(InlineKeyboardButton(f'{projectname}', callback_data=f'flxxi {uid}'))
    if sp_list == []:
        keyboard.append([InlineKeyboardButton("新建一行", callback_data='newfl')])
    else:
        keyboard.append([InlineKeyboardButton("新建一行", callback_data='newfl'),
                         InlineKeyboardButton('调整行排序', callback_data='paixufl'),
                         InlineKeyboardButton('删除一行', callback_data='delfl')])
    keyboard.append([InlineKeyboardButton('返回', callback_data='backstart'),
                     InlineKeyboardButton('关闭', callback_data=f'close {user_id}')])
    text = f'''
商品管理
    '''
    query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


def generate_24bit_uid():
    # 生成一个UUID
    uid = uuid.uuid4()

    # 将UUID转换为字符串
    uid_str = str(uid)

    # 使用MD5哈希算法将字符串哈希为一个128位的值
    hashed_uid = hashlib.md5(uid_str.encode()).hexdigest()

    # 取哈希值的前24位作为我们的24位UID
    return hashed_uid[:24]


def newfl(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    del_message(query.message)
    bot_id = context.bot.id
    maxrow = fenlei.find_one({}, sort=[('row', -1)])
    if maxrow is None:
        maxrow = 1
    else:
        maxrow = maxrow['row'] + 1
    uid = generate_24bit_uid()
    fenleibiao(uid, '点击按钮修改', maxrow)
    keylist = list(fenlei.find({}, sort=[('row', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for i in keylist:
        uid = i['uid']
        projectname = i['projectname']
        row = i['row']
        keyboard[row - 1].append(InlineKeyboardButton(f'{projectname}', callback_data=f'flxxi {uid}'))
    keyboard.append([InlineKeyboardButton("新建一行", callback_data='newfl'),
                     InlineKeyboardButton('调整行排序', callback_data='paixufl'),
                     InlineKeyboardButton('删除一行', callback_data='delfl')])
    context.bot.send_message(chat_id=user_id, text='商品管理', reply_markup=InlineKeyboardMarkup(keyboard))


def flxxi(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    uid = query.data.replace('flxxi ', '')
    fl_pro = fenlei.find_one({'uid': uid})['projectname']
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    ej_list = ejfl.find({'uid': uid})
    for i in ej_list:
        nowuid = i['nowuid']
        projectname = i['projectname']
        row = i['row']
        keyboard[row - 1].append(InlineKeyboardButton(f'{projectname}', callback_data=f'fejxxi {nowuid}'))

    keyboard.append([InlineKeyboardButton('修改分类名', callback_data=f'upspname {uid}'),
                     InlineKeyboardButton('新增二级分类', callback_data=f'newejfl {uid}')])
    keyboard.append([InlineKeyboardButton('调整二级分类排序', callback_data=f'paixuejfl {uid}'),
                     InlineKeyboardButton('删除二级分类', callback_data=f'delejfl {uid}')])
    keyboard.append([InlineKeyboardButton('返回', callback_data=f'spgli')])
    fstext = f'''
分类: {fl_pro}
    '''
    query.edit_message_text(text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def fejxxi(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    nowuid = query.data.replace('fejxxi ', '')

    ej_list = ejfl.find_one({'nowuid': nowuid})
    uid = ej_list['uid']
    ej_projectname = ej_list['projectname']
    money = ej_list['money']
    fl_pro = fenlei.find_one({'uid': uid})['projectname']
    keyboard = [
        [InlineKeyboardButton('取出所有库存', callback_data=f'qchuall {nowuid}'),
         InlineKeyboardButton('此商品使用说明', callback_data=f'update_sysm {nowuid}')],
        [InlineKeyboardButton('上传谷歌账户', callback_data=f'update_gg {nowuid}'),
         InlineKeyboardButton('购买此商品提示', callback_data=f'update_wbts {nowuid}')],
        [InlineKeyboardButton('上传链接', callback_data=f'update_hy {nowuid}'),
         InlineKeyboardButton('上传txt文件', callback_data=f'update_txt {nowuid}')],
        [InlineKeyboardButton('上传号包', callback_data=f'update_hb {nowuid}'),
         InlineKeyboardButton('上传协议号', callback_data=f'update_xyh {nowuid}')],
        [InlineKeyboardButton('修改二级分类名', callback_data=f'upejflname {nowuid}'),
         InlineKeyboardButton('修改价格', callback_data=f'upmoney {nowuid}')],
        [InlineKeyboardButton('返回', callback_data=f'flxxi {uid}')]
    ]
    kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
    ys = len(list(hb.find({'nowuid': nowuid, 'state': 1})))
    fstext = f'''
主分类: {fl_pro}
二级分类: {ej_projectname}

价格: {money}U
库存: {kc}
已售: {ys}
    '''
    query.edit_message_text(text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def update_xyh(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    nowuid = query.data.replace('update_xyh ', '')
    fstext = f'''
发送协议号压缩包，自动识别里面的json或session格式
    '''
    user.update_one({"user_id": user_id}, {"$set": {"sign": f'update_xyh {nowuid}'}})
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def update_gg(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    nowuid = query.data.replace('update_gg ', '')
    fstext = f'''
发送txt文件
    '''
    user.update_one({"user_id": user_id}, {"$set": {"sign": f'update_gg {nowuid}'}})
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def update_txt(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    nowuid = query.data.replace('update_txt ', '')
    fstext = f'''
api号码链接专用，请正确上传，发送txt文件，一行一个
    '''
    user.update_one({"user_id": user_id}, {"$set": {"sign": f'update_txt {nowuid}'}})
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def update_sysm(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    nowuid = query.data.replace('update_sysm ', '')
    dqts = ejfl.find_one({'nowuid': nowuid})['sysm']

    context.bot.send_message(chat_id=user_id, text=dqts, parse_mode='HTML')

    fstext = f'''
当前使用说明为上面
输入新的文字更改
    '''
    user.update_one({"user_id": user_id}, {"$set": {"sign": f'update_sysm {nowuid}'}})
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def update_wbts(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    nowuid = query.data.replace('update_wbts ', '')
    dqts = ejfl.find_one({'nowuid': nowuid})['text']

    context.bot.send_message(chat_id=user_id, text=dqts, parse_mode='HTML')

    fstext = f'''
当前分类提示为上面
输入新的文字更改
    '''
    user.update_one({"user_id": user_id}, {"$set": {"sign": f'update_wbts {nowuid}'}})
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def update_hy(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    nowuid = query.data.replace('update_hy ', '')
    fstext = f'''
发送链接，换行代表多个
单个
https://t.me/giftcode/IApV5cqF2FCzAQAA5aDXkeEqQrQ
多个
https://t.me/giftcode/IApV5cqF2FCzAQAA5aDXkeEqQrQ
https://t.me/giftcode/wI_oG9K2oFBSAQAA-Z2W0Fb3ng8
https://t.me/giftcode/_xSoPUXMgVBmAQAAiKBPNxWWIpY
    '''
    user.update_one({"user_id": user_id}, {"$set": {"sign": f'update_hy {nowuid}'}})
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard),
                             disable_web_page_preview=True)


def update_hb(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    nowuid = query.data.replace('update_hb ', '')
    fstext = f'''
发送号包
    '''
    user.update_one({"user_id": user_id}, {"$set": {"sign": f'update_hb {nowuid}'}})
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def upmoney(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    uid = query.data.replace('upmoney ', '')
    fstext = f'''
输入新的价格
    '''

    user.update_one({"user_id": user_id}, {"$set": {"sign": f'upmoney {uid}'}})
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def upejflname(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    uid = query.data.replace('upejflname ', '')
    fstext = f'''
输入新的名字
例如 🇨🇳+86中国~直登号(tadta)
    '''

    user.update_one({"user_id": user_id}, {"$set": {"sign": f'upejflname {uid}'}})
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def upspname(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    uid = query.data.replace('upspname ', '')
    fstext = f'''
输入新的名字
例如 🌎亚洲国家~✈直登号(tadta)
    '''

    user.update_one({"user_id": user_id}, {"$set": {"sign": f'upspname {uid}'}})
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def newejfl(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    uid = query.data.replace('newejfl ', '')

    maxrow = ejfl.find_one({'uid': uid}, sort=[('row', -1)])
    if maxrow is None:
        maxrow = 1
    else:
        maxrow = maxrow['row'] + 1
    nowuid = generate_24bit_uid()
    erjifenleibiao(uid, nowuid, '点击按钮修改', maxrow)
    fl_pro = fenlei.find_one({'uid': uid})['projectname']
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    ej_list = ejfl.find({'uid': uid})
    for i in ej_list:
        nowuid = i['nowuid']
        projectname = i['projectname']
        row = i['row']
        keyboard[row - 1].append(InlineKeyboardButton(f'{projectname}', callback_data=f'fejxxi {nowuid}'))

    keyboard.append([InlineKeyboardButton('修改分类名', callback_data=f'upspname {uid}'),
                     InlineKeyboardButton('新增二级分类', callback_data=f'newejfl {uid}')])
    keyboard.append([InlineKeyboardButton('调整二级分类排序', callback_data=f'paixuejfl {uid}'),
                     InlineKeyboardButton('删除二级分类', callback_data=f'delejfl {uid}')])
    keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
    fstext = f'''
分类: {fl_pro}
    '''
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def addzdykey(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    keylist = get_key.find({}, sort=[('Row', 1), ('first', 1)])
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for i in keylist:
        projectname = i['projectname']
        row = i['Row']
        first = i['first']
        keyboard[i["Row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'keyxq {row}:{first}'))
    if keylist == []:
        keyboard = [[InlineKeyboardButton("新建一行", callback_data='newrow')]]
    else:
        keyboard.append([InlineKeyboardButton('新建一行', callback_data='newrow'),
                         InlineKeyboardButton('删除一行', callback_data='delrow'),
                         InlineKeyboardButton('调整行排序', callback_data='paixurow')])
        keyboard.append([InlineKeyboardButton('修改按钮', callback_data='newkey')])

    keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
    text = f'''
自定义按钮
    '''
    query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


def newkey(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    keylist = list(get_key.find({}, sort=[('Row', 1), ('first', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    count = []
    for i in keylist:
        projectname = i['projectname']
        row = i['Row']
        first = i['first']
        keyboard[i["Row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'keyxq {row}:{first}'))
        count.append(row)
    if count == []:
        context.bot.send_message(chat_id=user_id, text='请先新建一行')
    else:
        maxrow = max(count)
        for i in range(0, maxrow):
            keyboard.append([InlineKeyboardButton(f'第{i + 1}行', callback_data=f'dddd'),
                             InlineKeyboardButton('➕', callback_data=f'addhangkey {i + 1}'),
                             InlineKeyboardButton('➖', callback_data=f'delhangkey {i + 1}')])
        keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
        keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
        query.edit_message_text(text='自定义按钮', reply_markup=InlineKeyboardMarkup(keyboard))


def newrow(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    del_message(query.message)
    bot_id = context.bot.id
    maxrow = get_key.find_one({}, sort=[('Row', -1)])
    if maxrow is None:
        maxrow = 1
    else:
        maxrow = maxrow['Row'] + 1
    keybutton(maxrow, 1)
    keylist = list(get_key.find({}, sort=[('Row', 1), ('first', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for i in keylist:
        projectname = i['projectname']
        row = i['Row']
        first = i['first']
        keyboard[i["Row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'keyxq {row}:{first}'))
    keyboard.append([InlineKeyboardButton('新建一行', callback_data='newrow'),
                     InlineKeyboardButton('删除一行', callback_data='delrow'),
                     InlineKeyboardButton('调整行排序', callback_data='paixurow')])
    keyboard.append([InlineKeyboardButton('修改按钮', callback_data='newkey')])
    keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
    context.bot.send_message(chat_id=user_id, text='自定义按钮', reply_markup=InlineKeyboardMarkup(keyboard))


def close(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = query.message.chat
    query.answer()
    yh_id = query.data.replace("close ", '')
    bot_id = context.bot.id
    chat_id = chat.id
    user_id = query.from_user.id

    user.update_one({'user_id': user_id}, {'$set': {'sign': 0}})
    context.bot.delete_message(chat_id=query.from_user.id, message_id=query.message.message_id)


def paixurow(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    keylist = list(get_key.find({}, sort=[('Row', 1), ('first', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    count = []
    for i in keylist:
        projectname = i['projectname']
        row = i['Row']
        first = i['first']
        keyboard[i["Row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'keyxq {row}:{first}'))
        count.append(row)
    if count == []:
        context.bot.send_message(chat_id=user_id, text='没有按钮存在')
    else:
        maxrow = max(count)
        if maxrow == 1:
            context.bot.send_message(chat_id=user_id, text='只有一行按钮无法调整')
        else:
            for i in range(0, maxrow):
                if i == 0:
                    keyboard.append(
                        [InlineKeyboardButton(f'第{i + 1}行下移', callback_data=f'paixuyidong xiayi:{i + 1}')])
                elif i == maxrow - 1:
                    keyboard.append(
                        [InlineKeyboardButton(f'第{i + 1}行上移', callback_data=f'paixuyidong shangyi:{i + 1}')])
                else:
                    keyboard.append(
                        [InlineKeyboardButton(f'第{i + 1}行上移', callback_data=f'paixuyidong shangyi:{i + 1}'),
                         InlineKeyboardButton(f'第{i + 1}行下移', callback_data=f'paixuyidong xiayi:{i + 1}')])
            keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
            keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
            query.edit_message_text(text='自定义按钮', reply_markup=InlineKeyboardMarkup(keyboard))


def paixuyidong(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    qudata = query.data.replace('paixuyidong ', '')
    qudataall = qudata.split(':')
    yidongtype = qudataall[0]
    row = int(qudataall[1])
    if yidongtype == 'shangyi':
        get_key.update_many({"Row": row - 1}, {"$set": {'Row': 99}})
        get_key.update_many({"Row": row}, {"$set": {'Row': row - 1}})
        get_key.update_many({"Row": 99}, {"$set": {'Row': row}})
    else:
        get_key.update_many({"Row": row + 1}, {"$set": {'Row': 99}})
        get_key.update_many({"Row": row}, {"$set": {'Row': row + 1}})
        get_key.update_many({"Row": 99}, {"$set": {'Row': row}})
    keylist = list(get_key.find({}, sort=[('Row', 1), ('first', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for i in keylist:
        projectname = i['projectname']
        row = i['Row']
        first = i['first']
        keyboard[i["Row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'keyxq {row}:{first}'))
    keyboard.append([InlineKeyboardButton('新建一行', callback_data='newrow'),
                     InlineKeyboardButton('删除一行', callback_data='delrow'),
                     InlineKeyboardButton('调整行排序', callback_data='paixurow')])
    keyboard.append([InlineKeyboardButton('修改按钮', callback_data='newkey')])
    keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
    query.edit_message_text(text='自定义按钮', reply_markup=InlineKeyboardMarkup(keyboard))


def delrow(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    keylist = list(get_key.find({}, sort=[('Row', 1), ('first', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    count = []
    for i in keylist:
        projectname = i['projectname']
        row = i['Row']
        first = i['first']
        keyboard[i["Row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'keyxq {row}:{first}'))
        count.append(row)
    if count == []:
        context.bot.send_message(chat_id=user_id, text='没有按钮存在')
    else:
        maxrow = max(count)
        for i in range(0, maxrow):
            keyboard.append([InlineKeyboardButton(f'删除第{i + 1}行', callback_data=f'qrscdelrow {i + 1}')])
        keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
        keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
        query.edit_message_text(text='自定义按钮', reply_markup=InlineKeyboardMarkup(keyboard))


def qrscdelrow(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    del_message(query.message)
    row = int(query.data.replace('qrscdelrow ', ''))
    bot_id = context.bot.id
    get_key.delete_many({"Row": row})
    max_list = list(get_key.find({'Row': {"$gt": row}}))
    for i in max_list:
        max_row = i['Row']
        get_key.update_many({'Row': max_row}, {"$set": {"Row": max_row - 1}})
    maxrow = get_key.find_one({}, sort=[('Row', -1)])
    if maxrow is None:
        maxrow = 1
    else:
        maxrow = maxrow['Row'] + 1
    # keybutton(maxrow,1)
    keylist = list(get_key.find({}, sort=[('Row', 1), ('first', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for i in keylist:
        projectname = i['projectname']
        row = i['Row']
        first = i['first']
        keyboard[i["Row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'keyxq {row}:{first}'))
    keyboard.append([InlineKeyboardButton('新建一行', callback_data='newrow'),
                     InlineKeyboardButton('删除一行', callback_data='delrow'),
                     InlineKeyboardButton('调整行排序', callback_data='paixurow')])
    keyboard.append([InlineKeyboardButton('修改按钮', callback_data='newkey')])
    keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
    context.bot.send_message(chat_id=user_id, text='自定义按钮', reply_markup=InlineKeyboardMarkup(keyboard))


def delhangkey(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    row = int(query.data.replace('delhangkey ', ''))
    bot_id = context.bot.id
    key_list = list(get_key.find({'Row': row}, sort=[('first', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    count = []
    for i in key_list:
        projectname = i['projectname']
        row = i['Row']
        first = i['first']
        keyboard[i["Row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'keyxq {row}:{first}'))
        count.append(row)
    if count == []:
        context.bot.send_message(chat_id=user_id, text='没有按钮存在')
    else:

        # maxrow = max(count)
        for i in range(0, len(count)):
            keyboard[count[i]].append(InlineKeyboardButton('➖', callback_data=f'qrdelliekey {row}:{i + 1}'))
        keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
        keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
        query.edit_message_text(text='自定义按钮', reply_markup=InlineKeyboardMarkup(keyboard))


def keyxq(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    qudata = query.data.replace('keyxq ', '')
    qudataall = qudata.split(':')
    row = int(qudataall[0])
    first = int(qudataall[1])
    key_list = get_key.find_one({'Row': row, 'first': first})
    projectname = key_list['projectname']
    text = key_list['text']
    print_text = f'''
这是第{row}行第{first}个按钮

按钮名称: {projectname}
    '''

    keyboard = [
        [InlineKeyboardButton('图文设置', callback_data=f'settuwenset {row}:{first}'),
         InlineKeyboardButton('查看图文设置', callback_data=f'cattuwenset {row}:{first}')],
        [InlineKeyboardButton('修改尾随按钮', callback_data=f'setkeyboard {row}:{first}'),
         InlineKeyboardButton('修改按钮名字', callback_data=f'setkeyname {row}:{first}')],
        [InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]
    ]

    keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
    query.edit_message_text(text=print_text, reply_markup=InlineKeyboardMarkup(keyboard))


def setkeyname(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    qudata = query.data.replace('setkeyname ', '')
    qudataall = qudata.split(':')
    row = int(qudataall[0])
    first = int(qudataall[1])
    text = f'''
输入要修改的名字
    '''
    user.update_one({'user_id': user_id}, {"$set": {"sign": f'setkeyname {row}:{first}'}})
    keyboard = [[InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]]
    keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
    query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


def setkeyboard(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    qudata = query.data.replace('setkeyboard ', '')
    qudataall = qudata.split(':')
    row = int(qudataall[0])
    first = int(qudataall[1])
    text = f'''
按以下格式设置按钮，填入◈之间，同一行用 | 隔开
按钮名称&https://t.me/... | 按钮名称&https://t.me/...
按钮名称&https://t.me/... | 按钮名称&https://t.me/... | 按钮名称&https://t.me/....
    '''
    key_list = get_key.find_one({'Row': row, 'first': first})
    key_text = key_list['key_text']
    if key_text != '':
        context.bot.send_message(chat_id=user_id, text=key_text)
    user.update_one({'user_id': user_id}, {"$set": {"sign": f'setkeyboard {row}:{first}'}})
    keyboard = [[InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]]
    keyboard.append([InlineKeyboardButton('返回主界面', callback_data=f'backstart')])
    query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


def settuwenset(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    qudata = query.data.replace('settuwenset ', '')
    qudataall = qudata.split(':')
    row = int(qudataall[0])
    first = int(qudataall[1])
    key_list = get_key.find_one({'Row': row, 'first': first})
    key_text = key_list['key_text']
    text = key_list['text']
    file_type = key_list['file_type']
    file_id = key_list['file_id']
    entities = pickle.loads(key_list['entities'])
    keyboard = pickle.loads(key_list['keyboard'])
    if text == '' and file_id == '':
        pass
    else:
        if file_type == 'text':
            message_id = context.bot.send_message(chat_id=user_id, text=text,
                                                  reply_markup=InlineKeyboardMarkup(keyboard), entities=entities)
        else:
            if file_type == 'photo':
                message_id = context.bot.send_photo(chat_id=user_id, caption=text, photo=file_id,
                                                    reply_markup=InlineKeyboardMarkup(keyboard),
                                                    caption_entities=entities)
            else:
                message_id = context.bot.sendAnimation(chat_id=user_id, caption=text, animation=file_id,
                                                       reply_markup=InlineKeyboardMarkup(keyboard),
                                                       caption_entities=entities)
    text = f'''
✍️ 发送你的图文设置

文字、视频、图片、gif、图文
    '''
    user.update_one({'user_id': user_id}, {"$set": {"sign": f'settuwenset {row}:{first}'}})
    keyboard = [[InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]]
    context.bot.send_message(chat_id=user_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))


def cattuwenset(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    qudata = query.data.replace('cattuwenset ', '')
    qudataall = qudata.split(':')
    row = int(qudataall[0])
    first = int(qudataall[1])
    key_list = get_key.find_one({'Row': row, 'first': first})
    key_text = key_list['key_text']
    text = key_list['text']
    file_type = key_list['file_type']
    file_id = key_list['file_id']
    entities = pickle.loads(key_list['entities'])
    keyboard = pickle.loads(key_list['keyboard'])
    if text == '' and file_id == '':
        message_id = context.bot.send_message(chat_id=user_id, text='请设置图文后点击')
        timer11 = Timer(3, del_message, args=[message_id])
        timer11.start()
    else:
        if file_type == 'text':
            message_id = context.bot.send_message(chat_id=user_id, text=text,
                                                  reply_markup=InlineKeyboardMarkup(keyboard), entities=entities)
        else:
            if file_type == 'photo':
                message_id = context.bot.send_photo(chat_id=user_id, caption=text, photo=file_id,
                                                    reply_markup=InlineKeyboardMarkup(keyboard),
                                                    caption_entities=entities)
            else:
                message_id = context.bot.sendAnimation(chat_id=user_id, caption=text, animation=file_id,
                                                       reply_markup=InlineKeyboardMarkup(keyboard),
                                                       caption_entities=entities)
        timer11 = Timer(3, del_message, args=[message_id])
        timer11.start()


def qrdelliekey(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    qudata = query.data.replace('qrdelliekey ', '')
    qudataall = qudata.split(':')
    row = int(qudataall[0])
    first = int(qudataall[1])
    get_key.delete_one({"Row": row, 'first': first})
    max_list = list(get_key.find({'Row': row, 'first': {"$gt": first}}))
    for i in max_list:
        max_lie = i['first']
        get_key.update_one({'Row': row, 'first': max_lie}, {"$set": {"first": max_lie - 1}})

    keylist = list(get_key.find({}, sort=[('Row', 1), ('first', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    count = []
    for i in keylist:
        projectname = i['projectname']
        row = i['Row']
        first = i['first']
        keyboard[i["Row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'keyxq {row}:{first}'))
        count.append(row)
    if count == []:
        context.bot.send_message(chat_id=user_id, text='请先新建一行')
    else:
        maxrow = max(count)
        for i in range(0, maxrow):
            keyboard.append([InlineKeyboardButton(f'第{i + 1}行', callback_data=f'dddd'),
                             InlineKeyboardButton('➕', callback_data=f'addhangkey {i + 1}'),
                             InlineKeyboardButton('➖', callback_data=f'delhangkey {i + 1}')])
        keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
        context.bot.send_message(chat_id=user_id, text='自定义按钮', reply_markup=InlineKeyboardMarkup(keyboard))


def addhangkey(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    del_message(query.message)
    row = int(query.data.replace('addhangkey ', ''))
    bot_id = context.bot.id
    lie = get_key.find_one({'Row': row}, sort=[('first', -1)])['first']
    keybutton(row, lie + 1)

    keylist = list(get_key.find({}, sort=[('Row', 1), ('first', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    count = []
    for i in keylist:
        projectname = i['projectname']
        row = i['Row']
        first = i['first']
        keyboard[i["Row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'keyxq {row}:{first}'))
        count.append(row)
    if count == []:
        context.bot.send_message(chat_id=user_id, text='请先新建一行')
    else:
        maxrow = max(count)
        for i in range(0, maxrow):
            keyboard.append([InlineKeyboardButton(f'第{i + 1}行', callback_data=f'dddd'),
                             InlineKeyboardButton('➕', callback_data=f'addhangkey {i + 1}'),
                             InlineKeyboardButton('➖', callback_data=f'delhangkey {i + 1}')])
        keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
        context.bot.send_message(chat_id=user_id, text='自定义按钮', reply_markup=InlineKeyboardMarkup(keyboard))


def settrc20(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    text = f'''
输入以T开头共34位的 trc20地址
'''
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    user.update_one({'user_id': user_id}, {"$set": {"sign": 'settrc20'}})
    context.bot.send_message(chat_id=user_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))


def startupdate(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    text = f'''
输入新的欢迎语
'''
    keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    user.update_one({'user_id': user_id}, {"$set": {"sign": 'startupdate'}})
    context.bot.send_message(chat_id=user_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))


def zdycz(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    lang = user.find_one({'user_id': user_id})['lang']
    bot_id = context.bot.id

    if lang == 'zh':
        text = f'''
输入充值金额
    '''
        keyboard = [[InlineKeyboardButton('取消', callback_data=f'close {user_id}')]]
    else:
        text = f'''
Enter the recharge amount
        '''
        keyboard = [[InlineKeyboardButton('Cancel', callback_data=f'close {user_id}')]]
    message_id = context.bot.send_message(chat_id=user_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))

    user.update_one({'user_id': user_id}, {"$set": {"sign": f'zdycz {message_id.message_id}'}})


def yuecz(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    money = int(query.data.replace('yuecz ', ''))
    bot_id = context.bot.id
    user_id = query.from_user.id
    lang = user.find_one({'user_id': user_id})['lang']
    topup.delete_many({'user_id': user_id})
    timer = time.strftime('%Y%m%d', time.localtime())
    bianhao = timer + str(int(time.time()))
    while 1:
        suijishu = round(random.uniform(0.01, 0.50), 2)
        money = Decimal(str(money)) + Decimal(str(suijishu))
        if topup.find_one({"money": float(money)}) is None:
            break

    timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    trc20 = shangtext.find_one({'projectname': '充值地址'})['text']
    text = f'''
充值详情

实际支付金额：<code>{money}USDT</code>

收款地址：<code>{trc20}</code>


<b>请一定按照金额后面小数点转账，否则未到账概不负责
⚠️请在10分钟内付款，超时订单自动取消</b>
    '''
    text = text if lang == 'zh' else get_fy(text)
    if lang == 'zh':
        keyboard = [[InlineKeyboardButton('❌取消订单', callback_data=f'qxdingdan {user_id}')]]
    else:
        keyboard = [[InlineKeyboardButton('❌Cancel order', callback_data=f'qxdingdan {user_id}')]]
    message_id = context.bot.send_photo(chat_id=user_id, photo=open(f'{trc20}.png', 'rb'), caption=text,
                                        parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    topup.insert_one(
        {
            'bianhao': bianhao,
            'user_id': user_id,
            'money': float(money),
            'suijishu': suijishu,
            'timer': timer,
            'message_id': message_id.message_id
        }
    )


def catejflsp(update: Update, context: CallbackContext):
    query = update.callback_query
    uid = query.data.replace('catejflsp ', '').split(':')[0]
    zhsl = int(query.data.replace('catejflsp ', '').split(':')[1])
    query.answer()

    user_id = query.from_user.id
    lang = user.find_one({'user_id': user_id})['lang']

    # 获取所有二级分类并排序
    ej_list = ejfl.find({'uid': uid})
    sorted_ej_list = sorted(ej_list, key=lambda x: -len(list(hb.find({'nowuid': x['nowuid'], 'state': 0}))))

    keyboard = [[] for _ in range(len(sorted_ej_list))]

    # 创建键盘按钮
    for count, i in enumerate(sorted_ej_list):
        nowuid = i['nowuid']
        projectname = i['projectname']

        hsl = hb.count_documents({'nowuid': nowuid, 'state': 0})

        projectname = projectname if lang == 'zh' else get_fy(projectname)
        keyboard[count].append(InlineKeyboardButton(f'{projectname}  ({hsl})', callback_data=f'gmsp {nowuid}:{hsl}'))

    # 添加返回和关闭按钮
    back_text = '🔙返回' if lang == 'zh' else '🔙Back'
    close_text = '❌关闭' if lang == 'zh' else '❌Close'
    keyboard.append([InlineKeyboardButton(back_text, callback_data='backzcd'),
                     InlineKeyboardButton(close_text, callback_data=f'close {user_id}')])

    fstext = '''
<b>🛒这是商品列表  选择你需要的商品：

❗️没使用过的本店商品的，请先少量购买测试，以免造成不必要的争执！谢谢合作！

❗️购买后，请立即检测账户是否正常！超过1小时视为放弃售后服务！</b>
        '''

    fstext = fstext if lang == 'zh' else get_fy(fstext)
    query.edit_message_text(fstext, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


def gmsp(update: Update, context: CallbackContext):
    query = update.callback_query

    data = query.data.replace('gmsp ', '')
    nowuid = data.split(':')[0]
    hsl = data.split(':')[1]

    bot_id = context.bot.id
    user_id = query.from_user.id
    lang = user.find_one({'user_id': user_id})['lang']

    ejfl_list = ejfl.find_one({'nowuid': nowuid})
    projectname = ejfl_list['projectname']
    money = ejfl_list['money']
    uid = ejfl_list['uid']

    query.answer()
    if lang == 'zh':
        fstext = f'''
<b>✅您正在购买:  {projectname}

💰 价格： {money} USDT

🏢 库存： {hsl}

❗️ 未使用过的本店商品的，请先少量购买测试，以免造成不必要的争执！谢谢合作！

❗️账号价格会根据市场价有所浮动！请理解！</b>
            '''
        keyboard = [
            [InlineKeyboardButton('✅购买', callback_data=f'gmqq {nowuid}:{hsl}'),
             InlineKeyboardButton('使用说明📜', callback_data='sysming')],
            [InlineKeyboardButton('🏠主菜单', callback_data='backzcd'),
             InlineKeyboardButton('返回↩️', callback_data=f'catejflsp {uid}:1000')]

        ]

    else:
        projectname = projectname if lang == 'zh' else get_fy(projectname)
        fstext = f'''
<b>✅You are buying: {projectname}

💰 Price: {money} USDT

🏢 Inventory: {hsl}

❗️ For unused products from our store, please purchase a small amount for testing first to avoid Cause unnecessary disputes! Thank you for your cooperation! 

❗️The account price will fluctuate according to the market price! Please understand that!</b>
            '''
        keyboard = [
            [InlineKeyboardButton('✅Buy', callback_data=f'gmqq {nowuid}:{hsl}'),
             InlineKeyboardButton('Instructions 📜', callback_data='sysming')],
            [InlineKeyboardButton('🏠Main Menu', callback_data='backzcd'),
             InlineKeyboardButton('Return ↩️', callback_data=f'catejflsp {uid}:1000')]

        ]
    query.edit_message_text(fstext, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))


def gmqq(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    lang = user.find_one({'user_id': user_id})['lang']
    data = query.data.replace('gmqq ', '')
    nowuid = data.split(':')[0]
    hsl = data.split(':')[1]

    ejfl_list = ejfl.find_one({'nowuid': nowuid})
    projectname = ejfl_list['projectname']
    money = ejfl_list['money']
    uid = ejfl_list['uid']

    user_list = user.find_one({'user_id': user_id})
    USDT = user_list['USDT']
    if USDT < money:
        fstext = f'''
❌余额不足，请立即充值
            '''
        fstext = fstext if lang == 'zh' else get_fy(fstext)
        query.answer(fstext, show_alert=bool("true"))
        return
    else:
        query.answer()
        del_message(query.message)
        fstext = f'''
<b>请输入数量：
格式：</b><code>10</code>
            '''
        fstext = fstext if lang == 'zh' else get_fy(fstext)
        user.update_one({'user_id': user_id}, {"$set": {"sign": f"gmqq {nowuid}:{hsl}"}})

        context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML')


def sysming(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    nowuid = query.data.replace('sysming ', '')
    ejfl_list = ejfl.find_one({'nowuid': nowuid})
    sysm = ejfl_list['sysm']

    keyboard = [
        [InlineKeyboardButton('关闭', callback_data=f'close {user_id}')]
    ]
    context.bot.send_message(chat_id=user_id, text=sysm, reply_markup=InlineKeyboardMarkup(keyboard))


def paixuejfl(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    uid = query.data.replace('paixuejfl ', '')
    bot_id = context.bot.id
    fl_pro = fenlei.find_one({'uid': uid})['projectname']
    keylist = list(ejfl.find({'uid': uid}, sort=[('row', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    count = []
    for i in keylist:
        projectname = i['projectname']
        row = i['row']
        nowuid = i['nowuid']
        keyboard[i["row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'fejxxi {nowuid}'))
        count.append(row)
    if count == []:
        context.bot.send_message(chat_id=user_id, text='没有按钮存在')
    else:
        maxrow = max(count)
        if maxrow == 1:
            context.bot.send_message(chat_id=user_id, text='只有一行按钮无法调整')
        else:
            for i in range(0, maxrow):
                pxuid = ejfl.find_one({'uid': uid, 'row': i + 1})['nowuid']
                if i == 0:
                    keyboard.append(
                        [InlineKeyboardButton(f'第{i + 1}行下移', callback_data=f'ejfpaixu xiayi:{i + 1}:{pxuid}')])
                elif i == maxrow - 1:
                    keyboard.append(
                        [InlineKeyboardButton(f'第{i + 1}行上移', callback_data=f'ejfpaixu shangyi:{i + 1}:{pxuid}')])
                else:
                    keyboard.append(
                        [InlineKeyboardButton(f'第{i + 1}行上移', callback_data=f'ejfpaixu shangyi:{i + 1}:{pxuid}'),
                         InlineKeyboardButton(f'第{i + 1}行下移', callback_data=f'ejfpaixu xiayi:{i + 1}:{pxuid}')])
            keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
            context.bot.send_message(chat_id=user_id, text=f'分类: {fl_pro}',
                                     reply_markup=InlineKeyboardMarkup(keyboard))


def ejfpaixu(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    qudata = query.data.replace('ejfpaixu ', '')
    qudataall = qudata.split(':')
    yidongtype = qudataall[0]
    row = int(qudataall[1])
    nowuid = qudataall[2]
    uid = ejfl.find_one({'nowuid': nowuid})['uid']
    if yidongtype == 'shangyi':
        ejfl.update_many({"row": row - 1, 'uid': uid}, {"$set": {'row': 99}})
        ejfl.update_many({"row": row, 'uid': uid}, {"$set": {'row': row - 1}})
        ejfl.update_many({"row": 99, 'uid': uid}, {"$set": {'row': row}})
    else:
        ejfl.update_many({"row": row + 1, 'uid': uid}, {"$set": {'row': 99}})
        ejfl.update_many({"row": row, 'uid': uid}, {"$set": {'row': row + 1}})
        ejfl.update_many({"row": 99, 'uid': uid}, {"$set": {'row': row}})

    fl_pro = fenlei.find_one({'uid': uid})['projectname']
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    ej_list = ejfl.find({'uid': uid})
    for i in ej_list:
        nowuid = i['nowuid']
        projectname = i['projectname']
        row = i['row']
        keyboard[row - 1].append(InlineKeyboardButton(f'{projectname}', callback_data=f'fejxxi {nowuid}'))

    keyboard.append([InlineKeyboardButton('修改分类名', callback_data=f'upspname {uid}'),
                     InlineKeyboardButton('新增二级分类', callback_data=f'newejfl {uid}')])
    keyboard.append([InlineKeyboardButton('调整二级分类排序', callback_data=f'paixuejfl {uid}'),
                     InlineKeyboardButton('删除二级分类', callback_data=f'delejfl {uid}')])
    keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
    fstext = f'''
分类: {fl_pro}
    '''
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def paixufl(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    keylist = list(fenlei.find({}, sort=[('row', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    count = []
    for i in keylist:
        projectname = i['projectname']
        row = i['row']
        uid = i['uid']
        keyboard[i["row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'flxxi {uid}'))
        count.append(row)
    if count == []:
        context.bot.send_message(chat_id=user_id, text='没有按钮存在')
    else:
        maxrow = max(count)
        if maxrow == 1:
            context.bot.send_message(chat_id=user_id, text='只有一行按钮无法调整')
        else:
            for i in range(0, maxrow):
                if i == 0:
                    keyboard.append([InlineKeyboardButton(f'第{i + 1}行下移', callback_data=f'flpxyd xiayi:{i + 1}')])
                elif i == maxrow - 1:
                    keyboard.append([InlineKeyboardButton(f'第{i + 1}行上移', callback_data=f'flpxyd shangyi:{i + 1}')])
                else:
                    keyboard.append([InlineKeyboardButton(f'第{i + 1}行上移', callback_data=f'flpxyd shangyi:{i + 1}'),
                                     InlineKeyboardButton(f'第{i + 1}行下移', callback_data=f'flpxyd xiayi:{i + 1}')])
            keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
            context.bot.send_message(chat_id=user_id, text='商品管理', reply_markup=InlineKeyboardMarkup(keyboard))


def flpxyd(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    qudata = query.data.replace('flpxyd ', '')
    qudataall = qudata.split(':')
    yidongtype = qudataall[0]
    row = int(qudataall[1])
    if yidongtype == 'shangyi':
        fenlei.update_many({"row": row - 1}, {"$set": {'row': 99}})
        fenlei.update_many({"row": row}, {"$set": {'row': row - 1}})
        fenlei.update_many({"row": 99}, {"$set": {'row': row}})
    else:
        fenlei.update_many({"row": row + 1}, {"$set": {'row': 99}})
        fenlei.update_many({"row": row}, {"$set": {'row': row + 1}})
        fenlei.update_many({"row": 99}, {"$set": {'row': row}})
    keylist = list(fenlei.find({}, sort=[('row', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for i in keylist:
        uid = i['uid']
        projectname = i['projectname']
        row = i['row']
        keyboard[row - 1].append(InlineKeyboardButton(f'{projectname}', callback_data=f'flxxi {uid}'))
    keyboard.append([InlineKeyboardButton("新建一行", callback_data='newfl'),
                     InlineKeyboardButton('调整行排序', callback_data='paixufl'),
                     InlineKeyboardButton('删除一行', callback_data='delfl')])
    context.bot.send_message(chat_id=user_id, text='商品管理', reply_markup=InlineKeyboardMarkup(keyboard))


def delejfl(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    uid = query.data.replace('delejfl ', '')
    fl_pro = fenlei.find_one({'uid': uid})['projectname']
    keylist = list(ejfl.find({'uid': uid}, sort=[('row', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    count = []
    for i in keylist:
        projectname = i['projectname']
        row = i['row']
        nowuid = i['nowuid']
        keyboard[i["row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'fejxxi {nowuid}'))
        count.append(row)
    if count == []:
        context.bot.send_message(chat_id=user_id, text='没有按钮存在')
    else:
        maxrow = max(count)
        for i in range(0, maxrow):
            pxuid = ejfl.find_one({'uid': uid, 'row': i + 1})['nowuid']
            keyboard.append([InlineKeyboardButton(f'删除第{i + 1}行', callback_data=f'qrscejrow {i + 1}:{pxuid}')])
        keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
        context.bot.send_message(chat_id=user_id, text=f'分类: {fl_pro}', reply_markup=InlineKeyboardMarkup(keyboard))


def qrscejrow(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    del_message(query.message)

    row = int(query.data.replace('qrscejrow ', '').split(':')[0])
    nowuid = query.data.replace('qrscejrow ', '').split(':')[1]
    uid = ejfl.find_one({'nowuid': nowuid})['uid']
    bot_id = context.bot.id
    ejfl.delete_many({'uid': uid, "row": row})
    max_list = list(ejfl.find({'row': {"$gt": row}}))
    for i in max_list:
        max_row = i['row']
        ejfl.update_many({'uid': uid, 'row': max_row}, {"$set": {"row": max_row - 1}})

    fl_pro = fenlei.find_one({'uid': uid})['projectname']
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    ej_list = ejfl.find({'uid': uid})
    for i in ej_list:
        nowuid = i['nowuid']
        projectname = i['projectname']
        row = i['row']
        keyboard[row - 1].append(InlineKeyboardButton(f'{projectname}', callback_data=f'fejxxi {nowuid}'))

    keyboard.append([InlineKeyboardButton('修改分类名', callback_data=f'upspname {uid}'),
                     InlineKeyboardButton('新增二级分类', callback_data=f'newejfl {uid}')])
    keyboard.append([InlineKeyboardButton('调整二级分类排序', callback_data=f'paixuejfl {uid}'),
                     InlineKeyboardButton('删除二级分类', callback_data=f'delejfl {uid}')])
    keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
    fstext = f'''
分类: {fl_pro}
    '''
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def delfl(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    bot_id = context.bot.id
    keylist = list(fenlei.find({}, sort=[('row', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    count = []
    for i in keylist:
        uid = i['uid']
        projectname = i['projectname']
        row = i['row']
        keyboard[i["row"] - 1].append(InlineKeyboardButton(projectname, callback_data=f'flxxi {uid}'))
        count.append(row)
    if count == []:
        context.bot.send_message(chat_id=user_id, text='没有按钮存在')
    else:
        maxrow = max(count)
        for i in range(0, maxrow):
            keyboard.append([InlineKeyboardButton(f'删除第{i + 1}行', callback_data=f'qrscflrow {i + 1}')])
        keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
        context.bot.send_message(chat_id=user_id, text='商品管理', reply_markup=InlineKeyboardMarkup(keyboard))


def qrscflrow(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    del_message(query.message)
    row = int(query.data.replace('qrscflrow ', ''))
    bot_id = context.bot.id
    fenlei.delete_many({"row": row})
    max_list = list(fenlei.find({'row': {"$gt": row}}))
    for i in max_list:
        max_row = i['row']
        fenlei.update_many({'row': max_row}, {"$set": {"row": max_row - 1}})
    keylist = list(fenlei.find({}, sort=[('row', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for i in keylist:
        uid = i['uid']
        projectname = i['projectname']
        row = i['row']
        keyboard[row - 1].append(InlineKeyboardButton(f'{projectname}', callback_data=f'flxxi {uid}'))
    keyboard.append([InlineKeyboardButton("新建一行", callback_data='newfl'),
                     InlineKeyboardButton('调整行排序', callback_data='paixufl'),
                     InlineKeyboardButton('删除一行', callback_data='delfl')])
    context.bot.send_message(chat_id=user_id, text='商品管理', reply_markup=InlineKeyboardMarkup(keyboard))


def backzcd(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    bot_id = context.bot.id
    user_id = query.from_user.id
    lang = user.find_one({'user_id': user_id})['lang']
    keylist = list(fenlei.find({}, sort=[('row', 1)]))
    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    for i in keylist:
        uid = i['uid']
        projectname = i['projectname']

        row = i['row']
        hsl = 0
        for j in list(ejfl.find({'uid': uid})):
            nowuid = j['nowuid']
            hsl += len(list(hb.find({'nowuid': nowuid, 'state': 0})))
        projectname = projectname if lang == 'zh' else get_fy(projectname)
        keyboard[row - 1].append(InlineKeyboardButton(f'{projectname}({hsl})', callback_data=f'catejflsp {uid}:{hsl}'))
    fstext = f'''
<b>🛒这是商品列表  选择你需要的商品：

❗️没使用过的本店商品的，请先少量购买测试，以免造成不必要的争执！谢谢合作！

❗️购买后，请立即检测账户是否正常！超过1小时视为放弃售后服务！</b>
        '''
    fstext = fstext if lang == 'zh' else get_fy(fstext)
    keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
    query.edit_message_text(fstext, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def dabaohao(context, user_id, folder_names, leixing, nowuid, erjiprojectname, fstext, yssj):
    if leixing == '协议号':
        shijiancuo = int(time.time())
        zip_filename = f"./协议号发货/{user_id}_{shijiancuo}.zip"
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            # 将每个文件及其内容添加到 zip 文件中
            for file_name in folder_names:
                # 检查是否存在以 .json 或 .session 结尾的文件
                json_file_path = os.path.join(f"./协议号/{nowuid}", file_name + ".json")
                session_file_path = os.path.join(f"./协议号/{nowuid}", file_name + ".session")
                if os.path.exists(json_file_path):
                    zipf.write(json_file_path, os.path.basename(json_file_path))
                if os.path.exists(session_file_path):
                    zipf.write(session_file_path, os.path.basename(session_file_path))
        current_time = datetime.datetime.now()

        # 将当前时间格式化为字符串
        formatted_time = current_time.strftime("%Y%m%d%H%M%S")

        # 添加时间戳
        timestamp = str(current_time.timestamp()).replace(".", "")

        # 组合编号
        bianhao = formatted_time + timestamp
        timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        goumaijilua('协议号', bianhao, user_id, erjiprojectname, zip_filename, fstext, timer)
        # 发送 zip 文件给用户
        context.bot.send_document(chat_id=user_id, document=open(zip_filename, "rb"))
    elif leixing == '直登号':
        shijiancuo = int(time.time())
        zip_filename = f"./发货/{user_id}_{shijiancuo}.zip"
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            # 将每个文件夹及其内容添加到 zip 文件中
            for folder_name in folder_names:
                full_folder_path = os.path.join(f"./号包/{nowuid}", folder_name)
                if os.path.exists(full_folder_path):
                    # 添加文件夹及其内容
                    for root, dirs, files in os.walk(full_folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # 使用相对路径在压缩包中添加文件，并设置压缩包内部的路径
                            zipf.write(file_path,
                                       os.path.join(folder_name, os.path.relpath(file_path, full_folder_path)))
                else:
                    # update.message.reply_text(f"文件夹 '{folder_name}' 不存在！")
                    pass

        # 发送 zip 文件给用户

        folder_names = '\n'.join(folder_names)

        current_time = datetime.datetime.now()

        # 将当前时间格式化为字符串
        formatted_time = current_time.strftime("%Y%m%d%H%M%S")

        # 添加时间戳
        timestamp = str(current_time.timestamp()).replace(".", "")

        # 组合编号
        bianhao = formatted_time + timestamp
        timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        goumaijilua('直登号', bianhao, user_id, erjiprojectname, zip_filename, fstext, timer)

        context.bot.send_document(chat_id=user_id, document=open(zip_filename, "rb"))


def qrgaimai(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    bot_id = context.bot.id
    user_id = query.from_user.id
    fullname = query.from_user.full_name.replace('<', '').replace('>', '')
    username = query.from_user.username
    data = query.data.replace('qrgaimai ', '')
    nowuid = data.split(':')[0]
    gmsl = int(data.split(':')[1])
    zxymoney = float(data.split(':')[2])
    user_list = user.find_one({'user_id': user_id})
    USDT = user_list['USDT']
    lang = user_list['lang']
    kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
    if kc < gmsl:
        kcbz = '当前库存不足' if lang == 'zh' else get_fy('当前库存不足')
        context.bot.send_message(chat_id=user_id, text=kcbz)
        return
    if zxymoney == 0:
        return
    keyboard = [[InlineKeyboardButton('✅已读（点击销毁此消息）', callback_data=f'close {user_id}')]]
    if USDT >= zxymoney:
        now_price = standard_num(float(USDT) - float(zxymoney))
        now_price = float(now_price) if str((now_price)).count('.') > 0 else int(standard_num(now_price))

        ejfl_list = ejfl.find_one({'nowuid': nowuid})

        fhtype = hb.find_one({'nowuid': nowuid})['leixing']
        projectname = ejfl_list['projectname']
        erjiprojectname = ejfl_list['projectname']
        yijiid = ejfl_list['uid']
        yiji_list = fenlei.find_one({'uid': yijiid})
        yijiprojectname = yiji_list['projectname']
        fstext = ejfl_list['text']
        fstext = fstext if lang == 'zh' else get_fy(fstext)
        if fhtype == '协议号':
            zgje = user_list['zgje']
            zgsl = user_list['zgsl']
            user.update_one({'user_id': user_id},
                            {"$set": {'USDT': now_price, 'zgje': zgje + zxymoney, 'zgsl': zgsl + gmsl}})
            user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
            del_message(query.message)
            # for j in list(hb.find({"nowuid": nowuid,'state': 0},limit=gmsl)):
            #     projectname = j['projectname']
            #     hbid = j['hbid']
            #     timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

            #     hb.update_one({'hbid': hbid},{"$set":{'state': 1, 'yssj': timer, 'gmid': user_id}})
            #     folder_names.append(projectname)

            query_condition = {"nowuid": nowuid, "state": 0}

            pipeline = [
                {"$match": query_condition},
                {"$limit": gmsl}
            ]
            cursor = hb.aggregate(pipeline)
            document_ids = [doc['_id'] for doc in cursor]
            cursor = hb.aggregate(pipeline)
            folder_names = [doc['projectname'] for doc in cursor]

            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            update_data = {"$set": {'state': 1, 'yssj': timer, 'gmid': user_id}}
            hb.update_many({"_id": {"$in": document_ids}}, update_data)

            # timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            # update_data = {"$set": {'state': 1, 'yssj': timer, 'gmid': user_id}}

            # hb.update_many(query_condition, update_data, limit=gmsl)

            context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML', disable_web_page_preview=True,
                                     reply_markup=InlineKeyboardMarkup(keyboard))
            fstext = f'''
用户: <a href="tg://user?id={user_id}">{fullname}</a> @{username}
用户ID: <code>{user_id}</code>
购买商品: {yijiprojectname}/{erjiprojectname}
购买数量: {gmsl}
购买金额: {zxymoney}
            '''
            for i in list(user.find({"state": '4'})):
                try:
                    context.bot.send_message(chat_id=i['user_id'], text=fstext, parse_mode='HTML')
                except:
                    pass

            Timer(1, dabaohao,
                  args=[context, user_id, folder_names, '协议号', nowuid, erjiprojectname, fstext, timer]).start()
            # shijiancuo = int(time.time())
            # zip_filename = f"./协议号发货/{user_id}_{shijiancuo}.zip"
            # with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            #     # 将每个文件及其内容添加到 zip 文件中
            #     for file_name in folder_names:
            #         # 检查是否存在以 .json 或 .session 结尾的文件
            #         json_file_path = os.path.join(f"./协议号/{nowuid}", file_name + ".json")
            #         session_file_path = os.path.join(f"./协议号/{nowuid}", file_name + ".session")
            #         if os.path.exists(json_file_path):
            #             zipf.write(json_file_path, os.path.basename(json_file_path))
            #         if os.path.exists(session_file_path):
            #             zipf.write(session_file_path, os.path.basename(session_file_path))
            # current_time = datetime.datetime.now()

            # # 将当前时间格式化为字符串
            # formatted_time = current_time.strftime("%Y%m%d%H%M%S")

            # # 添加时间戳
            # timestamp = str(current_time.timestamp()).replace(".", "")

            # # 组合编号
            # bianhao = formatted_time + timestamp
            # timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            # goumaijilua('协议号', bianhao, user_id, erjiprojectname,zip_filename,fstext, timer)
            # # 发送 zip 文件给用户
            # query.message.reply_document(open(zip_filename, "rb"))



        elif fhtype == '谷歌':
            zgje = user_list['zgje']
            zgsl = user_list['zgsl']
            user.update_one({'user_id': user_id},
                            {"$set": {'USDT': now_price, 'zgje': zgje + zxymoney, 'zgsl': zgsl + gmsl}})
            user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
            del_message(query.message)

            context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML', disable_web_page_preview=True,
                                     reply_markup=InlineKeyboardMarkup(keyboard))
            folder_names = []
            for j in list(hb.find({"nowuid": nowuid, 'state': 0, 'leixing': '谷歌'}, limit=gmsl)):
                projectname = j['projectname']
                hbid = j['hbid']
                timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                hb.update_one({'hbid': hbid}, {"$set": {'state': 1, 'yssj': timer, 'gmid': user_id}})
                data = j['data']
                us1 = data['账户']
                us2 = data['密码']
                us3 = data['子邮件']
                fste23xt = f'账户: {us1}\n密码: {us2}\n子邮件: {us3}\n'
                folder_names.append(fste23xt)

            folder_names = '\n'.join(folder_names)

            shijiancuo = int(time.time())
            zip_filename = f"./谷歌发货/{user_id}_{shijiancuo}.txt"
            with open(zip_filename, "w") as f:
                f.write(folder_names)
            current_time = datetime.datetime.now()

            # 将当前时间格式化为字符串
            formatted_time = current_time.strftime("%Y%m%d%H%M%S")

            # 添加时间戳
            timestamp = str(current_time.timestamp()).replace(".", "")

            # 组合编号
            bianhao = formatted_time + timestamp
            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            goumaijilua('谷歌', bianhao, user_id, erjiprojectname, zip_filename, fstext, timer)

            query.message.reply_document(open(zip_filename, "rb"))

            fstext = f'''
用户: <a href="tg://user?id={user_id}">{fullname}</a> @{username}
用户ID: <code>{user_id}</code>
购买商品: {yijiprojectname}/{erjiprojectname}
购买数量: {gmsl}
购买金额: {zxymoney}
            '''
            for i in list(user.find({"state": '4'})):
                try:
                    context.bot.send_message(chat_id=i['user_id'], text=fstext, parse_mode='HTML')
                except:
                    pass


        elif fhtype == 'API':
            zgje = user_list['zgje']
            zgsl = user_list['zgsl']
            user.update_one({'user_id': user_id},
                            {"$set": {'USDT': now_price, 'zgje': zgje + zxymoney, 'zgsl': zgsl + gmsl}})
            user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
            del_message(query.message)

            context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML', disable_web_page_preview=True,
                                     reply_markup=InlineKeyboardMarkup(keyboard))
            folder_names = []
            for j in list(hb.find({"nowuid": nowuid, 'state': 0}, limit=gmsl)):
                projectname = j['projectname']
                hbid = j['hbid']
                timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                hb.update_one({'hbid': hbid}, {"$set": {'state': 1, 'yssj': timer, 'gmid': user_id}})
                folder_names.append(projectname)

            shijiancuo = int(time.time())

            zip_filename = f"./手机接码发货/{user_id}_{shijiancuo}.txt"
            with open(zip_filename, "w") as f:
                for folder_name in folder_names:
                    f.write(folder_name + "\n")

            current_time = datetime.datetime.now()

            # 将当前时间格式化为字符串
            formatted_time = current_time.strftime("%Y%m%d%H%M%S")

            # 添加时间戳
            timestamp = str(current_time.timestamp()).replace(".", "")

            # 组合编号
            bianhao = formatted_time + timestamp
            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            goumaijilua('API链接', bianhao, user_id, erjiprojectname, zip_filename, fstext, timer)

            query.message.reply_document(open(zip_filename, "rb"))

            fstext = f'''
用户: <a href="tg://user?id={user_id}">{fullname}</a> @{username}
用户ID: <code>{user_id}</code>
购买商品: {yijiprojectname}/{erjiprojectname}
购买数量: {gmsl}
购买金额: {zxymoney}
            '''
            for i in list(user.find({"state": '4'})):
                try:
                    context.bot.send_message(chat_id=i['user_id'], text=fstext, parse_mode='HTML')
                except:
                    pass
        elif fhtype == '会员链接':
            zgje = user_list['zgje']
            zgsl = user_list['zgsl']
            user.update_one({'user_id': user_id},
                            {"$set": {'USDT': now_price, 'zgje': zgje + zxymoney, 'zgsl': zgsl + gmsl}})
            user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
            del_message(query.message)
            folder_names = []
            for j in list(hb.find({"nowuid": nowuid, 'state': 0}, limit=gmsl)):
                projectname = j['projectname']
                hbid = j['hbid']
                timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                hb.update_one({'hbid': hbid}, {"$set": {'state': 1, 'yssj': timer, 'gmid': user_id}})
                folder_names.append(projectname)

            context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML', disable_web_page_preview=True,
                                     reply_markup=InlineKeyboardMarkup(keyboard))

            folder_names = '\n'.join(folder_names)

            current_time = datetime.datetime.now()

            # 将当前时间格式化为字符串
            formatted_time = current_time.strftime("%Y%m%d%H%M%S")

            # 添加时间戳
            timestamp = str(current_time.timestamp()).replace(".", "")

            # 组合编号
            bianhao = formatted_time + timestamp
            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            goumaijilua('会员链接', bianhao, user_id, erjiprojectname, folder_names, fstext, timer)

            context.bot.send_message(chat_id=user_id, text=folder_names, disable_web_page_preview=True)

            fstext = f'''
用户: <a href="tg://user?id={user_id}">{fullname}</a> @{username}
用户ID: <code>{user_id}</code>
购买商品: {yijiprojectname}/{erjiprojectname}
购买数量: {gmsl}
购买金额: {zxymoney}
            '''
            for i in list(user.find({"state": '4'})):
                try:
                    context.bot.send_message(chat_id=i['user_id'], text=fstext, parse_mode='HTML')
                except:
                    pass
        else:
            zgje = user_list['zgje']
            zgsl = user_list['zgsl']
            user.update_one({'user_id': user_id},
                            {"$set": {'USDT': now_price, 'zgje': zgje + zxymoney, 'zgsl': zgsl + gmsl}})
            user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
            del_message(query.message)

            # folder_names = []
            # for j in list(hb.find({"nowuid": nowuid, 'state': 0}, limit=gmsl)):
            #     projectname = j['projectname']
            #     hbid = j['hbid']
            #     timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            #     hb.update_one({'hbid': hbid}, {"$set": {'state': 1, 'yssj': timer, 'gmid': user_id}})
            #     folder_names.append(projectname)

            query_condition = {"nowuid": nowuid, "state": 0}

            pipeline = [
                {"$match": query_condition},
                {"$limit": gmsl}
            ]
            cursor = hb.aggregate(pipeline)
            document_ids = [doc['_id'] for doc in cursor]
            cursor = hb.aggregate(pipeline)
            folder_names = [doc['projectname'] for doc in cursor]

            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            update_data = {"$set": {'state': 1, 'yssj': timer, 'gmid': user_id}}
            hb.update_many({"_id": {"$in": document_ids}}, update_data)

            context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML', disable_web_page_preview=True,
                                     reply_markup=InlineKeyboardMarkup(keyboard))

            fstext = f'''
用户: <a href="tg://user?id={user_id}">{fullname}</a> @{username}
用户ID: <code>{user_id}</code>
购买商品: {yijiprojectname}/{erjiprojectname}
购买数量: {gmsl}
购买金额: {zxymoney}
            '''
            for i in list(user.find({"state": '4'})):
                try:
                    context.bot.send_message(chat_id=i['user_id'], text=fstext, parse_mode='HTML')
                except:
                    pass

            Timer(1, dabaohao,
                  args=[context, user_id, folder_names, '直登号', nowuid, erjiprojectname, fstext, timer]).start()
            # shijiancuo = int(time.time())
            # zip_filename = f"./发货/{user_id}_{shijiancuo}.zip"
            # with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            #     # 将每个文件夹及其内容添加到 zip 文件中
            #     for folder_name in folder_names:
            #         full_folder_path = os.path.join(f"./号包/{nowuid}", folder_name)
            #         if os.path.exists(full_folder_path):
            #             # 添加文件夹及其内容
            #             for root, dirs, files in os.walk(full_folder_path):
            #                 for file in files:
            #                     file_path = os.path.join(root, file)
            #                     # 使用相对路径在压缩包中添加文件，并设置压缩包内部的路径
            #                     zipf.write(file_path, os.path.join(folder_name, os.path.relpath(file_path, full_folder_path)))
            #         else:
            #             # update.message.reply_text(f"文件夹 '{folder_name}' 不存在！")
            #             pass

            # # 发送 zip 文件给用户

            # folder_names = '\n'.join(folder_names)

            # current_time = datetime.datetime.now()

            # # 将当前时间格式化为字符串
            # formatted_time = current_time.strftime("%Y%m%d%H%M%S")

            # # 添加时间戳
            # timestamp = str(current_time.timestamp()).replace(".", "")

            # # 组合编号
            # bianhao = formatted_time + timestamp
            # timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            # goumaijilua('直登号', bianhao, user_id, erjiprojectname, zip_filename,fstext, timer)

            # query.message.reply_document(open(zip_filename, "rb"))




    else:
        if lang == 'zh':
            context.bot.send_message(chat_id=user_id, text='❌ 余额不足，请及时充值！')
            user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
        else:
            context.bot.send_message(chat_id=user_id, text='❌ Insufficient balance, please recharge in time!')
        return


def qchuall(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    bot_id = context.bot.id
    user_id = query.from_user.id

    nowuid = query.data.replace('qchuall ', '')

    ejfl_list = ejfl.find_one({'nowuid': nowuid})
    fhtype = hb.find_one({'nowuid': nowuid})['leixing']
    projectname = ejfl_list['projectname']
    yijiid = ejfl_list['uid']
    yiji_list = fenlei.find_one({'uid': yijiid})
    yijiprojectname = yiji_list['projectname']

    folder_names = []
    if fhtype == '协议号':
        for j in list(hb.find({"nowuid": nowuid, 'state': 0})):
            projectname = j['projectname']
            hbid = j['hbid']
            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            hb.delete_one({'hbid': hbid})
            folder_names.append(projectname)
        shijiancuo = int(time.time())
        zip_filename = f"./协议号发货/{user_id}_{shijiancuo}.zip"
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            # 将每个文件及其内容添加到 zip 文件中
            for file_name in folder_names:
                # 检查是否存在以 .json 或 .session 结尾的文件
                json_file_path = os.path.join(f"./协议号/{nowuid}", file_name + ".json")
                session_file_path = os.path.join(f"./协议号/{nowuid}", file_name + ".session")
                if os.path.exists(json_file_path):
                    zipf.write(json_file_path, os.path.basename(json_file_path))
                if os.path.exists(session_file_path):
                    zipf.write(session_file_path, os.path.basename(session_file_path))
        query.message.reply_document(open(zip_filename, "rb"))

    elif fhtype == 'API':
        for j in list(hb.find({"nowuid": nowuid, 'state': 0})):
            projectname = j['projectname']
            hbid = j['hbid']
            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            hb.delete_one({'hbid': hbid})
            folder_names.append(projectname)

        shijiancuo = int(time.time())

        zip_filename = f"./手机接码发货/{user_id}_{shijiancuo}.txt"
        with open(zip_filename, "w") as f:
            for folder_name in folder_names:
                f.write(folder_name + "\n")

        query.message.reply_document(open(zip_filename, "rb"))

    elif fhtype == '谷歌':
        for j in list(hb.find({"nowuid": nowuid, 'state': 0, 'leixing': '谷歌'})):
            projectname = j['projectname']
            hbid = j['hbid']
            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            hb.update_one({'hbid': hbid}, {"$set": {'state': 1, 'yssj': timer, 'gmid': user_id}})
            data = j['data']
            us1 = data['账户']
            us2 = data['密码']
            us3 = data['子邮件']
            fste23xt = f'login: {us1}\npassword: {us2}\nsubmail: {us3}\n'
            hb.delete_one({'hbid': hbid})
            folder_names.append(fste23xt)
        folder_names = '\n'.join(folder_names)
        shijiancuo = int(time.time())

        zip_filename = f"./谷歌发货/{user_id}_{shijiancuo}.txt"
        with open(zip_filename, "w") as f:

            f.write(folder_names)

        query.message.reply_document(open(zip_filename, "rb"))


    elif fhtype == '会员链接':
        for j in list(hb.find({"nowuid": nowuid, 'state': 0})):
            projectname = j['projectname']
            hbid = j['hbid']
            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            hb.delete_one({'hbid': hbid})
            folder_names.append(projectname)
        folder_names = '\n'.join(folder_names)

        context.bot.send_message(chat_id=user_id, text=folder_names, disable_web_page_preview=True)
    else:
        for j in list(hb.find({"nowuid": nowuid, 'state': 0})):
            projectname = j['projectname']
            hbid = j['hbid']
            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            hb.delete_one({'hbid': hbid})
            folder_names.append(projectname)

        shijiancuo = int(time.time())
        zip_filename = f"./发货/{user_id}_{shijiancuo}.zip"
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            # 将每个文件夹及其内容添加到 zip 文件中
            for folder_name in folder_names:
                full_folder_path = os.path.join(f"./号包/{nowuid}", folder_name)
                if os.path.exists(full_folder_path):
                    # 添加文件夹及其内容
                    for root, dirs, files in os.walk(full_folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # 使用相对路径在压缩包中添加文件，并设置压缩包内部的路径
                            zipf.write(file_path,
                                       os.path.join(folder_name, os.path.relpath(file_path, full_folder_path)))
                else:
                    # update.message.reply_text(f"文件夹 '{folder_name}' 不存在！")
                    pass

        query.message.reply_document(open(zip_filename, "rb"))

    ej_list = ejfl.find_one({'nowuid': nowuid})
    uid = ej_list['uid']
    ej_projectname = ej_list['projectname']
    money = ej_list['money']
    fl_pro = fenlei.find_one({'uid': uid})['projectname']
    keyboard = [
        [InlineKeyboardButton('取出所有库存', callback_data=f'qchuall {nowuid}'),
         InlineKeyboardButton('此商品使用说明', callback_data=f'update_sysm {nowuid}')],
        [InlineKeyboardButton('上传谷歌账户', callback_data=f'update_gg {nowuid}'),
         InlineKeyboardButton('购买此商品提示', callback_data=f'update_wbts {nowuid}')],
        [InlineKeyboardButton('上传链接', callback_data=f'update_hy {nowuid}'),
         InlineKeyboardButton('上传txt文件', callback_data=f'update_txt {nowuid}')],
        [InlineKeyboardButton('上传号包', callback_data=f'update_hb {nowuid}'),
         InlineKeyboardButton('上传协议号', callback_data=f'update_xyh {nowuid}')],
        [InlineKeyboardButton('修改二级分类名', callback_data=f'upejflname {nowuid}'),
         InlineKeyboardButton('修改价格', callback_data=f'upmoney {nowuid}')],
        [InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]
    ]
    kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
    ys = len(list(hb.find({'nowuid': nowuid, 'state': 1})))
    fstext = f'''
主分类: {fl_pro}
二级分类: {ej_projectname}

价格: {money}U
库存: {kc}
已售: {ys}
    '''
    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


def qxdingdan(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = query.message.chat
    query.answer()
    bot_id = context.bot.id
    chat_id = chat.id
    user_id = query.from_user.id

    topup.delete_one({'user_id': user_id})
    context.bot.delete_message(chat_id=query.from_user.id, message_id=query.message.message_id)


def textkeyboard(update: Update, context: CallbackContext):
    chat = update.effective_chat
    if chat.type == 'private':
        user_id = chat.id
        username = chat.username
        firstname = chat.first_name
        lastname = chat.last_name
        bot_id = context.bot.id
        fullname = chat.full_name.replace('<', '').replace('>', '')
        reply_to_message_id = update.effective_message.message_id
        timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        user_list = user.find_one({"user_id": user_id})
        creation_time = user_list['creation_time']
        state = user_list['state']
        sign = user_list['sign']
        USDT = user_list['USDT']
        zgje = user_list['zgje']
        zgsl = user_list['zgsl']
        lang = user_list['lang']
        text = update.message.text
        zxh = update.message.text_html
        yyzt = shangtext.find_one({'projectname': '营业状态'})['text']
        if yyzt == 0:
            if state != '4':
                return

        get_key_list = get_key.find({})
        get_prolist = []
        for i in get_key_list:
            get_prolist.append(i["projectname"])
        if update.message.text:
            if text in get_prolist:
                sign = 0
        if sign != 0:
            if update.message.text:

                if sign == 'addhb':
                    if is_number(text):

                        money = float(text) if text.count('.') > 0 else int(text)
                        if money < 1:
                            context.bot.send_message(chat_id=user_id, text='⚠️ 输入错误，最少金额不能小于1U')
                            return
                        if USDT >= money:
                            keyboard = [[InlineKeyboardButton('🚫取消', callback_data=f'close {user_id}')]]
                            user.update_one({'user_id': user_id}, {"$set": {'sign': f'sethbsl {money}'}})
                            context.bot.send_message(chat_id=user_id, text='<b>💡 请回复你要发送的红包数量</b>',
                                                     parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

                        else:
                            user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
                            context.bot.send_message(chat_id=user_id, text='⚠️ 操作失败，余额不足')
                    else:
                        context.bot.send_message(chat_id=user_id, text='⚠️ 输入错误，请输入数字！')
                elif 'sethbsl' in sign:
                    money = sign.replace('sethbsl ', '')
                    money = float(money) if money.count('.') > 0 else int(money)

                    if is_number(text) and text.count('.') == 0:
                        hbsl = int(text)
                        if hbsl == 0:
                            context.bot.send_message(chat_id=user_id, text='红包数量不能为0')
                            return
                        if hbsl > 100:
                            context.bot.send_message(chat_id=user_id, text='红包数量最大为100')
                            return
                        user_list = user.find_one({"user_id": user_id})
                        USDT = user_list['USDT']
                        if USDT < money:
                            user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
                            context.bot.send_message(chat_id=user_id, text='⚠️ 操作失败，余额不足')
                            return
                        user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
                        uid = generate_24bit_uid()
                        timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        hongbao.insert_one({
                            'uid': uid,
                            'user_id': user_id,
                            'fullname': fullname,
                            'hbmoney': money,
                            'hbsl': hbsl,
                            'timer': timer,
                            'state': 0
                        })
                        now_money = standard_num(USDT - money)
                        now_money = float(now_money) if str((now_money)).count('.') > 0 else int(
                            standard_num(now_money))
                        user.update_one({'user_id': user_id}, {"$set": {'USDT': now_money}})
                        fstext = f'''
🧧 <a href="tg://user?id={user_id}">{fullname}</a> 发送了一个红包
💵总金额:{money} USDT💰 剩余:{hbsl}/{hbsl}

✅ 红包添加成功，请点击按钮发送
                        '''
                        keyboard = [
                            [InlineKeyboardButton('发送红包', switch_inline_query=f'redpacket {uid}')]
                        ]

                        context.bot.send_message(chat_id=user_id, text=fstext,
                                                 reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

                    else:
                        user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
                        context.bot.send_message(chat_id=user_id, text='⚠️ 输入错误，请输入数字！')


                elif sign == 'startupdate':
                    entities = update.message.entities
                    shangtext.update_one({"projectname": '欢迎语'}, {"$set": {"text": zxh}})
                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
                    context.bot.send_message(chat_id=user_id, text=f'当前欢迎语为: {zxh}', parse_mode='HTML')
                elif 'zdycz' in sign:
                    if is_number(text):
                        del_message(update.message)
                        del_message_id = sign.replace('zdycz ', '')
                        try:
                            context.bot.deleteMessage(chat_id=user_id, message_id=del_message_id)
                        except:
                            pass
                        money = float(text)

                        topup.delete_many({'user_id': user_id})
                        timer = time.strftime('%Y%m%d', time.localtime())
                        bianhao = timer + str(int(time.time()))
                        while 1:
                            suijishu = round(random.uniform(0.01, 0.50), 2)
                            money = Decimal(str(money)) + Decimal(str(suijishu))
                            if topup.find_one({"money": float(money)}) is None:
                                break

                        timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        trc20 = shangtext.find_one({'projectname': '充值地址'})['text']
                        text = f'''
充值详情

实际支付金额：<code>{money}USDT</code>

收款地址：<code>{trc20}</code>


<b>请一定按照金额后面小数点转账，否则未到账概不负责
⚠️请在10分钟内付款，超时订单自动取消</b>
                        '''
                        text = text if lang == 'zh' else get_fy(text)
                        if lang == 'zh':
                            keyboard = [[InlineKeyboardButton('❌取消订单', callback_data=f'qxdingdan {user_id}')]]
                        else:
                            keyboard = [[InlineKeyboardButton('❌Cancel order', callback_data=f'qxdingdan {user_id}')]]

                        user.update_one({'user_id': user_id}, {"$set": {"sign": 0}})
                        message_id = context.bot.send_photo(chat_id=user_id, photo=open(f'{trc20}.png', 'rb'),
                                                            caption=text,
                                                            parse_mode='HTML',
                                                            reply_markup=InlineKeyboardMarkup(keyboard))
                        topup.insert_one(
                            {
                                'bianhao': bianhao,
                                'user_id': user_id,
                                'money': float(money),
                                'suijishu': suijishu,
                                'timer': timer,
                                'message_id': message_id.message_id
                            }
                        )

                    else:
                        keyboard = [[InlineKeyboardButton('❌取消输入', callback_data=f'close {user_id}')]]
                        context.bot.send_message(chat_id=user_id, text='请输入数字',
                                                 reply_markup=InlineKeyboardMarkup(keyboard))


                elif 'gmqq' in sign:
                    del_message(update.message)
                    data = sign.replace('gmqq ', '')
                    nowuid = data.split(':')[0]
                    del_message_id = data.split(':')[1]
                    try:
                        context.bot.deleteMessage(chat_id=user_id, message_id=del_message_id)
                    except:
                        pass

                    ejfl_list = ejfl.find_one({'nowuid': nowuid})
                    projectname = ejfl_list['projectname']
                    money = ejfl_list['money']
                    uid = ejfl_list['uid']
                    kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
                    if is_number(text):
                        gmsl = int(text)
                        zxymoney = standard_num(gmsl * money)
                        zxymoney = float(zxymoney) if str((zxymoney)).count('.') > 0 else int(standard_num(zxymoney))
                        if kc < gmsl:
                            if lang == 'zh':
                                keyboard = [[InlineKeyboardButton('❌取消购买', callback_data=f'close {user_id}')]]
                                context.bot.send_message(chat_id=user_id, text='当前库存不足【请再次输入数量】',
                                                         reply_markup=InlineKeyboardMarkup(keyboard))
                            else:
                                keyboard = [
                                    [InlineKeyboardButton('❌Cancel purchase', callback_data=f'close {user_id}')]]
                                context.bot.send_message(chat_id=user_id,
                                                         text='Current inventory is insufficient [Please enter the quantity again]',
                                                         reply_markup=InlineKeyboardMarkup(keyboard))
                            return

                        if lang == 'zh':
                            fstext = f'''
<b>✅您正在购买：{projectname}

✅ 数量{gmsl}

💰 价格{zxymoney}

💰 您的余额{USDT}</b>
                                                '''

                            keyboard = [
                                [InlineKeyboardButton('❌取消交易', callback_data=f'close {user_id}'),
                                 InlineKeyboardButton('确认购买✅',
                                                      callback_data=f'qrgaimai {nowuid}:{gmsl}:{zxymoney}')],
                                [InlineKeyboardButton('🏠主菜单', callback_data='backzcd')]

                            ]


                        else:
                            projectname = projectname if lang == 'zh' else get_fy(projectname)
                            fstext = f'''
<b>✅You are buying: {projectname}

✅ Quantity {gmsl}

💰 Price {zxymoney}

💰 Your balance {USDT}</b>
                                                '''
                            keyboard = [
                                [InlineKeyboardButton('❌Cancel transaction', callback_data=f'close {user_id}'),
                                 InlineKeyboardButton('Confirm purchase✅',
                                                      callback_data=f'qrgaimai {nowuid}:{gmsl}:{zxymoney}')],
                                [InlineKeyboardButton('🏠Main menu', callback_data='backzcd')]

                            ]
                        user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
                        context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML',
                                                 reply_markup=InlineKeyboardMarkup(keyboard))

                    else:
                        if lang == 'zh':
                            keyboard = [[InlineKeyboardButton('❌取消购买', callback_data=f'close {user_id}')]]
                            context.bot.send_message(chat_id=user_id, text='请输入数字，不购买请点击取消',
                                                     reply_markup=InlineKeyboardMarkup(keyboard))
                        # user.update_one({'user_id': user_id},{"$set":{'sign': 0}})
                        else:
                            keyboard = [[InlineKeyboardButton('❌Cancel purchase', callback_data=f'close {user_id}')]]
                            context.bot.send_message(chat_id=user_id,
                                                     text='Please enter a number. If you do not want to purchase, please click Cancel',
                                                     reply_markup=InlineKeyboardMarkup(keyboard))
                elif 'upmoney' in sign:
                    if is_number(text):
                        nowuid = sign.replace('upmoney ', '')
                        money = float(text) if text.count('.') > 0 else int(text)
                        ejfl.update_one({"nowuid": nowuid}, {"$set": {"money": money}})
                        user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})

                        ej_list = ejfl.find_one({'nowuid': nowuid})
                        uid = ej_list['uid']
                        ej_projectname = ej_list['projectname']
                        money = ej_list['money']
                        fl_pro = fenlei.find_one({'uid': uid})['projectname']
                        keyboard = [
                            [InlineKeyboardButton('取出所有库存', callback_data=f'qchuall {nowuid}'),
                             InlineKeyboardButton('此商品使用说明', callback_data=f'update_sysm {nowuid}')],
                            [InlineKeyboardButton('上传谷歌账户', callback_data=f'update_gg {nowuid}'),
                             InlineKeyboardButton('购买此商品提示', callback_data=f'update_wbts {nowuid}')],
                            [InlineKeyboardButton('上传链接', callback_data=f'update_hy {nowuid}'),
                             InlineKeyboardButton('上传txt文件', callback_data=f'update_txt {nowuid}')],
                            [InlineKeyboardButton('上传号包', callback_data=f'update_hb {nowuid}'),
                             InlineKeyboardButton('上传协议号', callback_data=f'update_xyh {nowuid}')],
                            [InlineKeyboardButton('修改二级分类名', callback_data=f'upejflname {nowuid}'),
                             InlineKeyboardButton('修改价格', callback_data=f'upmoney {nowuid}')],
                            [InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]
                        ]
                        kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
                        ys = len(list(hb.find({'nowuid': nowuid, 'state': 1})))
                        fstext = f'''
主分类: {fl_pro}
二级分类: {ej_projectname}

价格: {money}U
库存: {kc}
已售: {ys}
                        '''
                        context.bot.send_message(chat_id=user_id, text=fstext,
                                                 reply_markup=InlineKeyboardMarkup(keyboard))

                    else:
                        context.bot.send_message(chat_id=user_id, text=f'请输入数字', parse_mode='HTML')

                elif 'upejflname' in sign:
                    nowuid = sign.replace('upejflname ', '')
                    ejfl.update_one({"nowuid": nowuid}, {"$set": {"projectname": text}})
                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
                    uid = ejfl.find_one({'nowuid': nowuid})['uid']
                    fl_pro = fenlei.find_one({'uid': uid})['projectname']
                    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], []]
                    ej_list = ejfl.find({'uid': uid})
                    for i in ej_list:
                        nowuid = i['nowuid']
                        projectname = i['projectname']
                        row = i['row']
                        keyboard[row - 1].append(
                            InlineKeyboardButton(f'{projectname}', callback_data=f'fejxxi {nowuid}'))

                    keyboard.append([InlineKeyboardButton('修改分类名', callback_data=f'upspname {uid}'),
                                     InlineKeyboardButton('新增二级分类', callback_data=f'newejfl {uid}')])
                    keyboard.append([InlineKeyboardButton('调整二级分类排序', callback_data=f'paixuejfl {uid}'),
                                     InlineKeyboardButton('删除二级分类', callback_data=f'delejfl {uid}')])
                    keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
                    fstext = f'''
分类: {fl_pro}
                    '''
                    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))

                elif 'upspname' in sign:
                    uid = sign.replace('upspname ', '')
                    fenlei.update_one({"uid": uid}, {"$set": {"projectname": text}})
                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})

                    keylist = list(fenlei.find({}, sort=[('row', 1)]))
                    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], []]
                    for i in keylist:
                        uid = i['uid']
                        projectname = i['projectname']
                        row = i['row']
                        keyboard[row - 1].append(InlineKeyboardButton(f'{projectname}', callback_data=f'flxxi {uid}'))
                    keyboard.append([InlineKeyboardButton("新建一行", callback_data='newfl'),
                                     InlineKeyboardButton('调整行排序', callback_data='paixufl'),
                                     InlineKeyboardButton('删除一行', callback_data='delfl')])
                    context.bot.send_message(chat_id=user_id, text='商品管理',
                                             reply_markup=InlineKeyboardMarkup(keyboard))
                elif sign == 'settrc20':
                    shangtext.update_one({"projectname": '充值地址'}, {"$set": {"text": text}})
                    img = qrcode.make(data=text)
                    with open(f'{text}.png', 'wb') as f:
                        img.save(f)
                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
                    context.bot.send_message(chat_id=user_id, text=f'当前充值地址为: {text}', parse_mode='HTML')
                elif 'setkeyname' in sign:
                    qudata = sign.replace('setkeyname ', '')
                    qudataall = qudata.split(':')
                    row = int(qudataall[0])
                    first = int(qudataall[1])
                    get_key.update_one({'Row': row, 'first': first}, {'$set': {'projectname': text}})
                    keylist = list(get_key.find({}, sort=[('Row', 1), ('first', 1)]))
                    keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                                [], [], [], [], [], [], [], [], []]
                    for i in keylist:
                        projectname = i['projectname']
                        row = i['Row']
                        first = i['first']
                        keyboard[i["Row"] - 1].append(
                            InlineKeyboardButton(projectname, callback_data=f'keyxq {row}:{first}'))
                    keyboard.append([InlineKeyboardButton('新建一行', callback_data='newrow'),
                                     InlineKeyboardButton('删除一行', callback_data='delrow'),
                                     InlineKeyboardButton('调整行排序', callback_data='paixurow')])
                    keyboard.append([InlineKeyboardButton('修改按钮', callback_data='newkey')])
                    user.update_one({'user_id': user_id}, {"$set": {"sign": 0}})
                    context.bot.send_message(chat_id=user_id, text='自定义按钮',
                                             reply_markup=InlineKeyboardMarkup(keyboard))
                elif 'settuwenset' in sign:
                    qudata = sign.replace('settuwenset ', '')
                    qudataall = qudata.split(':')
                    row = int(qudataall[0])
                    first = int(qudataall[1])
                    entities = update.message.entities
                    get_key.update_one({'Row': row, 'first': first}, {'$set': {'text': zxh}})
                    get_key.update_one({'Row': row, 'first': first}, {'$set': {'file_id': ''}})
                    get_key.update_one({'Row': row, 'first': first}, {'$set': {'file_type': 'text'}})
                    get_key.update_one({'Row': row, 'first': first}, {'$set': {'entities': pickle.dumps(entities)}})
                    user.update_one({'user_id': user_id}, {"$set": {"sign": 0}})
                    message_id = context.bot.send_message(chat_id=user_id, text=text, entities=entities)
                    timer11 = Timer(3, del_message, args=[message_id])
                    timer11.start()
                elif 'setkeyboard' in sign:
                    qudata = sign.replace('setkeyboard ', '')
                    qudataall = qudata.split(':')
                    row = int(qudataall[0])
                    first = int(qudataall[1])
                    text = text.replace('｜', '|').replace(' ', '')
                    keyboard = parse_urls(text)
                    dumped = pickle.dumps(keyboard)
                    try:
                        message_id = context.bot.send_message(chat_id=user_id, text=f'尾随按钮设置',
                                                              reply_markup=InlineKeyboardMarkup(keyboard))
                        get_key.update_one({'Row': row, 'first': first}, {"$set": {'keyboard': dumped}})
                        get_key.update_one({'Row': row, 'first': first}, {"$set": {'key_text': text}})
                        timer11 = Timer(3, del_message, args=[message_id])
                        timer11.start()
                    except:
                        keyboard = [[InlineKeyboardButton('格式配置错误,请检查', callback_data='ddd')]]
                        message_id = context.bot.send_message(chat_id=user_id, text='格式配置错误,请检查',
                                                              reply_markup=InlineKeyboardMarkup(keyboard))
                        timer11 = Timer(3, del_message, args=[message_id])
                        timer11.start()
                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})
                elif 'update_sysm' in sign:
                    nowuid = sign.replace('update_sysm ', '')
                    uid = ejfl.find_one({'nowuid': nowuid})['uid']
                    ejfl.update_one({"nowuid": nowuid}, {"$set": {'sysm': zxh}})
                    fstext = f'''
新的使用说明为:
{zxh}
                    '''
                    context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML')
                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})

                    ej_list = ejfl.find_one({'nowuid': nowuid})
                    uid = ej_list['uid']
                    money = ej_list['money']
                    ej_projectname = ej_list['projectname']
                    fl_pro = fenlei.find_one({'uid': uid})['projectname']
                    keyboard = [
                        [InlineKeyboardButton('取出所有库存', callback_data=f'qchuall {nowuid}'),
                         InlineKeyboardButton('此商品使用说明', callback_data=f'update_sysm {nowuid}')],
                        [InlineKeyboardButton('上传谷歌账户', callback_data=f'update_gg {nowuid}'),
                         InlineKeyboardButton('购买此商品提示', callback_data=f'update_wbts {nowuid}')],
                        [InlineKeyboardButton('上传链接', callback_data=f'update_hy {nowuid}'),
                         InlineKeyboardButton('上传txt文件', callback_data=f'update_txt {nowuid}')],
                        [InlineKeyboardButton('上传号包', callback_data=f'update_hb {nowuid}'),
                         InlineKeyboardButton('上传协议号', callback_data=f'update_xyh {nowuid}')],
                        [InlineKeyboardButton('修改二级分类名', callback_data=f'upejflname {nowuid}'),
                         InlineKeyboardButton('修改价格', callback_data=f'upmoney {nowuid}')],
                        [InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]
                    ]
                    kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
                    ys = len(list(hb.find({'nowuid': nowuid, 'state': 1})))
                    fstext = f'''
主分类: {fl_pro}
二级分类: {ej_projectname}

价格: {money}U
库存: {kc}
已售: {ys}
                    '''
                    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))
                elif 'update_wbts' in sign:
                    nowuid = sign.replace('update_wbts ', '')
                    uid = ejfl.find_one({'nowuid': nowuid})['uid']
                    ejfl.update_one({"nowuid": nowuid}, {"$set": {'text': zxh}})
                    fstext = f'''
新的提示为:
{zxh}
                    '''
                    context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML')
                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})

                    ej_list = ejfl.find_one({'nowuid': nowuid})
                    uid = ej_list['uid']
                    money = ej_list['money']
                    ej_projectname = ej_list['projectname']
                    fl_pro = fenlei.find_one({'uid': uid})['projectname']
                    keyboard = [
                        [InlineKeyboardButton('取出所有库存', callback_data=f'qchuall {nowuid}'),
                         InlineKeyboardButton('此商品使用说明', callback_data=f'update_sysm {nowuid}')],
                        [InlineKeyboardButton('上传谷歌账户', callback_data=f'update_gg {nowuid}'),
                         InlineKeyboardButton('购买此商品提示', callback_data=f'update_wbts {nowuid}')],
                        [InlineKeyboardButton('上传链接', callback_data=f'update_hy {nowuid}'),
                         InlineKeyboardButton('上传txt文件', callback_data=f'update_txt {nowuid}')],
                        [InlineKeyboardButton('上传号包', callback_data=f'update_hb {nowuid}'),
                         InlineKeyboardButton('上传协议号', callback_data=f'update_xyh {nowuid}')],
                        [InlineKeyboardButton('修改二级分类名', callback_data=f'upejflname {nowuid}'),
                         InlineKeyboardButton('修改价格', callback_data=f'upmoney {nowuid}')],
                        [InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]
                    ]
                    kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
                    ys = len(list(hb.find({'nowuid': nowuid, 'state': 1})))
                    fstext = f'''
主分类: {fl_pro}
二级分类: {ej_projectname}

价格: {money}U
库存: {kc}
已售: {ys}
                    '''
                    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


                elif 'update_hy' in sign:
                    nowuid = sign.replace('update_hy ', '')
                    uid = ejfl.find_one({'nowuid': nowuid})['uid']

                    text = text.split('\n')
                    count = 0
                    for i in text:
                        if 'https:' in i:
                            if hb.find_one({'nowuid': nowuid, 'projectname': i}) is None:
                                hbid = generate_24bit_uid()
                                shangchuanhaobao('会员链接', uid, nowuid, hbid, i, timer)
                                count += 1

                    update.message.reply_text(f'本次上传了{count}个链接')
                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})

                    ej_list = ejfl.find_one({'nowuid': nowuid})
                    uid = ej_list['uid']
                    money = ej_list['money']
                    ej_projectname = ej_list['projectname']
                    fl_pro = fenlei.find_one({'uid': uid})['projectname']
                    keyboard = [
                        [InlineKeyboardButton('取出所有库存', callback_data=f'qchuall {nowuid}'),
                         InlineKeyboardButton('此商品使用说明', callback_data=f'update_sysm {nowuid}')],
                        [InlineKeyboardButton('上传谷歌账户', callback_data=f'update_gg {nowuid}'),
                         InlineKeyboardButton('购买此商品提示', callback_data=f'update_wbts {nowuid}')],
                        [InlineKeyboardButton('上传链接', callback_data=f'update_hy {nowuid}'),
                         InlineKeyboardButton('上传txt文件', callback_data=f'update_txt {nowuid}')],
                        [InlineKeyboardButton('上传号包', callback_data=f'update_hb {nowuid}'),
                         InlineKeyboardButton('上传协议号', callback_data=f'update_xyh {nowuid}')],
                        [InlineKeyboardButton('修改二级分类名', callback_data=f'upejflname {nowuid}'),
                         InlineKeyboardButton('修改价格', callback_data=f'upmoney {nowuid}')],
                        [InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]
                    ]
                    kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
                    ys = len(list(hb.find({'nowuid': nowuid, 'state': 1})))
                    fstext = f'''
主分类: {fl_pro}
二级分类: {ej_projectname}

价格: {money}U
库存: {kc}
已售: {ys}
                    '''
                    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))

            elif update.message.document:
                if 'update_hb' in sign:
                    nowuid = sign.replace('update_hb ', '')
                    uid = ejfl.find_one({'nowuid': nowuid})['uid']

                    file = update.message.document
                    # 获取文件名
                    filename = file.file_name

                    # 获取文件ID
                    file_id = file.file_id
                    # 下载文件
                    new_file = context.bot.get_file(file_id)
                    # 将文件保存到本地
                    new_file_path = f'./临时文件夹/{filename}'
                    new_file.download(new_file_path)

                    context.bot.send_message(chat_id=user_id, text='上传中，请勿重复操作')
                    # 解压缩文件
                    count = 0
                    timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    with zipfile.ZipFile(new_file_path, 'r') as zip_ref:
                        for file_info in zip_ref.infolist():
                            match = re.match(r'^([^/]+)/.*$', file_info.filename)
                            if match:
                                extracted_folder_name = match.group(1)

                                if hb.find_one({'nowuid': nowuid, 'projectname': extracted_folder_name}) is None:
                                    count += 1
                                    hbid = generate_24bit_uid()
                                    shangchuanhaobao('直登号', uid, nowuid, hbid, extracted_folder_name, timer)
                            zip_ref.extract(file_info, f'号包/{nowuid}')

                    update.message.reply_text(f'解压并处理完成！本次上传了{count}个号')
                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})

                    ej_list = ejfl.find_one({'nowuid': nowuid})
                    uid = ej_list['uid']
                    money = ej_list['money']
                    ej_projectname = ej_list['projectname']
                    fl_pro = fenlei.find_one({'uid': uid})['projectname']
                    keyboard = [
                        [InlineKeyboardButton('取出所有库存', callback_data=f'qchuall {nowuid}'),
                         InlineKeyboardButton('此商品使用说明', callback_data=f'update_sysm {nowuid}')],
                        [InlineKeyboardButton('上传谷歌账户', callback_data=f'update_gg {nowuid}'),
                         InlineKeyboardButton('购买此商品提示', callback_data=f'update_wbts {nowuid}')],
                        [InlineKeyboardButton('上传链接', callback_data=f'update_hy {nowuid}'),
                         InlineKeyboardButton('上传txt文件', callback_data=f'update_txt {nowuid}')],
                        [InlineKeyboardButton('上传号包', callback_data=f'update_hb {nowuid}'),
                         InlineKeyboardButton('上传协议号', callback_data=f'update_xyh {nowuid}')],
                        [InlineKeyboardButton('修改二级分类名', callback_data=f'upejflname {nowuid}'),
                         InlineKeyboardButton('修改价格', callback_data=f'upmoney {nowuid}')],
                        [InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]
                    ]
                    kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
                    ys = len(list(hb.find({'nowuid': nowuid, 'state': 1})))
                    fstext = f'''
主分类: {fl_pro}
二级分类: {ej_projectname}

价格: {money}U
库存: {kc}
已售: {ys}
                    '''
                    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))

                elif 'update_gg' in sign:
                    nowuid = sign.replace('update_gg ', '')
                    uid = ejfl.find_one({'nowuid': nowuid})['uid']

                    file = update.message.document
                    # 获取文件名
                    filename = file.file_name

                    # 获取文件ID
                    file_id = file.file_id
                    # 下载文件
                    new_file = context.bot.get_file(file_id)
                    # 将文件保存到本地
                    new_file_path = f'./临时文件夹/{filename}'
                    new_file.download(new_file_path)

                    context.bot.send_message(chat_id=user_id, text='上传中，请勿重复操作')

                    with open(new_file_path, 'r', encoding='utf-8') as file:
                        link_list = file.read()

                    login = re.findall('login: (.*)', link_list)
                    password = re.findall('password: (.*)', link_list)
                    submail = re.findall('submail: (.*)', link_list)
                    # 将匹配结果打包成元组列表
                    matches = list(zip(login, password, submail))

                    timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    count = 0
                    for i in matches:
                        login = i[0]
                        password = i[1]
                        submail = i[2]
                        jihe12 = {'账户': login, '密码': password, '子邮件': submail}
                        if hb.find_one({'nowuid': nowuid, 'projectname': login}) is None:
                            hbid = generate_24bit_uid()
                            shangchuanhaobao('谷歌', uid, nowuid, hbid, login, timer)
                            hb.update_one({'hbid': hbid}, {"$set": {"leixing": '谷歌', 'data': jihe12}})
                            count += 1

                    update.message.reply_text(f'处理完成！本次上传了{count}个谷歌号')
                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})

                    ej_list = ejfl.find_one({'nowuid': nowuid})
                    uid = ej_list['uid']
                    money = ej_list['money']
                    ej_projectname = ej_list['projectname']
                    fl_pro = fenlei.find_one({'uid': uid})['projectname']
                    keyboard = [
                        [InlineKeyboardButton('取出所有库存', callback_data=f'qchuall {nowuid}'),
                         InlineKeyboardButton('此商品使用说明', callback_data=f'update_sysm {nowuid}')],
                        [InlineKeyboardButton('上传谷歌账户', callback_data=f'update_gg {nowuid}'),
                         InlineKeyboardButton('购买此商品提示', callback_data=f'update_wbts {nowuid}')],
                        [InlineKeyboardButton('上传链接', callback_data=f'update_hy {nowuid}'),
                         InlineKeyboardButton('上传txt文件', callback_data=f'update_txt {nowuid}')],
                        [InlineKeyboardButton('上传号包', callback_data=f'update_hb {nowuid}'),
                         InlineKeyboardButton('上传协议号', callback_data=f'update_xyh {nowuid}')],
                        [InlineKeyboardButton('修改二级分类名', callback_data=f'upejflname {nowuid}'),
                         InlineKeyboardButton('修改价格', callback_data=f'upmoney {nowuid}')],
                        [InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]
                    ]
                    kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
                    ys = len(list(hb.find({'nowuid': nowuid, 'state': 1})))
                    fstext = f'''
主分类: {fl_pro}
二级分类: {ej_projectname}

价格: {money}U
库存: {kc}
已售: {ys}
                    '''
                    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))

                elif 'update_txt' in sign:
                    nowuid = sign.replace('update_txt ', '')
                    uid = ejfl.find_one({'nowuid': nowuid})['uid']

                    file = update.message.document
                    # 获取文件名
                    filename = file.file_name

                    # 获取文件ID
                    file_id = file.file_id
                    # 下载文件
                    new_file = context.bot.get_file(file_id)
                    # 将文件保存到本地
                    new_file_path = f'./临时文件夹/{filename}'
                    new_file.download(new_file_path)

                    context.bot.send_message(chat_id=user_id, text='上传中，请勿重复操作')

                    link_list = []
                    with open(new_file_path, 'r', encoding='utf-8') as file:
                        # 逐行读取文件内容
                        for line in file:
                            # 去除每行末尾的换行符并添加到列表中
                            link_list.append(line.strip())
                    timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    count = 0
                    for i in link_list:
                        if hb.find_one({'nowuid': nowuid, 'projectname': i}) is None:
                            hbid = generate_24bit_uid()
                            shangchuanhaobao('API', uid, nowuid, hbid, i, timer)
                            count += 1

                    update.message.reply_text(f'处理完成！本次上传了{count}个api链接')
                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})

                    ej_list = ejfl.find_one({'nowuid': nowuid})
                    uid = ej_list['uid']
                    money = ej_list['money']
                    ej_projectname = ej_list['projectname']
                    fl_pro = fenlei.find_one({'uid': uid})['projectname']
                    keyboard = [
                        [InlineKeyboardButton('取出所有库存', callback_data=f'qchuall {nowuid}'),
                         InlineKeyboardButton('此商品使用说明', callback_data=f'update_sysm {nowuid}')],
                        [InlineKeyboardButton('上传谷歌账户', callback_data=f'update_gg {nowuid}'),
                         InlineKeyboardButton('购买此商品提示', callback_data=f'update_wbts {nowuid}')],
                        [InlineKeyboardButton('上传链接', callback_data=f'update_hy {nowuid}'),
                         InlineKeyboardButton('上传txt文件', callback_data=f'update_txt {nowuid}')],
                        [InlineKeyboardButton('上传号包', callback_data=f'update_hb {nowuid}'),
                         InlineKeyboardButton('上传协议号', callback_data=f'update_xyh {nowuid}')],
                        [InlineKeyboardButton('修改二级分类名', callback_data=f'upejflname {nowuid}'),
                         InlineKeyboardButton('修改价格', callback_data=f'upmoney {nowuid}')],
                        [InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]
                    ]
                    kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
                    ys = len(list(hb.find({'nowuid': nowuid, 'state': 1})))
                    fstext = f'''
主分类: {fl_pro}
二级分类: {ej_projectname}

价格: {money}U
库存: {kc}
已售: {ys}
                    '''
                    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))
                elif 'update_xyh' in sign:
                    nowuid = sign.replace('update_xyh ', '')
                    uid = ejfl.find_one({'nowuid': nowuid})['uid']

                    file = update.message.document
                    # 获取文件名
                    filename = file.file_name

                    # 获取文件ID
                    file_id = file.file_id
                    # 下载文件
                    new_file = context.bot.get_file(file_id)
                    # 将文件保存到本地
                    new_file_path = f'./临时文件夹/{filename}'
                    new_file.download(new_file_path)

                    context.bot.send_message(chat_id=user_id, text='上传中，请勿重复操作')
                    # 解压缩文件
                    count = 0
                    tj_dict = {}
                    timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    with zipfile.ZipFile(new_file_path, 'r') as zip_ref:
                        for file_info in zip_ref.infolist():
                            filename = file_info.filename
                            if filename.endswith('.json') or filename.endswith('.session'):
                                # 仅解压 session 或者 json 格式的文件
                                fli1 = filename.replace('.json', '').replace('.session', '')
                                if fli1 not in tj_dict.keys():

                                    hbid = generate_24bit_uid()
                                    if hb.find_one({'nowuid': nowuid, 'projectname': fli1}) is None:
                                        tj_dict[fli1] = 1
                                        shangchuanhaobao('协议号', uid, nowuid, hbid, fli1, timer)

                                zip_ref.extract(member=file_info, path=f'协议号/{nowuid}')
                                pass
                            else:
                                pass
                    for i in tj_dict:
                        count += 1

                    update.message.reply_text(f'解压并处理完成！本次上传了{count}个协议号')

                    user.update_one({'user_id': user_id}, {"$set": {'sign': 0}})

                    ej_list = ejfl.find_one({'nowuid': nowuid})
                    uid = ej_list['uid']
                    money = ej_list['money']
                    ej_projectname = ej_list['projectname']
                    fl_pro = fenlei.find_one({'uid': uid})['projectname']
                    keyboard = [
                        [InlineKeyboardButton('取出所有库存', callback_data=f'qchuall {nowuid}'),
                         InlineKeyboardButton('此商品使用说明', callback_data=f'update_sysm {nowuid}')],
                        [InlineKeyboardButton('上传谷歌账户', callback_data=f'update_gg {nowuid}'),
                         InlineKeyboardButton('购买此商品提示', callback_data=f'update_wbts {nowuid}')],
                        [InlineKeyboardButton('上传链接', callback_data=f'update_hy {nowuid}'),
                         InlineKeyboardButton('上传txt文件', callback_data=f'update_txt {nowuid}')],
                        [InlineKeyboardButton('上传号包', callback_data=f'update_hb {nowuid}'),
                         InlineKeyboardButton('上传协议号', callback_data=f'update_xyh {nowuid}')],
                        [InlineKeyboardButton('修改二级分类名', callback_data=f'upejflname {nowuid}'),
                         InlineKeyboardButton('修改价格', callback_data=f'upmoney {nowuid}')],
                        [InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')]
                    ]
                    kc = len(list(hb.find({'nowuid': nowuid, 'state': 0})))
                    ys = len(list(hb.find({'nowuid': nowuid, 'state': 1})))
                    fstext = f'''
主分类: {fl_pro}
二级分类: {ej_projectname}

价格: {money}U
库存: {kc}
已售: {ys}
                    '''
                    context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))

            else:
                caption = update.message.caption
                entities = update.message.caption_entities

                if 'settuwenset' in sign:
                    qudata = sign.replace('settuwenset ', '')
                    qudataall = qudata.split(':')
                    row = int(qudataall[0])
                    first = int(qudataall[1])
                    if update.message.photo:
                        file = update.message.photo[-1].file_id
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'text': caption}})
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'file_id': file}})
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'file_type': 'photo'}})
                        user.update_one({'user_id': user_id}, {"$set": {"sign": 0}})
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'entities': pickle.dumps(entities)}})
                        message_id = context.bot.send_photo(chat_id=user_id, caption=caption, photo=file,
                                                            caption_entities=entities)
                        timer11 = Timer(3, del_message, args=[message_id])
                        timer11.start()
                    elif update.message.animation:
                        file = update.message.animation.file_id
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'text': caption}})
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'file_id': file}})
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'file_type': 'animation'}})
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'state': 1}})
                        user.update_one({'user_id': user_id}, {"$set": {"sign": 0}})
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'entities': pickle.dumps(entities)}})
                        message_id = context.bot.sendAnimation(chat_id=user_id, caption=caption, animation=file,
                                                               caption_entities=entities)
                        timer11 = Timer(3, del_message, args=[message_id])
                        timer11.start()
                    else:
                        file = update.message.video.file_id
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'text': caption}})
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'file_id': file}})
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'file_type': 'video'}})
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'state': 1}})
                        user.update_one({'user_id': user_id}, {"$set": {"sign": 0}})
                        get_key.update_one({'Row': row, 'first': first}, {'$set': {'entities': pickle.dumps(entities)}})
                        message_id = context.bot.sendVideo(chat_id=user_id, caption=caption, video=file,
                                                           caption_entities=entities)
                        timer11 = Timer(3, del_message, args=[message_id])
                        timer11.start()
        else:
            if text == '开始营业':
                if state == '4':
                    shangtext.update_one({'projectname': '营业状态'}, {"$set": {"text": 1}})
                    context.bot.send_message(chat_id=user_id, text='开始营业')
            elif text == '停止营业':
                if state == '4':
                    shangtext.update_one({'projectname': '营业状态'}, {"$set": {"text": 0}})
                    context.bot.send_message(chat_id=user_id, text='停止营业')

            grzx = get_key.find_one({'projectname': {"$regex": "中心"}})['projectname'] if lang == 'zh' else \
            fyb.find_one({'text': {"$regex": "中心"}})['fanyi']
            wycz = get_key.find_one({'projectname': {"$regex": "充值"}})['projectname'] if lang == 'zh' else \
            fyb.find_one({'text': {"$regex": "充值"}})['fanyi']
            splb = get_key.find_one({'projectname': {"$regex": "列表"}})['projectname'] if lang == 'zh' else \
            fyb.find_one({'text': {"$regex": "列表"}})['fanyi']
            fhb = get_key.find_one({'projectname': {"$regex": "红包"}})['projectname'] if lang == 'zh' else \
            fyb.find_one({'text': {"$regex": "红包"}})['fanyi']
            key_list = get_key.find_one({"projectname": text})
            if text == grzx:
                del_message(update.message)
                if username is None:
                    username = fullname
                else:
                    username = f'<a href="https://t.me/{username}">{username}</a>'
                if lang == 'zh':
                    fstext = f'''
<b>您的ID:</b>  <code>{user_id}</code>
<b>您的用户名:</b>  {username} 
<b>注册日期:</b>  {creation_time}

<b>总购数量:</b>  {zgsl}

<b>总购金额:</b>  {standard_num(zgje)} USDT

<b>您的余额:</b>  {USDT} USDT
                                '''

                    keyboard = [[InlineKeyboardButton('🛒购买记录', callback_data=f'gmaijilu {user_id}')]]
                else:
                    fstext = f'''
<b>Your ID:</b>  <code>{user_id}</code>
<b>username:</b>  {username} 
<b>Registration date:</b>  {creation_time}

<b>Total purchase quantity:</b>  {zgsl}

<b>Total purchase amount:</b>  {standard_num(zgje)} USDT

<b> balance:</b>  {USDT} USDT
                                '''
                    keyboard = [[InlineKeyboardButton('🛒Purchase history', callback_data=f'gmaijilu {user_id}')]]

                context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML',
                                         reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

            elif text == '中文服务':
                del_message(update.message)
                user.update_one({'user_id': user_id}, {"$set": {'lang': 'zh'}})
                keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                            [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                            [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                            [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                            [], [], [], [], []]
                lang = 'zh'
                keylist = get_key.find({}, sort=[('Row', 1), ('first', 1)])
                for i in keylist:
                    projectname = i['projectname']
                    if projectname == '中文服务':
                        pass
                    else:
                        projectname = projectname if lang == 'zh' else get_fy(projectname)
                    row = i['Row']
                    first = i['first']
                    keyboard[i["Row"] - 1].append(KeyboardButton(projectname))

                context.bot.send_message(chat_id=user_id, text='语言切换成功',
                                         reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True,
                                                                          one_time_keyboard=False), parse_mode='HTML')

            elif text == 'English':
                del_message(update.message)
                user.update_one({'user_id': user_id}, {"$set": {'lang': 'en'}})
                lang = 'en'
                keyboard = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                            [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                            [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                            [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                            [], [], [], [], []]
                keylist = get_key.find({}, sort=[('Row', 1), ('first', 1)])
                for i in keylist:
                    projectname = i['projectname']
                    if projectname == '中文服务':
                        pass
                    else:
                        projectname = projectname if lang == 'zh' else get_fy(projectname)
                    row = i['Row']
                    first = i['first']
                    keyboard[i["Row"] - 1].append(KeyboardButton(projectname))

                context.bot.send_message(chat_id=user_id, text='Language switch successful',
                                         reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True,
                                                                          one_time_keyboard=False), parse_mode='HTML')
            elif text == wycz:
                del_message(update.message)
                fstext = f'''
<b>💰请选择下面充值订单金额

💹请严格按照小数点转账‼️</b>
                                '''
                fstext = fstext if lang == 'zh' else get_fy(fstext)
                if lang == 'zh':
                    keyboard = [
                        [InlineKeyboardButton('10USDT', callback_data='yuecz 10'),
                         InlineKeyboardButton('30USDT', callback_data='yuecz 30'),
                         InlineKeyboardButton('50USDT', callback_data='yuecz 50')],
                        [InlineKeyboardButton('100USDT', callback_data='yuecz 100'),
                         InlineKeyboardButton('200USDT', callback_data='yuecz 200'),
                         InlineKeyboardButton('500USDT', callback_data='yuecz 500')],
                        [InlineKeyboardButton('1000USDT', callback_data='yuecz 1000'),
                         InlineKeyboardButton('1500USDT', callback_data='yuecz 1500'),
                         InlineKeyboardButton('2000USDT', callback_data='yuecz 2000')],
                        [InlineKeyboardButton('自定义充值金额', callback_data='zdycz')],
                        [InlineKeyboardButton('取消充值', callback_data=f'close {user_id}')]
                    ]
                else:
                    keyboard = [
                        [InlineKeyboardButton('10USDT', callback_data='yuecz 10'),
                         InlineKeyboardButton('30USDT', callback_data='yuecz 30'),
                         InlineKeyboardButton('50USDT', callback_data='yuecz 50')],
                        [InlineKeyboardButton('100USDT', callback_data='yuecz 100'),
                         InlineKeyboardButton('200USDT', callback_data='yuecz 200'),
                         InlineKeyboardButton('500USDT', callback_data='yuecz 500')],
                        [InlineKeyboardButton('1000USDT', callback_data='yuecz 1000'),
                         InlineKeyboardButton('1500USDT', callback_data='yuecz 1500'),
                         InlineKeyboardButton('2000USDT', callback_data='yuecz 2000')],
                        [InlineKeyboardButton('Customize recharge amount', callback_data='zdycz')],
                        [InlineKeyboardButton('Cancel recharge', callback_data=f'close {user_id}')]
                    ]
                context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML',
                                         reply_markup=InlineKeyboardMarkup(keyboard))

            elif text == fhb:
                del_message(update.message)
                fstext = f'''
从下面的列表中选择一个红包
                '''
                # fstext = fstext if lang == 'zh' else get_fy(fstext)
                # if lang == 'zh':

                keyboard = [
                    [InlineKeyboardButton('◾️进行中', callback_data='jxzhb'),
                     InlineKeyboardButton('已结束', callback_data='yjshb')],
                    [InlineKeyboardButton('➕添加', callback_data='addhb')],
                    [InlineKeyboardButton('关闭', callback_data=f'close {user_id}')]
                ]
                # else:
                #     keyboard = [
                #         [InlineKeyboardButton('◾️ in progress', callback_data='jxzhb'),
                #          InlineKeyboardButton(' finished', callback_data='yjshb')],
                #         [InlineKeyboardButton('➕ add', callback_data='addhb')],
                #         [InlineKeyboardButton(' close', callback_data=f'close {user_id}')]
                #     ]
                context.bot.send_message(chat_id=user_id, text=fstext, reply_markup=InlineKeyboardMarkup(keyboard))


            elif text == splb:
                del_message(update.message)
                fenlei_data = list(fenlei.find({}, sort=[('row', 1)]))
                ejfl_data = list(ejfl.find({}))
                hb_data = list(hb.find({'state': 0}))

                keyboard = [[] for _ in range(50)]  # 创建一个空的键盘列表

                for i in fenlei_data:
                    uid = i['uid']
                    projectname = i['projectname']
                    row = i['row']

                    hsl = sum(1 for j in ejfl_data if j['uid'] == uid for hb_item in hb_data if
                              hb_item['nowuid'] == j['nowuid'])

                    projectname = projectname if lang == 'zh' else get_fy(projectname)
                    keyboard[row - 1].append(
                        InlineKeyboardButton(f'{projectname}({hsl})', callback_data=f'catejflsp {uid}:{hsl}'))
                fstext = f'''
<b>🛒这是商品列表  选择你需要的商品：

❗️没使用过的本店商品的，请先少量购买测试，以免造成不必要的争执！谢谢合作！

❗️购买后，请立即检测账户是否正常！超过1小时视为放弃售后服务！</b>
                                '''
                fstext = fstext if lang == 'zh' else get_fy(fstext)
                keyboard.append([InlineKeyboardButton('❌关闭', callback_data=f'close {user_id}')])
                context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML',
                                         reply_markup=InlineKeyboardMarkup(keyboard))

            else:
                if lang == 'en':
                    text = fyb.find_one({'fanyi': text})['text']
                key_list = get_key.find_one({"projectname": text})
                if key_list != None:
                    key_text = key_list['key_text']
                    print_text = key_list['text']

                    print_text = print_text if lang == 'zh' else get_fy(print_text)
                    file_type = key_list['file_type']
                    file_id = key_list['file_id']
                    entities = pickle.loads(key_list['entities'])
                    keyboard = pickle.loads(key_list['keyboard'])
                    if context.bot.username in ['TelergamKFbot', 'Tclelgnam_bot']:
                        pass
                    else:
                        if print_text == '' and file_id == '':
                            context.bot.send_message(chat_id=user_id, text=text)
                        else:
                            if file_type == 'text':
                                message_id = context.bot.send_message(chat_id=user_id, text=print_text,
                                                                      reply_markup=InlineKeyboardMarkup(keyboard),
                                                                      parse_mode='HTML')
                            else:
                                if file_type == 'photo':
                                    message_id = context.bot.send_photo(chat_id=user_id, caption=print_text,
                                                                        photo=file_id,
                                                                        reply_markup=InlineKeyboardMarkup(keyboard),
                                                                        parse_mode='HTML')
                                else:
                                    message_id = context.bot.sendAnimation(chat_id=user_id, caption=print_text,
                                                                           animation=file_id,
                                                                           reply_markup=InlineKeyboardMarkup(keyboard),
                                                                           parse_mode='HTML')


def del_message(message):
    try:
        message.delete()
    except:
        pass


def standard_num(num):
    value = Decimal(str(num)).quantize(Decimal("0.01"))
    return value.to_integral() if value == value.to_integral() else value.normalize()


def jiexi(context: CallbackContext):
    trc20 = shangtext.find_one({'projectname': '充值地址'})['text']
    qukuai_list = qukuai.find({'state': 0, 'to_address': trc20})
    for i in qukuai_list:
        txid = i['txid']
        quant = i['quant']
        from_address = i['from_address']
        quant123 = Decimal(quant) / Decimal('1000000')
        quant = abs(float(quant123))
        today_money = quant
        dj_list = topup.find_one({"money": quant})
        if dj_list is not None:
            message_id = dj_list['message_id']
            user_id = dj_list['user_id']
            user_list = user.find_one({'user_id': user_id})
            user_id = user_list['user_id']
            USDT = user_list['USDT']

            now_price = standard_num(float(USDT) + float(quant))
            now_price = float(now_price) if str((now_price)).count('.') > 0 else int(standard_num(now_price))
            keyboard = [[InlineKeyboardButton("✅已读（点击销毁此消息）", callback_data=f'close {user_id}')]]
            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            order_id = str(uuid.uuid4())

            user_logging(order_id, '充值', user_id, today_money, timer)
            us_list = user.find_one({"user_id": user_id})
            user.update_one({'user_id': user_id}, {"$set": {'USDT': now_price}})
            text = f'''
🎉恭喜您，成功充值💰{today_money}U，祝您一切顺利！ 🥳💫
            '''

            context.bot.send_message(chat_id=user_id, text=text, parse_mode='HTML')
            us_firstname = us_list['fullname'].replace('<', '').replace('>', '')
            us_username = us_list['username']
            text = f'''
用户: <a href="tg://user?id={user_id}">{us_firstname}</a> @{us_username} 充值成功
地址: <code>{from_address}</code>
充值: {today_money} USDT
<a href="https://tronscan.org/#/transaction/{txid}">充值详细</a>
            '''
            for us in list(user.find({'state': '4'})):
                try:
                    context.bot.send_message(chat_id=us['user_id'], text=text, parse_mode='HTML',
                                             disable_web_page_preview=True)
                except:
                    continue
            topup.delete_one({'user_id': user_id})
            qukuai.update_one({'txid': txid}, {"$set": {"state": 1}})
        else:
            qukuai.update_one({'txid': txid}, {"$set": {"state": 2}})


def jianceguoqi(context: CallbackContext):
    while 1:
        for i in topup.find({}):
            timer = i['timer']
            bianhao = i['bianhao']
            user_id = i['user_id']
            message_id = i['message_id']
            dt = datetime.datetime.strptime(timer, '%Y-%m-%d %H:%M:%S')

            # 加上5分钟
            new_dt = dt + timedelta(minutes=10)

            # 将新的 datetime 对象转换回时间字符串
            new_time_str = new_dt.strftime('%Y-%m-%d %H:%M:%S')

            keyboard = [[InlineKeyboardButton("✅已读（点击销毁此消息）", callback_data=f'close {user_id}')]]

            timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            if timer >= new_time_str:
                try:
                    # context.bot.send_message(chat_id=user_id,text=f'❌ 订单支付超时(或金额错误)')
                    context.bot.edit_message_caption(chat_id=user_id, message_id=message_id,
                                                     caption='❌ 订单支付超时(或金额错误)')
                    # context.bot.edit_message_media(chat_id=user_id, message_id=message_id, media=InputMediaPhoto(
                    #     media='AgACAgQAAxkDAAJ_4mZfL-22cVYZqxzbYdiJJk9tFP7zAALOwDEbwAv4Um-tzSgu40aMAQADAgADeQADNQQ',
                    #     caption='❌ 订单支付超时(或金额错误)'), reply_markup=InlineKeyboardMarkup(keyboard))

                except:
                    pass
                topup.delete_one({'user_id': user_id})
        time.sleep(3)


def suoyouchengxu(context: CallbackContext):
    Timer(1, jianceguoqi, args=[context]).start()

    job = context.job_queue.get_jobs_by_name('suoyouchengxu')
    if job != ():
        job[0].schedule_removal()


def fbgg(update: Update, context: CallbackContext):
    chat = update.effective_chat
    # print(chat)
    if chat.type == 'private':
        user_id = chat['id']
        chat_id = user_id
        username = chat['username']
        firstname = chat['first_name']
        fullname = chat['full_name']
        timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        lastname = chat['last_name']
        text = update.message.text
        user_list = user.find_one({'user_id': user_id})
        USDT = user_list['USDT']
        state = user_list['state']
        if state == '4':

            context.bot.send_message(chat_id=user_id, text='开始发送广告')
            fstext = text.replace('/gg ', '')
            for i in user.find({}):
                yh_id = i['user_id']
                keyboard = [[InlineKeyboardButton("✅已读（点击销毁此消息）", callback_data=f'close {yh_id}')]]
                try:
                    context.bot.send_message(chat_id=i['user_id'], text=fstext,
                                             reply_markup=InlineKeyboardMarkup(keyboard))
                except:
                    pass
                time.sleep(3)
            context.bot.send_message(chat_id=user_id, text='广告发送完成')


def adm(update: Update, context: CallbackContext):
    chat = update.effective_chat
    # print(chat)
    if chat.type == 'private':
        user_id = chat['id']
        chat_id = user_id
        username = chat['username']
        firstname = chat['first_name']
        fullname = chat['full_name']
        timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        lastname = chat['last_name']
        text = update.message.text
        text1 = text.split(' ')
        user_list = user.find_one({'user_id': user_id})
        USDT = user_list['USDT']
        state = user_list['state']
        if state == '4':
            if len(text1) == 3:
                df_id = int(text1[1])
                money = text1[2]
                if user.find_one({'user_id': df_id}) is None:
                    context.bot.send_message(chat_id=chat_id, text='用户不存在')
                    return
                if '+' in money:
                    money = money.replace('+', '')
                    if not is_number(money):
                        context.bot.send_message(chat_id=chat_id, text='非数字，操作失败')
                        return
                    hyh_list = user.find_one({'user_id': df_id})
                    hyh_money = hyh_list['USDT']
                    now_money = standard_num(hyh_money + float(money))
                    now_money = float(now_money) if str((now_money)).count('.') > 0 else int(standard_num(now_money))

                    order_id = generate_24bit_uid()
                    user_logging(order_id, '充值', df_id, money, timer)
                    user.update_one({'user_id': df_id}, {'$set': {'USDT': now_money}})
                    hyh_list = user.find_one({"user_id": df_id})
                    fullname = hyh_list['fullname']
                    USDT = hyh_list['USDT']
                    fstext = f'''
ID: {df_id}
昵称: {fullname}
余额: {USDT}
                    '''
                    context.bot.send_message(chat_id=chat_id, text=fstext)

                    fstext = f'''
<b>✅    通过管理员充值：{money} USDT

💳    您的余额：{USDT}  USDT</b>
                    '''
                    context.bot.send_message(chat_id=df_id, text=fstext, parse_mode='HTML')
                else:
                    money = money.replace('-', '')
                    if not is_number(money):
                        context.bot.send_message(chat_id=chat_id, text='非数字，操作失败')
                        return
                    hyh_list = user.find_one({'user_id': df_id})
                    hyh_money = hyh_list['USDT']
                    now_money = standard_num(hyh_money - float(money))
                    now_money = float(now_money) if str((now_money)).count('.') > 0 else int(standard_num(now_money))

                    order_id = generate_24bit_uid()
                    user_logging(order_id, '扣款', df_id, money, timer)
                    user.update_one({'user_id': df_id}, {'$set': {'USDT': now_money}})
                    hyh_list = user.find_one({"user_id": df_id})
                    fullname = hyh_list['fullname']
                    USDT = hyh_list['USDT']
                    fstext = f'''
ID: {df_id}
昵称: {fullname}
余额: {USDT}
                    '''
                    context.bot.send_message(chat_id=chat_id, text=fstext)

                    fstext = f'''
<b>✅    通过管理员扣款：{money} USDT

💳    您的余额：{USDT}  USDT</b>
                    '''
                    context.bot.send_message(chat_id=df_id, text=fstext, parse_mode='HTML')
            else:
                context.bot.send_message(chat_id=chat_id, text='格式为: /add id +-数值，有两个空格')


def cha(update: Update, context: CallbackContext):
    chat = update.effective_chat
    # print(chat)
    if chat.type == 'private':
        user_id = chat['id']
        chat_id = user_id
        username = chat['username']
        firstname = chat['first_name']
        fullname = chat['full_name']
        timer = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        lastname = chat['last_name']
        text = update.message.text
        text1 = text.split(' ')
        user_list = user.find_one({'user_id': user_id})
        USDT = user_list['USDT']
        state = user_list['state']
        if state == '4':
            if len(text1) == 2:
                jieguo = text1[1]
                if is_number(jieguo):
                    df_id = int(jieguo)
                    df_list = user.find_one({'user_id': df_id})
                    if df_list is None:
                        context.bot.send_message(chat_id=chat_id, text='用户不存在')
                        return
                else:
                    df_list = user.find_one({'username': jieguo.replace('@', '')})
                    if df_list is None:
                        context.bot.send_message(chat_id=chat_id, text='用户不存在')
                        return
                    df_id = df_list['user_id']
                df_fullname = df_list['fullname']
                df_username = df_list['username']
                if df_username is None:
                    df_username = df_fullname
                else:
                    df_username = f'<a href="https://t.me/{df_username}">{df_username}</a>'
                creation_time = df_list['creation_time']
                zgsl = df_list['zgsl']
                zgje = df_list['zgje']
                USDT = df_list['USDT']
                fstext = f'''
<b>用户ID:</b>  <code>{df_id}</code>
<b>用户名:</b>  {df_username} 
<b>注册日期:</b>  {creation_time}

<b>总购数量:</b>  {zgsl}

<b>总购金额:</b>  {standard_num(zgje)} USDT

<b>您的余额:</b>  {USDT} USDT
                '''
                keyboard = [[InlineKeyboardButton('🛒购买记录', callback_data=f'gmaijilu {df_id}')],
                            [InlineKeyboardButton('关闭', callback_data=f'close {df_id}')]]
                context.bot.send_message(chat_id=user_id, text=fstext, parse_mode='HTML',
                                         reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)



            else:
                context.bot.send_message(chat_id=chat_id, text='格式为: /cha id或用户名，有一个空格')


def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        # print(f"Folder '{folder_path}' created successfully.")
    else:
        pass
        # print(f"Folder '{folder_path}' already exists.")


def parse_url(content):
    args = content.split('&')
    if len(args) < 2:
        (title, url) = ("格式错误，点击联系管理员", "www.baidu.com")
    else:
        (title, url) = (args[0].strip(), (None if len(args) < 1 else args[1].strip()))
    return create_keyboard(title, url)


def create_keyboard(title, url=None, callback_data=None, inline_query=None):
    return [InlineKeyboardButton(title, url=url, callback_data=callback_data,
                                 switch_inline_query_current_chat=inline_query)]


def parse_urls(content, maxurl=99):
    cnt_url = 0
    keyboard = []
    rows = content.split('\n')
    for row in rows:
        krow = []
        els = row.split('|')
        for el in els:
            kel = parse_url(el)
            if not kel:
                continue
            krow = krow + kel
            cnt_url = cnt_url + 1
            if cnt_url == maxurl:
                break
        keyboard.append(krow)
        if cnt_url == maxurl:
            break
    return keyboard


def main():
    updater = Updater(token='token', use_context=True, workers=128,
                      request_kwargs={'read_timeout': 20, 'connect_timeout': 20})
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start, run_async=True))
    dispatcher.add_handler(CommandHandler('add', adm, run_async=True))
    dispatcher.add_handler(CommandHandler('cha', cha, run_async=True))
    dispatcher.add_handler(CommandHandler('gg', fbgg, run_async=True))
    # dispatcher.add_error_handler(error_callback)

    dispatcher.add_handler(CallbackQueryHandler(startupdate, pattern='startupdate'))

    dispatcher.add_handler(CallbackQueryHandler(delrow, pattern='delrow'))
    dispatcher.add_handler(CallbackQueryHandler(newrow, pattern='newrow'))
    dispatcher.add_handler(CallbackQueryHandler(newkey, pattern='newkey'))
    dispatcher.add_handler(CallbackQueryHandler(backstart, pattern='backstart'))
    dispatcher.add_handler(CallbackQueryHandler(paixurow, pattern='paixurow'))
    dispatcher.add_handler(CallbackQueryHandler(addzdykey, pattern='addzdykey'))
    dispatcher.add_handler(CallbackQueryHandler(qrscdelrow, pattern='qrscdelrow '))
    dispatcher.add_handler(CallbackQueryHandler(addhangkey, pattern='addhangkey '))
    dispatcher.add_handler(CallbackQueryHandler(delhangkey, pattern='delhangkey '))
    dispatcher.add_handler(CallbackQueryHandler(qrdelliekey, pattern='qrdelliekey '))
    dispatcher.add_handler(CallbackQueryHandler(keyxq, pattern='keyxq '))
    dispatcher.add_handler(CallbackQueryHandler(setkeyname, pattern='setkeyname '))
    dispatcher.add_handler(CallbackQueryHandler(settuwenset, pattern='settuwenset '))
    dispatcher.add_handler(CallbackQueryHandler(setkeyboard, pattern='setkeyboard '))
    dispatcher.add_handler(CallbackQueryHandler(cattuwenset, pattern='cattuwenset '))
    dispatcher.add_handler(CallbackQueryHandler(paixuyidong, pattern='paixuyidong '))
    dispatcher.add_handler(CallbackQueryHandler(close, pattern='close '))
    dispatcher.add_handler(CallbackQueryHandler(yuecz, pattern='yuecz '))
    dispatcher.add_handler(CallbackQueryHandler(settrc20, pattern='settrc20'))
    dispatcher.add_handler(CallbackQueryHandler(spgli, pattern='spgli'))
    dispatcher.add_handler(CallbackQueryHandler(newfl, pattern='newfl'))
    dispatcher.add_handler(CallbackQueryHandler(flxxi, pattern='flxxi '))
    dispatcher.add_handler(CallbackQueryHandler(upspname, pattern='upspname '))
    dispatcher.add_handler(CallbackQueryHandler(newejfl, pattern='newejfl '))
    dispatcher.add_handler(CallbackQueryHandler(fejxxi, pattern='fejxxi '))
    dispatcher.add_handler(CallbackQueryHandler(upejflname, pattern='upejflname '))
    dispatcher.add_handler(CallbackQueryHandler(catejflsp, pattern='catejflsp '))
    dispatcher.add_handler(CallbackQueryHandler(backzcd, pattern='backzcd'))
    dispatcher.add_handler(CallbackQueryHandler(paixufl, pattern='paixufl'))
    dispatcher.add_handler(CallbackQueryHandler(flpxyd, pattern='flpxyd '))
    dispatcher.add_handler(CallbackQueryHandler(delfl, pattern='delfl'))
    dispatcher.add_handler(CallbackQueryHandler(qrscflrow, pattern='qrscflrow '))
    dispatcher.add_handler(CallbackQueryHandler(paixuejfl, pattern='paixuejfl '))
    dispatcher.add_handler(CallbackQueryHandler(ejfpaixu, pattern='ejfpaixu '))
    dispatcher.add_handler(CallbackQueryHandler(delejfl, pattern='delejfl '))
    dispatcher.add_handler(CallbackQueryHandler(qrscejrow, pattern='qrscejrow '))
    dispatcher.add_handler(CallbackQueryHandler(update_hb, pattern='update_hb '))
    dispatcher.add_handler(CallbackQueryHandler(gmsp, pattern='gmsp '))
    dispatcher.add_handler(CallbackQueryHandler(upmoney, pattern='upmoney '))
    dispatcher.add_handler(CallbackQueryHandler(sysming, pattern='sysming'))
    dispatcher.add_handler(CallbackQueryHandler(gmqq, pattern='gmqq'))
    dispatcher.add_handler(CallbackQueryHandler(qrgaimai, pattern='qrgaimai '))
    dispatcher.add_handler(CallbackQueryHandler(update_xyh, pattern='update_xyh '))
    dispatcher.add_handler(CallbackQueryHandler(update_hy, pattern='update_hy '))
    dispatcher.add_handler(CallbackQueryHandler(yhnext, pattern='yhnext '))
    dispatcher.add_handler(CallbackQueryHandler(yhlist, pattern='yhlist'))
    dispatcher.add_handler(CallbackQueryHandler(gmaijilu, pattern='gmaijilu'))
    dispatcher.add_handler(CallbackQueryHandler(zcfshuo, pattern='zcfshuo'))
    dispatcher.add_handler(CallbackQueryHandler(gmainext, pattern='gmainext '))
    dispatcher.add_handler(CallbackQueryHandler(update_txt, pattern='update_txt '))
    dispatcher.add_handler(CallbackQueryHandler(backgmjl, pattern='backgmjl '))
    dispatcher.add_handler(CallbackQueryHandler(qchuall, pattern='qchuall '))
    dispatcher.add_handler(CallbackQueryHandler(update_wbts, pattern='update_wbts '))
    dispatcher.add_handler(CallbackQueryHandler(update_gg, pattern='update_gg '))
    dispatcher.add_handler(CallbackQueryHandler(zdycz, pattern='zdycz'))

    dispatcher.add_handler(CallbackQueryHandler(addhb, pattern='addhb'))
    dispatcher.add_handler(CallbackQueryHandler(lqhb, pattern='lqhb '))
    dispatcher.add_handler(CallbackQueryHandler(xzhb, pattern='xzhb '))
    dispatcher.add_handler(CallbackQueryHandler(yjshb, pattern='yjshb'))
    dispatcher.add_handler(CallbackQueryHandler(jxzhb, pattern='jxzhb'))
    dispatcher.add_handler(CallbackQueryHandler(shokuan, pattern='shokuan '))
    dispatcher.add_handler(CallbackQueryHandler(update_sysm, pattern='update_sysm '))
    dispatcher.add_handler(InlineQueryHandler(inline_query))

    dispatcher.add_handler(CallbackQueryHandler(qxdingdan, pattern='qxdingdan ', run_async=True))

    dispatcher.add_handler(CallbackQueryHandler(sifa, pattern='sifa'))
    dispatcher.add_handler(CallbackQueryHandler(kaiqisifa, pattern='kaiqisifa', run_async=True))
    dispatcher.add_handler(CallbackQueryHandler(tuwen, pattern='tuwen', run_async=True))
    dispatcher.add_handler(CallbackQueryHandler(anniu, pattern='anniu', run_async=True))
    dispatcher.add_handler(CallbackQueryHandler(cattu, pattern='cattu', run_async=True))

    dispatcher.add_handler(MessageHandler(Filters.chat_type.private & Filters.reply, huifu), )
    dispatcher.add_handler(MessageHandler(
        (Filters.text | Filters.photo | Filters.animation | Filters.video | Filters.document) & ~(Filters.command),
        textkeyboard, run_async=True))
    updater.job_queue.run_repeating(suoyouchengxu, 1, 1, name='suoyouchengxu')
    updater.job_queue.run_repeating(jiexi, 3, 1, name='chongzhi')
    updater.start_polling(timeout=600)
    updater.idle()


if __name__ == '__main__':

    for i in ['发货', '协议号发货', '手机接码发货', '临时文件夹', '谷歌发货', '协议号', '号包']:
        create_folder_if_not_exists(i)
    main()

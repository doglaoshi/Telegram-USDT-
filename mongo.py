import datetime, time
import json
import random
import re
from datetime import timedelta, date
import pymongo
from pymongo.collection import Collection

teleclient = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
teleclient["admin"].authenticate("admin", "005514", mechanism='SCRAM-SHA-1')
mydb = teleclient['GULi48_bot']  # pyright: ignore[reportUnreachable, reportUnreachable, reportUndefinedVariable]
user = mydb['user']
shangtext = mydb['shangtext']
get_key = mydb['get_key']
topup = mydb['topup']
get_kehuduan = mydb['get_kehuduan']
shiyong = mydb['shiyong']
user_log = mydb['user_log']
fenlei = mydb['fenlei']
ejfl = mydb['ejfl']
hb = mydb['hb']
xyh = mydb['xyh']
gmjlu = mydb['gmjlu']
fyb = mydb['fyb']
sftw = mydb['sftw']
hongbao = mydb['hongbao']
qb = mydb['qb']
zhuanz = mydb['zhuanz']




def sifatuwen(bot_id, projectname, text, file_id,key_text, keyboard, send_type):
    sftw.insert_one({
        'bot_id': bot_id,
        'projectname': projectname,
        'text': text,
        'file_id': file_id,
        'key_text': key_text,
        'keyboard': keyboard,
        'send_type': send_type,
        'state': 1,
        'entities': b'\x80\x03]q\x00.'
    })

def fanyibao(projectname, text, fanyi):
    fyb.insert_one({
        'projectname':projectname,
        'text': text,
        'fanyi': fanyi
    })

def goumaijilua(leixing, bianhao, user_id, projectname,text, ts,timer):
    gmjlu.insert_one({
        'leixing': leixing,
        'bianhao': bianhao,
        'user_id': user_id,
        'projectname': projectname,
        'text': text,
        'ts': ts,
        'timer': timer
    })

def xieyihaobaocun(uid, nowuid, hbid, projectname, timer): 
    xyh.insert_one({
        'uid': uid,
        'nowuid': nowuid,
        'hbid': hbid,
        'projectname': projectname,
        'state': 0,
        'timer': timer
    })

def shangchuanhaobao(leixing,uid, nowuid, hbid, projectname,timer): 
    hb.insert_one({
        'leixing': leixing,
        'uid': uid,
        'nowuid': nowuid,
        'hbid': hbid,
        'projectname': projectname,
        'state': 0,
        'timer': timer
    })
    
    
def erjifenleibiao(uid, nowuid, projectname, row):
    ejfl.insert_one({
        'uid': uid,
        'nowuid': nowuid,
        'projectname': projectname,
        'row': row,
        'text': f'''
<b>♻️ 账号正在打包！稍等片刻！
‼️   二级密码看文件夹里2fa
➖➖➖➖➖➖➖➖
➖➖➖➖➖➖➖➖
☎️ 客服✈️ @goulaoshi @goulaoshi
📣频道：@goulaoshi
✨双向联系：@goulaoshi
➖➖➖➖➖➖➖➖</b>
        ''',
        'money': 0
    })

def fenleibiao(uid, projectname,row):
    fenlei.insert_one({
        'uid': uid,
        'projectname': projectname,
        'row': row
    })

def user_logging(uid, projectname , user_id, today_money,today_time):
    user_log.insert({
        'uid': uid,
        'projectname': projectname,
        'user_id': user_id,
        'today_money': today_money,
        'today_time': today_time
    })

def sydata(tranhash):
    shiyong.insert_one({
        'tranhash': tranhash
    })

def kehuduanurl(api, key):
    get_kehuduan.insert_one({
        'api': api,
        'key': key,
        'tcid': 0,
    })
    
    
def keybutton(Row,first):
    get_key.insert_one({
        'Row': Row,
        'first': first,
        'projectname': '点击修改内容',
        'text': '',
        'file_id': '',
        'file_type': '',
        'key_text': '',
        'keyboard': b'\x80\x03]q\x00.',
        'entities': b'\x80\x03]q\x00.'
    })

def shang_text(projectname, text):
    shangtext.insert_one({
        'projectname': projectname,
        'text': text
    })
    
    
def user_data(key_id, user_id, username, fullname, lastname, state, creation_time, last_contact_time):
    user.insert_one({
        'count_id': key_id,
        'user_id': user_id,
        'username': username,
        'fullname': fullname,
        'lastname': lastname,
        'state': state,
        'creation_time': creation_time,
        'last_contact_time': last_contact_time,
        'USDT': 0,
        'zgje': 0,
        'zgsl': 0,
        'sign': 0,
        'lang': 'zh'

    })


if shangtext.find_one({}) == None:
    fstext = f'''
🌹🌹🌹 欢迎光临故里号铺,祝各位老板2023顺风顺水

    💎本店业务💎 

飞机号，协议号,  直登号(tdata) 批发/零售 !
开通飞机会员,  能量租用&TRX兑换 , 老号老群老频道 !
_____________________________________

❗️ 未使用过的本店商品的，请先少量购买测试，以免造成不必要的争执！谢谢合作！

❗️ 免责声明：本店所有商品，仅用于娱乐测试，不得用于违法活动！ 请遵守当地法律法规！

_____________________________________

☎️ 客服： @goulaoshi  @goulaoshi
🏦 频道： @goulaoshi     @goulaoshi
♻️能量租用&TRX兑换:  @goulaoshi

⚙️ /start   ⬅️点击命令打开底部菜单!
    '''
    shang_text('欢迎语',fstext)
    shang_text('欢迎语样式',b'\x80\x03]q\x00.')
    shang_text('充值地址','')
    shang_text('营业状态',1)
if __name__ == '__main__':
    get_key.insert_one({
        'Row': 4,
        'first': 1,
        'projectname': '🧧 发红包',
        'text': '',
        'file_id': '',
        'file_type': '',
        'key_text': '',
        'keyboard': b'\x80\x03]q\x00.',
        'entities': b'\x80\x03]q\x00.'
    })
    # hb.update_many({'uid':'7f485c78af4b550e8ab02e89'},{"$set":{"leixing":'API'}})
    # shang_text('欢迎语样式',b'\x80\x03]q\x00.')
    # shang_text('充值地址','')
    # shang_text('营业状态',1)
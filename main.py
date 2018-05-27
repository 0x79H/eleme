# -*- coding: UTF-8 -*-
# coding=utf-8

import time
import codecs

import requests
import json
import pymysql
import logging
import _winreg

# 选地址后地址栏内
ele_geohash = 'xxxxxxxxxxxx'
ele_latitude = 'xx.xxxxxx'
ele_longitude = 'xxx.xxxxxx'

# ele.me登陆信息
ele_SID = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
ele_USERID = 'xxxxxxxxx'
ele_ubt_ssid = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx_xxxx-xx-xx'

# sql
db_server = '127.0.0.1'
db_user = 'root'
db_pass = 'toor'
db_db = 'ele'

# 红包
hb_limit = 35
hb_discount = 5

limit = 50
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] \t%(name)s:\t%(levelname)s:\t %(message)s"
)


def get_desktop():
    key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                          r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
    return _winreg.QueryValueEx(key, "Desktop")[0]


def setting():
    conn = pymysql.connect(db_server, db_user, db_pass, charset='utf8')
    cursor = conn.cursor()
    try:
        cursor.execute("DROP DATABASE  {0}".format(db_db))
        conn.commit()
    except:
        pass
    cursor.execute("CREATE DATABASE {0}".format(db_db))
    conn.commit()
    cursor.close()
    conn.close()

    db = pymysql.connect(db_server, db_user, db_pass, db_db, charset='utf8')
    cursor = db.cursor()
    sql = """create table activities
(
  id         int unsigned auto_increment
    primary key,
  name       varchar(255)                        null,
  tips       varchar(255)                        null,
  buy        int(5) unsigned default '0'         null,
  discount   double(5, 1) default '0.0'          null,
  express_price       int(5) unsigned default '0'         null,
  express_fee   double(5, 1) default '0.0'          null,
  created_at timestamp default CURRENT_TIMESTAMP null
  on update CURRENT_TIMESTAMP
)
  engine = InnoDB
  charset = utf8mb4;

"""
    cursor.execute(sql)
    db.commit()
    cursor.close()
    db.close()


def get_info():
    offset = 0
    db = pymysql.connect(db_server, db_user, db_pass, db_db, charset='utf8')
    while True:
        url = "https://www.ele.me/restapi/shopping/restaurants?extras%5B%5D=activities&geohash={0}&latitude={1}&longitude={2}&offset={3}&limit={4}&terminal=web".format(
            ele_geohash, ele_latitude, ele_longitude, offset, limit)
        cookies = dict(SID=ele_SID, USERID=ele_USERID, ubt_ssid=ele_ubt_ssid)
        data = requests.get(url, cookies=cookies).json()
        logging.info("offset:" + str(offset))
        json.dumps(data, sort_keys=True, indent=4, separators=(',', ':'))
        if len(data) == 0:
            break

        offset += limit
        for restaurant in data:
            description = restaurant['piecewise_agent_fee']['rules'][0]
            description_tips = restaurant['piecewise_agent_fee']['description']
            for activity in restaurant['activities']:
                if "type" in activity and activity['type'] is 106:  # 满赠
                    description_tips += activity['tips']
                if "type" in activity and activity['type'] is 102:  # 满减
                    attribute = json.loads(activity["attribute"])
                    for manjian in attribute:
                        name = restaurant["name"]
                        tips = activity["tips"]
                        buy = manjian
                        discount = attribute[manjian]["1"]
                        cursor = db.cursor()
                        sql = u"INSERT INTO activities(name, \
                                   tips, buy, discount,express_price,express_fee) \
                                   VALUES ('%s', '%s', '%s', '%s','%s','%s')" % \
                              (name, description_tips + u'|' + tips, buy, discount, description['price'],
                               description['fee'])
                        cursor.execute(sql)
                        db.commit()

    db.close()


def get_output(pay_money=999999):
    sql = """select name,tips,buy,discount,if(buy<={0},{0}-discount-{1}+express_fee,buy-discount-{1}+express_fee) as pay,if(buy<={0},({0}-discount-{1}+express_fee)/{0},(buy-discount-{1}+express_fee)/buy) as percent from activities where if(buy<={0},{0}-discount-{1}+express_fee,buy-discount-{1}+express_fee)<{2} order by if(buy<={0},({0}-discount-{1}+express_fee)/{0},(buy-discount-{1}+express_fee)/buy)"""
    name = u"折扣"
    do_sql(sql, name, pay_money)
    sql = """select name,tips,buy,discount,if(buy<={0},{0}-discount-{1}+express_fee,buy-discount-{1}+express_fee) as pay,if(buy<={0},({0}-discount-{1}+express_fee)/{0},(buy-discount-{1}+express_fee)/buy) as percent from activities where if(buy<={0},{0}-discount-{1}+express_fee,buy-discount-{1}+express_fee)<{2} order by if(buy<={0},{0}-discount-{1}+express_fee,buy-discount-{1}+express_fee)"""
    name = u"价格"
    do_sql(sql, name, pay_money)
    time.sleep(5)


def do_sql(sql, name, pay_money):
    sql = sql.format(hb_limit, hb_discount, pay_money)
    db = pymysql.connect(db_server, db_user, db_pass, db_db, charset='utf8')
    cursor = db.cursor()
    cursor.execute(sql)
    html = u"""<style type="text/css">
*,:after,:before{box-sizing:border-box}
body{font-family:Open Sans,sans-serif;font-size:13px;margin:20px;text-align:center;text-transform:uppercase;color:#000;background-color:#fff}
h1{font-size:21px;margin:1.5em 0}
table{overflow:hidden;width:auto;max-width:100%;margin:0 auto;border-collapse:collapse;border-spacing:0}
table td{padding:10px;position:relative;outline:0;border-bottom:1px solid rgba(0,0,0,.1);vertical-align:top}
table thead th{border-bottom-width:2px}
table tbody th{text-align:left;white-space:nowrap}
table tbody>tr:hover td,table tbody>tr:hover th{background:#fffe96}
table td:hover:after,table thead th:not(:empty):hover:after{content:'';position:absolute;z-index:-1;top:-5000px;left:0;width:100%;height:625pc;background:#fffe96}
   </style>
    """
    html += "<table>\r\n"
    html += u"<thead><tr><th>{0}</th><th>{1}</th><th>{2}</th><th>{3}</th><th>{4}</th><th>{5}</th></tr></thead>".format(
        u"店家名", u"规则", u"满", u"减", u"实付款", u"折扣")
    text = u"<tr><th>{0}</th><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5:.3f}</td></tr>\r\n"
    for i1, i2, i3, i4, i5, i6 in cursor:
        if u'蛋糕' in i1:
            continue
        i1 = re.sub("'", r"\'", i1)  # 怎么会有带单引号的xx店铺名
        html += text.format(i1, i2, i3, i4, i5, i6)

    html += "</table>\r\n"
    filename = get_desktop() + u'\\' + name + u'_' + time.strftime("%Y-%m-%d_%H%M", time.localtime()) + u'.html'
    with codecs.open(filename, "w", "utf-8") as f:
        f.write(html)
    logging.info("已生成至桌面。")


if __name__ == '__main__':
    setting()
    get_info()
    get_output()

# forked from https://gist.github.com/hooklife/b416c326e1ea726b38003f44b9109ed0

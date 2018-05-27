# -*- coding: UTF-8 -*-

import requests
import json
import pymysql
import logging

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
    level=logging.WARNING,
    format="[%(asctime)s] \t%(name)s:\t%(levelname)s:\t %(message)s"
)


def setting():
    conn = pymysql.connect(db_server, db_user, db_pass, charset='utf8')
    cursor = conn.cursor()
    cursor.execute("DROP DATABASE  {0}".format(db_db))
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
                        sql = "INSERT INTO activities(name, \
                                   tips, buy, discount,express_price,express_fee) \
                                   VALUES ('%s', '%s', '%s', '%s','%s','%s')" % \
                              (name, description_tips + '|' + tips, buy, discount, description['price'],
                               description['fee'])
                        cursor.execute(sql)
                        db.commit()

    db.close()


def get_output(pay_money=999999):
    sql = """select name,tips,buy,discount,if(buy<={0},{0}-discount-{1}+express_fee,buy-discount-{1}+express_fee) as pay,if(buy<={0},({0}-discount-{1}+express_fee)/{0},(buy-discount-{1}+express_fee)/buy) as percent from activities where if(buy<={0},{0}-discount-{1}+express_fee,buy-discount-{1}+express_fee)<{2} order by if(buy<={0},({0}-discount-{1}+express_fee)/{0},(buy-discount-{1}+express_fee)/buy)"""
    sql = sql.format(hb_limit, hb_discount, pay_money)
    db = pymysql.connect(db_server, db_user, db_pass, db_db, charset='utf8')
    cursor = db.cursor()
    cursor.execute(sql)
    # text = "{0:>10}{1:>10}{2:>10}{3:>10}{4:>10}{5:>10}"
    # text="<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>"
    # print text.format("店家名", "活动", "满", "减", "实付款", "折扣")
    for row in cursor:
        print row


if __name__ == '__main__':
    setting()
    get_info()
    get_output(40)

# forked from https://gist.github.com/hooklife/b416c326e1ea726b38003f44b9109ed0

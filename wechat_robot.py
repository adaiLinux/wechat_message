#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
发送微信机器人消息提醒！
"""

import socket
import urllib2
import urllib
import re
import json
import threading
import Queue
import time
import logging
import ConfigParser
import os

# token = u'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=aca0ef08-9f7e-4fb9-a0cc-62686b6d637d'

back_content = 'HTTP/1.x 200 ok\r\nContent-Type: text/html\r\n\r\n ok'

config = ConfigParser.ConfigParser()
config.read('./config.ini')


if config.has_section('log') and config.has_option('log', 'path'):
    path = config.get('log', 'path')
    if not os.path.exists(path):
        os.mkdir(path)
else:
    path = './'

log_first_name = time.strftime('%Y-%m-%d', time.localtime(time.time()))
log_name = path + '/' + log_first_name + '.log'
logger = logging.getLogger('wechat')
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler(log_name)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime) - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

wechat_queue = Queue.Queue()
msg_queue = Queue.Queue()


def wechat(message):
    """
    向微信机器人发消息
    :param message: 消息内容
    :return:
    """
    subject = ''
    content = ''

    if message['status'] != 'OK':
        subject = '告警'
        content = '告警主机: %s\n告警级别: %s\n告警信息: %s\n告警时间: %s\n' %(
            message['host'], message['level'], message['info'], message['time']
        )
    else:
        subject = '恢复'
        content = '恢复主机: %s\n恢复级别: %s\n恢复信息: %s\n恢复时间: %s\n' %(
            message['host'], message['level'], message['info'], message['time']
        )
        if message['tos']:
            tos = message['toc']
        else:
            tos = ''

    header = {
        "Content-Type": 'application/json',
        "charset": 'utf-8'
    }

    data = {
        "msgtype": "text",
        "text": {
            "content": subject + '\n' + content or u'',
            "mentioned_mobile_list": [tos, "@all"]
        }
    }

    try:
        send_data = json.dumps(data)
        request = urllib2.Request(token, data=send_data, headers=header)
        urlopen = urllib2.urlopen(request)
        return urlopen.read()

    except Exception as e:
        logger.error(e)


def set_message(msg):
    """
    构建消息内容
    :param msg:
    :return:
    """
    people = ''
    content = ''
    try:
        body = msg.split('\r\n\r\n', 1)[1]
        body = urllib.unquote(body)
        logger.info("获取消息成功: %s" %body)
        for i in body.split('&', 1):
            if re.match('tos', i):
                people = i
            else:
                content = i
                content = content.replace('+', ' ')

        search_obj = re.search(
            r'\[(.*)\]\[(.*)\]\[(.*)\]\[(.*)\]\[(.*)\]\[(.*)\]',
            content.split('=', 1)[1],
            re.M | re.I
        )

        message = {
            'level': search_obj.group(1),
            'status': search_obj.group(2),
            'host': search_obj.group(3),
            'tag': search_obj.group(4),
            'info': search_obj.group(5),
            'time': search_obj.group(6),
            'tos': people
        }

        return message

    except Exception as e:
        logger.error(e)


def thread_msg(thread_id):
    # while True:
    if not msg_queue.empty():
        msg = msg_queue.get()
        if msg:
            m = set_message(msg)
            logger.info("消息解析成功: %s" %m)
            wechat_queue.put(m)
        else:
            logger.debug("msg_queue is empty, waiting...")
            time.sleep(10)


def thread_wechat():

    # while True:
    if not wechat_queue.empty():
        msg = wechat_queue.get()
        logger.info("发送消息: %s" %msg)
        if msg:
            d_res = wechat(msg)
            logger.info("消息发送成功: %s" %d_res)
        else:
            logger.warning("获取消息失败: %s" %msg)
    else:
        logger.debug("wechat_queue is empty, waiting...")
        time.sleep(10)


def init(host=None, port=None):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if host is None:
        host = socket.gethostname()
    if port is None:
        port = 10086
    s.bind((host, int(port)))
    s.listen(5)
    return s


def get_msg(conn):
    msg = ''
    try:
        data = conn.recv(2048)
        msg += data
        msg_queue.put(msg)
        conn.sendall(back_content)
        conn.close()
    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    if config.has_section('default') and config.has_option('default', 'host'):
        host = config.get('default', 'host')
    else:
        host = None

    if config.has_section('default') and config.has_option('default', 'port'):
        port = config.get('default', 'port')
    else:
        port = None

    if config.has_section('default') and config.has_option('default', 'token'):
        token = config.get('default', 'token')
    else:
        logger.debug("Token is empty!!!")
    logger.info('Starting...')

    for x in range(0, 1):
        t = threading.Thread(target=thread_msg, args=(x,))
        t.start()
    print(host, port)
    ok = init(host, port)
    logger.info("初始化成功: %s" %ok)

    t = threading.Thread(target=thread_wechat)
    t.start()

    # while True:
    conn, addr = ok.accept()
    t = threading.Thread(target=get_msg, args=(conn,))
    t.start()


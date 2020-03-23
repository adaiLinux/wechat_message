#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
发送微信机器人消息提醒！
"""

import urllib
import re
import requests
from flask import Flask

app = Flask(__name__)

token = u'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=aca0ef08-9f7e-4fb9-a0cc-62686b6d637d'


def send_wechat(message):
    """
    向微信机器人发消息
    :param message: 消息内容
    :return:
    """
    subject = ''
    content = ''

    if message['status'] != 'OK':
        subject = '错误'
        content = '告警主机: %s\n告警级别: %s\n告警信息: %s\n告警时间: %s\n' %(
            message['host'], message['level'], message['info'], message['time']
        )
    else:
        subject = '恢复'
        content = '恢复主机: %s\n恢复级别: %s\n恢复信息: %s\n恢复时间: %s\n' %(
            message['host'], message['level'], message['info'], message['time']
        )
    if message['tos']:
        tos = message['tos']
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
            "mentioned_mobile_list": [message, "@all"]
        }
    }

    try:
        response = requests.post(token, json=data, timeout=2)
        return response.status_code == 200

    except Exception as e:
        return ValueError("error")


@app.route('/wechat/<msg>', methods=['GET'])
def set_message(msg):
    """
    获取消息内容
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

        send_wechat(message)

    except Exception as e:
        return ValueError("error")


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)



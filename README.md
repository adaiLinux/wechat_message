# 说明
小试牛刀。

通过企业微信机器人向微信群发送告警。

## 使用

### 修改配置文件

```ini
[default]
host = ip地址
port = 端口号
token = u'robot token'

; 日志相关，默认为当前目录
;[log] 
;path=
```

```bash
python wechat_robot.py
```

### 配置

将 `http://ip:port` 配置到falcon的alarm模块。
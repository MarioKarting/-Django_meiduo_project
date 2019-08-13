# !/usr/bin/env python
# _*_ coding:utf-8 _*_



# 定义发短信的任务
from celery_tasks.main import app


@app.task
def send_sms_code(mobile, sms_code):
    from libs.yuntongxun.sms import CCP
    #   手机号   验证码 过期时间 1短信模板
    result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    print("celery验证码:",sms_code)

    return result

# !/usr/bin/env python
# _*_ coding:utf-8 _*_
from django.conf import settings
from django.core.mail import send_mail

# 异步发送邮件
from celery_tasks.main import app

# bind：保证task对象会作为第一个参数自动传入
# name：异步任务别名
# retry_backoff：异常自动重试的时间间隔 第n次(retry_backoff×2^(n-1))s
# max_retries：异常自动重试次数的上限
from meiduo_mall.settings.dev import logger


@app.task(bind=True, name="send_verify_email", retry_backoff=3)
def send_verify_email(self, to_email, verify_url):
    """
    subject :主题标题
    message :邮件内容
    from_email:发件人
    recipient_list:收件人列表
     html_message: html标签邮件内容
    """
    subject = "美多商城邮箱验证"
    message = ""
    from_email = settings.EMAIL_FROM
    recipient_list = [to_email]
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s</a></p>' % (to_email, verify_url, verify_url)

    try:
        # 发邮件djano提供
        send_mail(subject, message, from_email, recipient_list, html_message=html_message)
    except Exception as e:
        logger.error(e)

        # 如果发送不成功 , 最大尝试次数3次
        raise self.retry(exec=e, max_retries=3)

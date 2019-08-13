# !/usr/bin/env python
# _*_ coding:utf-8 _*_
import re

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from apps.users.models import User
from meiduo_mall.settings.dev import logger




# 激活的链接
from utils.secret import SecretOauth

def generate_verify_email_url(user):
    # 1.userid email
    data_dict = {'user_id': user.id, 'email': user.email}

    # 2. 加密
    secret_data = SecretOauth().dumps(data_dict)

    # 3. 拼接 链接
    verify_url = settings.EMAIL_ACTIVE_URL + '?token=' + secret_data

    # 4.返回去
    return verify_url




# 封装 校验多用户名的 方法  account 下面代表什么就是什么  用户名 邮箱 手机号
def get_user_by_account(account):
    try:
        # 3.1 如果是手机号  验证码手机号
        if re.match('^1[345789]\d{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            # 3.2 不是手机号  ,验证username
            user = User.objects.get(username=account)

    except Exception as e:
        logger.error(e)#日志输出
        return None
    else:
        return user

# 2. 自定义认证后端类
class UsernameMobileAuthBackend(ModelBackend):
    # 3. 重写父类的认证方法
    def authenticate(self, request, username=None, password=None, **kwargs):

        # 1.获取校验完毕的 user
        user = get_user_by_account(username)
        # 2. 校验密码 ,如果通过返回user对象
        if user and user.check_password(password):
            return user

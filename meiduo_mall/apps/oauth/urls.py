# !/usr/bin/env python
# _*_ coding:utf-8 _*_


from django.conf.urls import url

from . import views

urlpatterns = [
    #     1. qq登录
    url(r'^qq/login/$', views.QQAuthURLView.as_view(), name='qqlogin'),

    # 2. 回调网址 解析code-->tooken-->openid  /oauth_callback
    #                  注意没有反/
    url(r'^oauth_callback$', views.QQAuthView.as_view(), name='qqauth'),

]

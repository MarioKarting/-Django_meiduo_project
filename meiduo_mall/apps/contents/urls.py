## !/usr/bin/env python
# _*_ coding:utf-8 _*_

from django.conf.urls import url

from . import views

urlpatterns = [

    # 1. 注册的子路由--子视图函数
    url(r'^$', views.IndexView.as_view(), name="index"),
]

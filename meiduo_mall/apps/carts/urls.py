# !/usr/bin/env python
# _*_ coding:utf-8 _*_


from django.conf.urls import url

from . import views

urlpatterns = [
    #    1.购物车数据 carts/
    url(r'^carts/$', views.CartsView.as_view(), name='addcart'),

    # 2. 全选 carts/selection/
    url(r'^carts/selection/$', views.CartsSelectAllView.as_view(), name='selected'),

    # 3. 简单购物车显示
    url(r'^carts/simple/$', views.CartsSimpleView.as_view(), name='simple'),

]

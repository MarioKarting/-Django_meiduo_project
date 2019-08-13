# !/usr/bin/env python
# _*_ coding:utf-8 _*_


from django.conf.urls import url

from . import views

urlpatterns = [
    #    1. 结算订单  orders/settlement/
    url(r'^orders/settlement/$', views.OrdersSettlementView.as_view(), name='settlement'),

    # 2. orders/commit/ 提交订单
    url(r'^orders/commit/$', views.OrdersCommitView.as_view(), name='commit'),

    # 3. 订单成功 -- orders/success/
    url(r'^orders/success/$', views.OrdersSuccessView.as_view(), name='sucess'),


]

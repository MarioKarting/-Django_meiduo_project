# !/usr/bin/env python
# _*_ coding:utf-8 _*_


from django.conf.urls import url

from . import views

urlpatterns = [
    #    1.payment/(?P<order_id>\d+)/  去支付接口-->获取支付宝的支付网址
    url(r'^payment/(?P<order_id>\d+)/$', views.PaymentView.as_view(), name='alipay'),


    #    1.接收支付成功的回调 payment/status/
    url(r'^payment/status/$', views.PaymentStatusView.as_view(), name='alipaystatus'),
]

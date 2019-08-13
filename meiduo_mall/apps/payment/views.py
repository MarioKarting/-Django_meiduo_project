import os

from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render

# 对接支付宝的流程---对接沙箱

# 1.登录zfb 成为开发者

# 2.注册应用 -->appid

# 3.生成 app 的公私钥 ---支付宝的公私钥 对接


# 4. 使用 python-alipy-sdk 装包

# 5. 创建aplipay --

# 6. 获取支付的url-- 支付宝网关 + order_string

# 7. 用户 --扫码支付

# 8. 对接 支付宝 支付成功的页面回调


from django.views import View

from apps.orders.models import OrderInfo
from apps.payment.models import Payment
from utils.response_code import RETCODE


# 接收回调 支付成功
class PaymentStatusView(View):
    def get(self, request):
        # 1.接收参数 查询参数
        query_dict = request.GET
        data = query_dict.dict()

        # 1.1 删除 sign值
        signature = data.pop('sign')

        # 2.校验 alipay校验--sign值 如果校验通过
        from alipay import AliPay
        alipy = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )
        sucess = alipy.verify(data, signature)

        if sucess:
            # 3.才写入 数据库
            order_id = data.get('out_trade_no')
            # 支付宝的 交易ID
            trade_id = data.get('trade_no')

            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )

            # 注意点 修改 订单的状态
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT']
            )
            # 4. 展示美多 支付成功的页面 render
            context = {
                'trade_id': trade_id
            }
            return render(request, 'pay_success.html', context)
        else:

            return HttpResponseForbidden('交易失败-非法请求')


# 1.获取 支付宝的支付网址  给了浏览器 js 请求
class PaymentView(View):
    def get(self, request, order_id):

        # 1.校验参数 判断 order 是否存在
        user = request.user
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except Exception as e:
            return HttpResponseForbidden('订单不存在')

        # 2. 创建 alipay对象  链接支付宝
        from alipay import AliPay
        alipy = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        # 3. 根据alipay对象, 加密参数
        order_string = alipy.api_alipay_trade_page_pay(
            subject="美多商城%s" % order_id,
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            return_url=settings.ALIPAY_RETURN_URL

        )

        # 4.拼接 支付宝的支付url 返回给前端
        # 真实环境电脑网站支付网关：https://openapi.alipay.com/gateway.do? + order_string
        # 沙箱环境电脑网站支付网关：https://openapi.alipaydev.com/gateway.do? + order_string
        alipay_url = settings.ALIPAY_URL + "?" + order_string

        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})

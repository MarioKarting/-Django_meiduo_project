import json
from datetime import datetime

from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views import View

# 1.结算订单页面显示
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import Address

from utils.response_code import RETCODE


# 3.订单成功
class OrdersSuccessView(View):
    def get(self, request):
        # 1.接收参数 GET
        order_id = request.GET.get('order_id')
        pay_method = request.GET.get('pay_method')
        payment_amount = request.GET.get('payment_amount')

        # 2.组合数据
        context = {
            "order_id": order_id,
            "pay_method": pay_method,
            "payment_amount": payment_amount

        }
        return render(request, 'order_success.html', context)


# 2. 提交订单
class OrdersCommitView(View):
    def post(self, request):

        # 1.接收参数 json
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        # 2.校验参数 判空 all(), address 地址存在, 支付方式 是否
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return HttpResponseForbidden('参数address_id错误')

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:

            return HttpResponseForbidden('参数pay_method错误')


        user = request.user
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + ("%09d" % user.id)
        from django.db import transaction
        # 3.生成基本订单信息 8个字段 ;  根据年月日时分秒+user.id 9位
        with transaction.atomic():
            # 回滚点
            save_id = transaction.savepoint()
            try:
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'ALIPAY'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )

                # 4.从redis购物车 取出选中的 商品
                redis_client = get_redis_connection('carts')
                redis_data = redis_client.hgetall(user.id)
                carst_dict = {}
                for data in redis_data.items():
                    sku_id = int(data[0].decode())
                    sku_dict = json.loads(data[1].decode())
                    # 如果商品选中了--我们才结算
                    if sku_dict['selected']:
                        carst_dict[sku_id] = sku_dict

                # 5.遍历商品:
                sku_ids = carst_dict.keys()
                for sku_id in sku_ids:

                    while True:
                        sku = SKU.objects.get(id=sku_id)

                        # 获取 最原始的  库存量 和 销量
                        origin_count = sku.stock
                        origin_sales = sku.sales

                        # 5.1 判断库存
                        sku_count = carst_dict[sku_id].get('count')
                        if sku_count > sku.stock:
                            # 如果买的 数量  大于了 库存
                            # 事务回滚
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})

                        # import time
                        # time.sleep(5)

                        # 5.2 sku 减少库存 增加销量
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()
                        new_stock = origin_count - sku_count
                        new_sales = origin_sales + sku_count

                        # 加乐观锁
                        result = SKU.objects.filter(id=sku_id, stock=origin_count).update(stock=new_stock,
                                                                                          sales=new_sales)
                        # 如果不是因为库存问题 倒置的下单失败, 给用户多次机会
                        if result == 0:
                            continue

                        # 5.3 spu 增加销量
                        sku.spu.sales += sku_count
                        sku.spu.save()

                        # 5.4 生成订单商品表 4个字段
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price
                        )
                        # 5.5 order 计算总价格 总数量
                        order.total_count += sku_count
                        order.total_amount += (sku_count * sku.price)

                        # 直到用户下单成功 跳出
                        break

                # 6. 总金额添加运费
                order.total_amount += order.freight
                order.save()

            except:
                    # 暴力回滚
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'code': RETCODE.OK, 'errmsg': '下单失败'})

            # 提交事务
            transaction.savepoint_commit(save_id)

            # 7. 删除 购物车 选中的数据
            redis_client.hdel(user.id, *carst_dict)

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '下单成功', 'order_id': order.order_id})


class OrdersSettlementView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        # 1.判断地址
        try:
            addresses = Address.objects.filter(user=user)

        except:
            # 设置为 None 前端需要-->编辑地址按钮
            addresses = None

        # 2.redis查询 选中的额 商品
        redis_client = get_redis_connection('carts')
        redis_data = redis_client.hgetall(user.id)
        carst_dict = {}
        for data in redis_data.items():
            sku_id = int(data[0].decode())
            sku_dict = json.loads(data[1].decode())
            # 如果商品选中了--我们才结算
            if sku_dict['selected']:
                carst_dict[sku_id] = sku_dict

        # 总个数 总金额 运费
        total_count = 0
        total_amount = Decimal(0.00)
        freight = Decimal(10.00)

        # 3. 再去 SKU 查商品, 动态添加 两个属性 count ,amount
        sku_ids = carst_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            # 动态添加 两个属性 count ,amount
            sku.count = carst_dict[sku.id].get('count')
            sku.amount = sku.price * sku.count

            # 总个数 总金额
            total_count += sku.count
            total_amount += sku.amount

        # 4. context
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight,
            'default_address_id': user.default_address_id

        }
        return render(request, 'place_order.html', context)

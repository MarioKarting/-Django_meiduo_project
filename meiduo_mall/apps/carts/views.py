from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views import View
import json

# Create your views here.
from django_redis import get_redis_connection

from apps.goods.models import SKU
from utils.response_code import RETCODE
from utils.cookiesecret import CookieSecret




class CartsSimpleView(View):
    """商品页面右上角购物车"""

    def get(self, request):
        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，查询Redis购物车
            carts_redis_client = get_redis_connection('carts')
            carts_data = carts_redis_client.hgetall(user.id)
            # 转换格式
            cart_dict = {int(data[0].decode()): json.loads(data[1].decode()) for data in carts_data.items()}

        else:
            # 用户未登录，查询cookie购物车
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = CookieSecret.loads(cart_str)
            else:
                cart_dict = {}

        # 构造简单购物车JSON数据
                # 构造简单购物车JSON数据
        cart_skus = []
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)

        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'default_image_url': sku.default_image.url
            })

        # 响应json列表数据
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_skus': cart_skus})


# 2.全选
class CartsSelectAllView(View):
    def put(self, request):
        # 1.接收参数
        selected = json.loads(request.body.decode()).get('selected', True)

        # 2.校验 seleted bool

        # 3.是否登录
        user = request.user
        if user.is_authenticated:
            # redis
            # 1.链接
            carts_redis_client = get_redis_connection('carts')

            # 2. hgetall
            carts_data = carts_redis_client.hgetall(user.id)

            # 3. 遍历修改每一个字典
            for data in carts_data.items():
                sku_id = data[0].decode()
                sku_dict = json.loads(data[1].decode())

                # 判断 全选
                if selected:
                    sku_dict['selected'] = True
                else:
                    sku_dict['selected'] = False

                carts_redis_client.hset(user.id, sku_id, json.dumps(sku_dict))

            return JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})

        else:
            # cookie
            cookie_str = request.COOKIES.get('carts')
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})
            if cookie_str is not None:
                carts_dict = CookieSecret.loads(cookie_str)

                for sku_id in carts_dict:
                    carts_dict[sku_id]['selected'] = selected

                cookie_secret_str = CookieSecret.dumps(carts_dict)
                response.set_cookie('carts', cookie_secret_str, max_age=24 * 30 * 3600)

            return response
                # 4.返回结果


# 1.增删除改查
class CartsView(View):
    # 4.删除数据
    def delete(self, request):

        # 1.接收参数
        sku_id = json.loads(request.body.decode()).get('sku_id')

        # 2. 校验 sku

        # 3. 是否登录
        user = request.user
        if user.is_authenticated:
            # redis
            # 1.链接
            cart_redis_client = get_redis_connection('carts')

            # 2. hdel删除
            cart_redis_client.hdel(user.id, sku_id)

            return JsonResponse({'code': RETCODE.OK, 'errmsg': '删除购物车成功'})
        else:
            # cookie
            cookie_str = request.COOKIES.get('carts')

            if cookie_str:
                carts_dict = CookieSecret.loads(cookie_str)
            else:
                carts_dict = {}

            response = JsonResponse({'code': RETCODE.OK, 'errmsg': '删除购物车成功'})
            if sku_id in carts_dict:
                # 1.删除
                del carts_dict[sku_id]
                # 2.加密
                carts_secret_str = CookieSecret.dumps(carts_dict)
                # 3.set_cookie
                response.set_cookie('carts', carts_secret_str, max_age=30 * 24 * 3600)
            return response
            # 4.返回前端结果

    # 3.修改数据
    def put(self, request):

        # 1.接收参数  json
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 2. 校验 判空, sku, int(count), selected
        try:
            sku = SKU.objects.get(id=sku_id)
        except:
            return HttpResponseForbidden('商品不存在')

        # 3.是否对登录
        user = request.user
        cookie_secret_str = ""
        if user.is_authenticated:
            # redis:
            # 1.链接
            carts_redis_client = get_redis_connection('carts')
            # 2. hset
            new_dict = {'count': count, 'selected': selected}
            carts_redis_client.hset(user.id, sku_id, json.dumps(new_dict))
        else:
            # cookie
            cookie_str = request.COOKIES.get('carts')

            if cookie_str:
                carts_dict = CookieSecret.loads(cookie_str)
            else:
                carts_dict = {}

            carts_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 将修改完毕的 cookie 加密
            cookie_secret_str = CookieSecret.dumps(carts_dict)

        # 4. 构建前端的数据
        cart_sku = {
            'id': sku_id,
            'count': count,
            'selected': selected,
            'name': sku.name,
            'default_image_url': sku.default_image.url,
            'price': sku.price,
            'amount': sku.price * count,
        }

        response = JsonResponse({'code': RETCODE.OK, 'errmsg': '修改购物车成功', 'cart_sku': cart_sku})
        if not user.is_authenticated:
            response.set_cookie('carts', cookie_secret_str, max_age=30 * 24 * 3600)
        # 5.返回响应
        return response

    # 2.展示 查询
    def get(self, request):
        # 1.是否登录
        user = request.user
        if user.is_authenticated:
            # 2.登录 操作redis
            # 2.1 链接
            carts_redis_client = get_redis_connection('carts')

            # 2.2 查询数据--user.id
            carts_data = carts_redis_client.hgetall(user.id)
            # carts_data = {b'1':b'{"count":1,"selected":true}'}

            # 2.3 转换数据格式
            carts_dict = {}
            # for data in carts_data.items():
            #     # data = (b'1':b'{"count":1,"selected":true}')
            #     sku_key = int(data[0].decode())
            #     sku_data = json.loads(data[1].decode())
            #     carts_dict[sku_key] = sku_data

            carts_dict = {int(data[0].decode()): json.loads(data[1].decode()) for data in carts_data.items()}

        else:
            # 3.未登录 cookie
            cookie_str = request.COOKIES.get('carts')

            if cookie_str:
                carts_dict = CookieSecret.loads(cookie_str)
            else:
                carts_dict = {}

        sku_ids = carts_dict.keys()
        # 根据 sku_id 取出所有的商品sku
        skus = SKU.objects.filter(id__in=sku_ids)

        # 拼接前端需要的数据格式
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': carts_dict.get(sku.id).get('count'),
                'selected': str(carts_dict.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * carts_dict.get(sku.id).get('count')),
            })

        context = {
            'cart_skus': cart_skus
        }
        return render(request, 'cart.html', context)

    # 1.增加POST
    def post(self, request):
        # 1.获取参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 2.校验 判空 sku,int(count) selected bool
        if not all([sku_id, count]):
            return HttpResponseForbidden('缺少必传参数')

        try:
            SKU.objects.get(id=sku_id)
        except:
            return HttpResponseForbidden('商品不存在')

        try:
            count = int(count)
        except:
            return HttpResponseForbidden('count参数 不是整型')

        if selected:
            if not isinstance(selected, bool):
                return HttpResponseForbidden('selected参数 不是布尔类型')

        # 3.判断是否登录
        user = request.user

        if user.is_authenticated:
            # 3.1 登录 redis存储
            # 1.链接redis的数据库
            carts_redis_client = get_redis_connection('carts')

            # 2.根据用户id 获取 所有的数据hgetall()=>bytes k v
            client_data = carts_redis_client.hgetall(user.id)

            if not client_data:
                # 直接新建
                carts_redis_client.hset(user.id, sku_id, json.dumps({'count': count, 'selected': selected}))

            # 3.判断是否 存在 sku_id 在的话 count += count
            if str(sku_id).encode() in client_data:
                # 1.取出原有的 商品
                child_dict = json.loads((client_data[str(sku_id).encode()]).decode())

                # 2.修改 count值 累加
                child_dict['count'] += count

                # 3.告诉redis 修改完毕了
                carts_redis_client.hset(user.id, sku_id, json.dumps(child_dict))

            # 4. 不存在 直接 创建新的 数据
            else:
                carts_redis_client.hset(user.id, sku_id, json.dumps({'count': count, 'selected': selected}))

            # 5. 返回响应
            return JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})

        else:
            # 3.2 未登录 Cookie存储

            # 1.取出cookie的数据 COOKIES
            cookie_str = request.COOKIES.get('carts')
            # 2.判断是否有值  有值:转成明文
            if cookie_str:
                carts_dict = CookieSecret.loads(cookie_str)
            else:
                # 3. 不存在 新建 {}
                carts_dict = {}

            # 4.判断sku_id 有没有, 没有 新建, 有累加个数
            if sku_id in carts_dict:
                # 数据累加
                origin_count = carts_dict[sku_id]['count']
                count += origin_count

            carts_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 5.转成密文
            cookie_cart_str = CookieSecret.dumps(carts_dict)

            # 6.设置cookie
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})
            response.set_cookie('carts', cookie_cart_str, max_age=24 * 30 * 3600)
            # 7.返回响应
            return response

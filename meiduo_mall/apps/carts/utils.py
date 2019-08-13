
import json
from django_redis import get_redis_connection
from utils.cookiesecret import CookieSecret

#封装 购物车合并
def merge_cart_cookie_to_redis(request, user, response):
    """
    登录后合并cookie购物车数据到Redis
    :param request: 本次请求对象，获取cookie中的数据
    :param response: 本次响应对象，清除cookie中的数据
    :param user: 登录用户信息，获取user_id
    :return: response
    """
    # 1.获取cookie_dict 数据
    cookie_str = request.COOKIES.get('carts')#传请求对对象

    # 2.如果没有数据 就响应结果
    if not cookie_str:
        return response

    # 3.解密
    cookie_dict = CookieSecret.loads(cookie_str)

    # 4.合并购物车数据
    carts_redis_client = get_redis_connection('carts')
    carts_data = carts_redis_client.hgetall(user.id)

    # 将carts_data 二进制字典 转换成 普通字典 字典推导式
    carts_dict = {int(data[0].decode()): json.loads(data[1].decode()) for data in carts_data.items()}

    # 更新数据 覆盖字典 update()
    carts_dict.update(cookie_dict)
    # 修改redis的数据
    for sku_id in carts_dict.keys():
        carts_redis_client.hset(user.id, sku_id, json.dumps(carts_dict[sku_id]))

    # 删除cookie值
    response.delete_cookie('carts')
    #改完响应对象，外面的代码还要用，得返回响应对象
    return response
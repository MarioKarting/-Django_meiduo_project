# !/usr/bin/env python
# _*_ coding:utf-8 _*_
import json

import redis

if __name__ == '__main__':
    # 1.复习hash的增伤改查
    redis_client = redis.StrictRedis(db=15)
    user_key = "user_id1"  # hash对象key
    sku_key = "sku_id1"  # hash的属性key
    value = '{"count":1,"selected":"true"}'
    sku_key2 = "sku_id2"  # hash的属性key
    value2 = '{"count":2,"selected":"true"}'
    sku_key3 = "sku_id3"  # hash的属性key
    value3 = '{"count":3,"selected":"true"}'


    # 增加
    redis_client.hset(user_key, sku_key, value)
    redis_client.hset(user_key, sku_key2,value2)
    redis_client.hset(user_key, sku_key3,value3)


    # 查询
    redis_client.hget(user_key, sku_key)
    get_all_data = redis_client.hgetall(user_key)
    # print(get_all_data)

    # 删除
    # redis_client.hdel(user_key, sku_key)

    # 改 hset
    #  如果 value 需要传递字典 --报错: Convert : dict: to be  a bytes or string or number first
    # 1.降级 redis的版本 2.10.6
    # 2.字典 转成 字符串
    # redis_client.hset(user_key, sku_key, {'count':6,"selected":True})



    # 2.数据格式 转换
    # {b'sku_id1': b"{'count':1,'selected':'true'}", b'sku_id2': b"{'count':2,'selected':'true'}", b'sku_id3': b"{'count':3,'selected':'true'}"}
    all_data = redis_client.hgetall(user_key)

    new_data_dict = {}
    for data in all_data.items():
        # print(data)
        # print(type(data))

        # 1.将元祖的key 装换成字符串
        sku_id = data[0].decode()
        # 2.将元祖的val 成字典
        sku_value_dict = json.loads(data[1].decode())

        new_data_dict[sku_id] = sku_value_dict

    # 字典推导式  [i for i in data_list]  {k:v for data in all_data.items()}
    new_dict = {data[0].decode():json.loads(data[1].decode()) for data in all_data.items()}

    # print(all_data)
    # print(new_data_dict)

    print(new_dict)


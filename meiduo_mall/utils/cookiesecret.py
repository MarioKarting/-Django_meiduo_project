# !/usr/bin/env python
# _*_ coding:utf-8 _*_


import json
import pickle
import base64


class CookieSecret(object):
    # 1.加密 dumps
    @classmethod
    def dumps(cls, data):

        # 1.使用pickle 转换 bytes
        pickle_bytes = pickle.dumps(data)

        # 2.使用base64 加密===>bytes
        base64_bytes = base64.b64encode(pickle_bytes)

        # 3.转成字符串
        return base64_bytes.decode()


    # 2.解密 loads
    @classmethod
    def loads(cls, data):
        # 1.使用base64 解密
        base64_bytes = base64.b64decode(data)

        # 2.pickle 转换成 原始数据类型
        return pickle.loads(base64_bytes)



if __name__ == '__main__':
    data_dict = {
        1: {'count': 2, 'selecte': True},
        2: {'count': 3, 'selecte': True}
    }

    # 1.dict====>Str
    # json_str = json.dumps(data_dict)
    # # 2.str====>dict
    # json_dict = json.loads(json_str)
    #
    # # pickle: dict===>bytes
    # pickle_bytes = pickle.dumps(data_dict)
    #
    # # pickle:bytes===>dict
    # pickle_dict = pickle.loads(pickle_bytes)
    #
    # # 1.加密==>bytes
    # dumps_base64_bytes = base64.b64encode(pickle_bytes)
    #
    # # 2.解密
    # loads_base64 = base64.b64decode(dumps_base64_bytes)
    #
    # print(loads_base64)
    # print(type(loads_base64))

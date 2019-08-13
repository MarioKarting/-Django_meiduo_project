# !/usr/bin/env python
# _*_ coding:utf-8 _*_


# 封装 面包屑组件 数据函数--list-detail
def get_breadcrumb(cat3):
    # 1.拿到的是 三级分类

    # 2.三级找二级parent
    cat2 = cat3.parent

    # 3.二级找一级 自连接 parent
    cat1 = cat2.parent

    breadcrumb = {
        'cat1': {
            'name': cat1.name,
            'url': cat1.goodschannel_set.all()[0].url
        },
        'cat2': cat2,
        'cat3': cat3,
    }

    return breadcrumb

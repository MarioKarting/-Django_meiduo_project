# !/usr/bin/env python
# _*_ coding:utf-8 _*_

from collections import OrderedDict


# 封装 商品三级分类查询的数据 函数
def get_categories():
    # 1.1 获取频道表的数据 37个频道 goodschannel
    from apps.goods.models import GoodsChannel
    # channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    channels = GoodsChannel.objects.all()
    # 1.2 遍历37个频道
    categories = OrderedDict()  # 有序的字典
    for channel in channels:
        # 1.3 通过频道 获取 组id 11个
        group_id = channel.group_id
        # 1.4 判断 当前组id 在不在 字典里面,如果不在:塞进去
        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}

        # 1.5 通过外键属性category--获取一级分类
        cat1 = channel.category
        # 1.6 拼接 channels 里面的字典数据
        categories[group_id]['channels'].append({
            'id': cat1,
            'name': cat1.name,
            'url': channel.url,
        })
        # 1.7 根据一级分类找2 .subs, --3 subs级分类 构建前端需要的数据
        for cat2 in cat1.subs.all():
            cat2.sub_cats = []

            # 二级找3级
            for cat3 in cat2.subs.all():
                cat2.sub_cats.append(cat3)

            # 将拼接完毕的ca2 添加到大字典的key里面
            categories[group_id]['sub_cats'].append(cat2)

    return categories

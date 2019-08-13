# !/usr/bin/env python
# _*_ coding:utf-8 _*_


# 生成 首页的静态文件
import os

import time
from django.conf import settings


def generate_static_index_html():

    print('%s: generate_static_index_html' % time.ctime())

    # 1.获取 首页需要的数据
    from apps.contents.utils import get_categories
    categories = get_categories()

    # 2.获取广告数据
    # 2.1 获取所有的广告分类 content_category
    from apps.contents.models import ContentCategory
    content_categories = ContentCategory.objects.all()
    # 2.2 遍历 广告分类
    contents = {}
    for cat in content_categories:
        # 2.3 通过外键属性 获取 广告内容
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

    # 前端数据
    context = {
        'categories': categories,
        'contents': contents
    }

    # 2.获取 模板里面的 index.html
    from django.template import loader
    template = loader.get_template('index.html')

    # 3.渲染 index.html 和 数据
    html_text = template.render(context)

    # 4. 写入本地文件
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)

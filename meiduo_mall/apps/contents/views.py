from django.shortcuts import render

from django.views import View


# 1.首页显示



class IndexView(View):
    def get(self, request):

        # 1.获取首页 商品分类数据
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
           'categories':categories,
            'contents':contents
        }

        return render(request, 'index.html',context)






















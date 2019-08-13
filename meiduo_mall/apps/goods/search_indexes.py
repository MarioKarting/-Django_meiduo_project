# !/usr/bin/env python
# _*_ coding:utf-8 _*_

# 1.导包
from haystack import indexes
from .models import SKU


# .2.继承
class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    # 3.字段的模板文件关联
    text = indexes.CharField(document=True, use_template=True)

    # 4. get_model()
    def get_model(self):
        return SKU

    # 5. index_queryset()
    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_launched=True)

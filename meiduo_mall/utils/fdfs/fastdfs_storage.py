# !/usr/bin/env python
# _*_ coding:utf-8 _*_


# 1.导包
from django.conf import settings
from django.core.files.storage import Storage


# 2.继承
class FastDFSStorage(Storage):
    def __init__(self, fsdf_base_url=None):

        self.fsdf_base_url = fsdf_base_url or settings.FDFS_BASE_URL

    # 3. 在settings.dev.py 配置一下 域名:8888

    # 4. 必须实现 _open _save
    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content, max_length=None):
        pass

    # 5. url 拼接全路径
    def url(self, name):
        # name :group1/M00/00/01/CtM3BVrLmc-AJdVSAAEI5Wm7zaw8639396
        # www..image.meiduo.site:8888/group1/M00/00/01/CtM3BVrLmc-AJdVSAAEI5Wm7zaw8639396

        return self.fsdf_base_url + name

# !/usr/bin/env python
# _*_ coding:utf-8 _*_

# 1.导包
from celery import Celery

# 可能加载django项目的包, 避免找不见
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

# 2. 实例化
app = Celery('celery_tasks')


# 3.加载配置文件
app.config_from_object('celery_tasks.config')


# 4. 自动加载任务
app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email'])
# !/usr/bin/env python
# _*_ coding:utf-8 _*_

class MasterSlaveDBRouter(object):
    """数据库读写路由"""
    #从 数据库从端去读
    def db_for_read(self, model, **hints):
        """读"""
        return "slave"
    #从 数据库主端去写
    def db_for_write(self, model, **hints):
        """写"""
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """是否运行关联操作"""
        return True
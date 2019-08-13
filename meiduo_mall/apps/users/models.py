from django.contrib.auth.models import AbstractUser
from django.db import models

from utils.models import BaseModel


class Address(BaseModel):
    """用户地址"""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses', verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses', verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']



# 2. 使用Django提供的认证系统, 密码直接加密, 提供完整校验流程   继承了抽象用户类
class User(AbstractUser):
    # 缺一个  手机号属性
    mobile = models.CharField(max_length=11,unique=True,verbose_name="手机号")
    #用户中心缺少邮箱字段
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')
    #默认地址
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='默认地址')


    class Meta:
        db_table = "tb_user"
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

# 1.自定义 用户模型 :
# 缺点 1.密码是明文发送不安全 需要自己手动加解密
#     2.将来用户验证 需要手动验证
# class User(models.Model):
#     username = models.CharField(max_length=20)
#     password = models.CharField(max_length=20)
#
#     class Meta:
#         db_table = "meiduo_user"
#
#     def __str__(self):
#         return self.username

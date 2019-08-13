from django.apps import AppConfig

# 不写auth 跟系统重名  啦
class OauthConfig(AppConfig):
    name = 'oauth'

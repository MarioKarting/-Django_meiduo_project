import re

from django.conf import settings
from django.contrib.auth import login
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse

from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django_redis import get_redis_connection
from apps.oauth.models import OAuthQQUser
from apps.users.models import User
from meiduo_mall.settings.dev import logger
from utils.response_code import RETCODE
from apps.oauth import constants
from utils.secret import SecretOauth

# 3.判断openid 是否绑定了
def is_bind_openid(request, openid):
    # 如果绑定了
    try:
        oauth_user = OAuthQQUser.objects.get(openid=openid)

    except Exception as e:
        logger.error(e)
        # 没有绑定了-->重定向到绑定页面
        secret_openid = SecretOauth().dumps({'openid': openid})
        context = {
            'openid': secret_openid
        }
        return render(request, 'oauth_callback.html', context)

    else:
        # 绑定了-保持登录状态->重定向到首页-->设置cookie username
        qq_user = oauth_user.user
        login(request, qq_user)

        # 响应结果
        response = redirect(reverse('contents:index'))

        # 登录时用户名写入到cookie，有效期15天
        response.set_cookie('username', qq_user.username, constants.USERNAME_EXPIRE_TIME)

        return response


# 2.回调网址 code-->token-->openid
class QQAuthView(View):
    def get(self, request):
        # 1.获取code
        code = request.GET.get('code')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state="")

        # 2.使用code--->token
        token = oauth.get_access_token(code)

        # 3.使用token--->openid
        openid = oauth.get_open_id(token)

        # 4.判断openid 是否绑定了 封装
        response = is_bind_openid(request, openid)

        return response

    # 绑定openid
    def post(self, request):
        # 1.接收参数 form POST
        mobile = request.POST.get('mobile')
        pwd = request.POST.get('password')
        sms_code = request.POST.get('sms_code')
        openid = request.POST.get('openid')


        # 2.校验--判空--正则--短信验证码
        # 判断参数是否齐全
        if not all([mobile, pwd]):
            return HttpResponseForbidden('参数不齐')
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('请输入正确的手机号码')
        # 判断密码是否合格
        if not re.match(r'^[0-9A-Za-z]{8,20}$', pwd):
            return HttpResponseForbidden('请输入8-20位的密码')
        # 判断短信验证码是否一致
        sms_code = request.POST.get('msg_code')
        # 6.1 从redis 中取出来
        redis_code_client = get_redis_connection('sms_code')
        redis_code = redis_code_client.get('sms_%s' % mobile)

        if redis_code is None:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '无效的短信验证码'})
        if sms_code != redis_code.decode():
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '输入短信验证码有误'})
            # 判断openid是否有效：错误提示放在sms_code_errmsg位置

        # 3.解密--openid 校验
        openid = SecretOauth().loads(openid).get('openid')
        if not openid:
            return render(request, 'oauth_callback.html', {'openid_errmsg': '无效的openid'})


        # 4.判断用户是否存在 存在 user; 不存在新建user
        try:
            user = User.objects.get(mobile=mobile)
        except Exception as e:
            # 用户不存在 新建user
            user = User.objects.create(username=mobile, password=pwd, mobile=mobile)
        else:
            # 如果用户存在，检查密码     密码不正确
            if not user.check_password(pwd):
                return render(request, 'oauth_callback.html', {'account_errmsg': '用户名或密码错误'})

        # 5.user绑定openid
        try:
            OAuthQQUser.objects.create(openid=openid, user=user)
        except Exception as e:
            return render(request, 'oauth_callback.html', {'qq_login_errmsg': 'QQ登录失败'})

        # 6. 保持登录状态--重定向首页--set_cookie username
        login(request, user)
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username,constants.USERNAME_EXPIRE_TIME)
        return response


# 1.获取qq登录url
class QQAuthURLView(View):
    def get(self, request):
        # 1. 创建 oauth对象
        oauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state=""
        )
        # 2. 获取qq登录网址
        login_url = oauth.get_qq_url()

        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})

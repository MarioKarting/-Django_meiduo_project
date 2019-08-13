# from django import http
import json
import re

from django_redis import get_redis_connection
from django.conf import settings
from django.contrib.auth import logout
from django.http.response import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from apps.carts.utils import merge_cart_cookie_to_redis
from apps.goods.models import SKU
from apps.users import constants
from apps.users.models import User, Address
from meiduo_mall.settings.dev import logger
from utils.response_code import RETCODE

from django.contrib.auth.mixins import LoginRequiredMixin
from utils.secret import SecretOauth



 # 15.记录用户浏览记录
class UseBrosweView(View):
    # 查询记录
    def get(self, request):
        # 1.获取缓存redis中的 sku_ids
        history_redis_client = get_redis_connection('history')
        sku_ids = history_redis_client.lrange('history_%s' % request.user.id, 0, -1)

        # 2.遍历所有sku_ids
        skus = []
        for sku_id in sku_ids:
            # 3.根据id获取sku商品--构建前端的数据格式 [{},{}]
            sku = SKU.objects.get(id=sku_id)

            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
            })

        # 4.返回结果
        return JsonResponse({'code': 0, 'errmsg': "OK", "skus": skus})

    # 新增记录
    def post(self, request):
        # 1.配置 dev.py --redis库
        # 2. users.urls.py 配置子路由
        # 3. users.views.py 写功能
        sku_id = json.loads(request.body.decode()).get('sku_id')
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return HttpResponseForbidden('商品不存在!')

        # 3.1 链接redis数据库
        history_redis_client = get_redis_connection('history')
        history_key = 'history_%s' % request.user.id

        # 管道操作
        p1 = history_redis_client.pipeline()

        # 3.2 去重
        p1.lrem(history_key, 0, sku_id)
        # 3.3 存储
        p1.lpush(history_key, sku_id)
        # 3.4 切片截取 5个
        p1.ltrim(history_key, 0, 4)

        # 管道执行
        p1.execute()

        # 4.返回结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


# 14.密码操作
class ChangePasswordView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'user_center_pass.html')

    def post(self, request):
        # 1.接收参数
        old_password = request.POST.get('old_pwd')
        new_password = request.POST.get('new_pwd')
        new_password2 = request.POST.get('new_cpwd')

        # 2.校验:判空 — 正则—密码正确 check_password()
        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return http.HttpResponseForbidden('缺少必传参数')

        ret = request.user.check_password(old_password)
        if ret ==False:
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        if new_password != new_password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')


        # 3.修改 user.密码 set_password(加密)
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码失败'})

        # 4.logout()
        logout(request)

        # 5.重定向到登录页
        response = redirect(reverse('users:login'))

        # 6.清空cookie
        response.delete_cookie('username')

        return response




# 13. 修改标题
class UpdateTitleAddressView(View):
    def put(self, request, address_id):

        # 1.获取title  Json
        title = json.loads(request.body.decode()).get('title')

        try:
            # 2. 根据id获取 address
            address = Address.objects.get(id=address_id)
            # 3. 修改  address.title = title
            address.title = title
            # 4. save()
            address.save()

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置地址标题失败'})

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})


# 12 .设置默认地址
class DefaultAddressView(View):
    def put(self, request, address_id):

        try:
            # 1.根据id查地址
            address = Address.objects.get(id=address_id)

            # 2.修改当前用户的默认地址 default_address
            request.user.default_address = address

            # 3. save()
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


# 11.修改地址
class UpdateAddressView(View):
    # 修改
    def put(self, request, address_id):

        # 1.拼接参数, jSOn参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 2.校验,判空正则
        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 3.修改 address_id 对应的 地址的属性
        try:
            address = Address.objects.get(id=address_id)
            address.user = request.user
            address.title = receiver
            address.receiver = receiver
            address.province_id = province_id
            address.city_id = city_id
            address.district_id = district_id
            address.place = place
            address.mobile = mobile
            address.tel = tel
            address.email = email
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})

        # 4.构建前端需要的数据格式 { }
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '更新地址成功', 'address': address_dict})

    # 删除地址
    def delete(self, request, address_id):

        try:
            # 1.获取当前的地址  address_id对应
            address = Address.objects.get(id=address_id)
            # 2. 修改is_deleted = True
            address.is_deleted = True
            # 3. save()
            address.save()

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})

# 10.新增地址
class CreateAddressView(LoginRequiredMixin, View):
    def post(self, request):

        # 判断总的地址个数, 大于20 不允许在添加
        count = Address.objects.filter(user=request.user, is_deleted=False).count()
        count = request.user.addresses.filter(is_deleted=False).count()

        if count >= 20:
            return JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超过地址数量上限'})

        # 1.接收参数 JSON
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 2.校验 判空not all[], 正则

        # 3.入库
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email,
            )

            # 判断用户 是否有默认地址, 没有默认地址自动绑定一个
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()


        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})

        # 4.构建前端要的数据json ; dict
        address_dict = {
            "id": address.id,
            "title": address.receiver,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email,
        }
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})


# 9.收货地址
class AddressView(View):
    def get(self, request):
        # 1.取出当前用户的 所有地址 没有删除的
        addresses = Address.objects.filter(user=request.user, is_deleted=False)

        # 2.构建前端需要的数据格式 列表字典
        address_list = []
        for address in addresses:
            address_list.append({
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })

        context = {
            'default_address_id': request.user.default_address_id,
            "addresses": address_list
        }

        return render(request, 'user_center_site.html', context)


# 8.激活邮箱
class VerifyEmailView(View):
    def get(self, request):
        # 1.接收参数  token
        token = request.GET.get('token')

        # 2.解密 token
        token_dict = SecretOauth().loads(token)

        # 3.校验 userid email
        try:
            user = User.objects.get(id=token_dict['user_id'], email=token_dict['email'])
        except Exception as e:
            return HttpResponseForbidden('无效的token')

        # 4. 修改 email_active
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('激活邮件失败')

        # 5.成功 重定向的首页
        return redirect(reverse('contents:index'))

# 7.增加邮箱
class EmailView(LoginRequiredMixin, View):
    def put(self, request):

        # 1.接收参数 email
        email = json.loads(request.body.decode()).get('email')

        # 2.校验邮箱 正则

        # 3. 存到该用户的email属性
        try:
            request.user.email = email
            request.user.save()

        except Exception as e:
            return JsonResponse({'code': RETCODE.EMAILERR, 'errmsg': '添加邮箱失败'})

        # 发邮件 耗时操作
        from apps.users.utils import generate_verify_email_url
        verify_url = generate_verify_email_url(request.user)
        from celery_tasks.email.tasks import send_verify_email
        send_verify_email.delay(email, verify_url)

        # 4. 返回前端的数据响应
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


# 6.个人中心
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        # 1.user_id --cookie取出usertname 判断
        # 2. request.user
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active,
        }

        return render(request, 'user_center_info.html', context)

# 5.退出登录
class LogoutView(View):
    def get(self, request):
        # 1.退出 清空session
        from django.contrib.auth import logout
        logout(request)

        # 2. 清空cookie
        response =  redirect(reverse('users:login'))
        response.delete_cookie('username')
        return response


# 4.登录页
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 1.接收三个参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        # 2.校验参数
        if not all([username, password]):
            return HttpResponseForbidden('参数不齐全')
        # 2.1 用户名
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseForbidden('请输入5-20个字符的用户名')
        # 2.2 密码
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')

        # 3.验证用户名和密码--django自带的认证
        from django.contrib.auth import authenticate, login
        user = authenticate(username=username, password=password)

        # 如果user不存在 重新登录 --render login.html
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 4.保持登录状态
        login(request, user)

        # 5.是否记住用户名
        if remembered != 'on':
            # 不记住用户名 , 过期时间 0
            request.session.set_expiry(0)
        else:
            # 记住用户名,  过期时间  默认 2周
            request.session.set_expiry(None)

        #接收next的值==路由
        next = request.GET.get('next')
        if next:
            response = redirect(next)
        else:
            # 6.返回响应结果
            response = redirect(reverse('contents:index'))

        #合并购物车
        response = merge_cart_cookie_to_redis(request=request, user=user, response=response)

        response.set_cookie('username', username, constants.USERNAME_EXPIRE_TIME)
        return response


# 3.判断手机号是否重
class MobileCountView(View):
    def get(self, request, mobile):
        # 1.接收 校验参数-路径里面已经正则校验过了

        # 2. 去数据库 查询 手机号的 个数
        count = User.objects.filter(mobile=mobile).count()

        # 3.返回给前端数据 Json
        from utils.response_code import RETCODE
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'count': count})


# 2.判断用户名是否重复
class UsernameCountView(View):
    def get(self, request, username):
        # 1.校验正则 是否符合

        # 2.去数据库校验 count
        from apps.users.models import User
        count = User.objects.filter(username=username).count()

        # 3.返回响应结果
        from utils.response_code import RETCODE
        return JsonResponse({
            "code": '0',
            "errmsg": "ok",
            "count": count,
        })


# 1.定义注册类视图
class RegisterView(View):
    # 1.显示注册页面
    def get(self, request):
        return render(request, 'register.html')

    # 2.注册提交功能
    def post(self, request):

        # 1.接收解析参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')

        # 2.校验 判空 正则
        if not all([username, password, password2, mobile, allow]):
            return HttpResponseForbidden('参数不全!')

        # 2.1 用户名
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseForbidden('请输入5-20个字符的用户名')
        # 2.2 密码
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')
        # 2.3 二次校验
        if password != password2:
            return HttpResponseForbidden('两次密码不一致!')
        # 2.4 手机号
        if not re.match(r'^1[345789]\d{9}$', mobile):
            return HttpResponseForbidden('您输入的手机号格式不正确')
        # 2.5 是否点击同意
        if allow != 'on':
            return HttpResponseForbidden('请勾选用户同意!')

        # 2.6 校验 短信验证码
        # 2.6.1 接收前端的验证码
        sms_code = request.POST.get('msg_code')

        # 2.6.2 校验判空, 正则, 和后台的验证码对比
        from django_redis import get_redis_connection
        redis_code_client = get_redis_connection('sms_code')
        redis_code = redis_code_client.get('sms_%s' % mobile)

        if redis_code is None:
            return render(request, 'register.html', {'sms_code_errmsg': '无效的短信验证码'})
        # 千万注意: redis取出来的 bytes ===>decode()  str
        if redis_code.decode() != sms_code:
            return render(request, 'register.html', {'sms_code_errmsg': '不正确的短信验证码'})


        # 3.注册用户数据
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                mobile=mobile,
            )
        except:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})
        # 保持登陆状态
        from django.contrib.auth import login
        login(request,user)

        # 4.重定向到首页
        # return redirect('/')
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', username, constants.USERNAME_EXPIRE_TIME)
        return response

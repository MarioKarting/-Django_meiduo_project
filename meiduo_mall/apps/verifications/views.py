import random

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View

# # 2.获取短信验证码
from django_redis import get_redis_connection

from apps.verifications import constants
from meiduo_mall.settings.dev import logger


class SMSCodeView(View):
    def get(self, request, mobile):

        # *   2.1 接收图片验证码
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # *   2.2 校验图片验证码的正确性--redis_image_code 一样; null 过期了, 不一致,写错了
        try:
            img_redis_client = get_redis_connection('verify_image_code')
            redis_img_code = img_redis_client.get("img_%s" % uuid)

            if not redis_img_code:
                return JsonResponse({'code': "4001", 'errmsg': '图形验证码失效了'})

            # 千万注意: redis返回的是 bytes 不能直接对比 bytes.decode()
            if redis_img_code.decode().lower() != image_code.lower():
                return JsonResponse({'code': "4001", 'errmsg': '图形验证码错误!'})
            # 删除以前的图片验证码
            img_redis_client.delete("img_%s" % uuid)
        except Exception as e:
            logger.error(e)

        # 频繁发送短信验证码
        sms_redis_client = get_redis_connection('sms_code')
        #1.取出 redis 保存发短信标识
        send_flag = sms_redis_client.get('send_flag_%s' % mobile)
        import json
        if send_flag:
            ret = {'code': "4002", 'errmsg': '发送短信过于频繁'}
            # return JsonResponse({'code': "4002", 'errmsg': '发送短信过于频繁'},json_dumps_params={'ensure_ascii':False},content_type="application/json,charset=utf-8")
            return HttpResponse(json.dumps(ret,ensure_ascii=False),content_type="application/json,charset=utf-8")

        # *   2.3 生成短信验证码 6位 随机码 random.radint(0,999999)
        sms_code = '%06d' % random.randint(0, 999999)
        # *   2.4 redis存储 短信验证码
        try:
            p1=sms_redis_client.pipeline()
            p1.setex('send_flag_%s' % mobile,constants.SMSCODE_SEND_TIME,1)
            p1.setex('sms_%s' % mobile,constants.SMSCODE_EXPIRE_TIME, sms_code)
            p1.execute()
        except Exception as e:
            logger.error(e)

        # *   2.5 容联云发送短信
        # from libs.yuntongxun.sms import CCP
                            #   手机号   验证码 过期时间 1短信模板
        # CCP().send_template_sms(mobile,[sms_code,5],1)
        # print(sms_code)
        # *   2.5 容联云发送短信---celery异步发送
        from celery_tasks.sms.tasks import send_sms_code
        send_sms_code.delay(mobile, sms_code)

        # *   2.6 发送短信完毕--让前端 倒计时 60秒
        return JsonResponse({'code': '0', 'errmsg': '发送短信成功'},json_dumps_params={'ensure_ascii':False})


# 1.获取图片验证码 GET
class ImageCodeView(View):
    def get(self, request, uuid):
        # 1.校验 uuid , 正则 已经校验过了

        # 2.生成图片验证码
        from libs.captcha.captcha import captcha
        text, image_code = captcha.generate_captcha()

        # 3.想redis缓存 存 验证码text
        from django_redis import get_redis_connection
        image_redis_client = get_redis_connection('verify_image_code')
        image_redis_client.setex("img_%s" % uuid, 300, text)

        # 4.返回图片验证码 image_code
        return HttpResponse(image_code, content_type='image/jpeg')

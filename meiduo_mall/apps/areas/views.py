from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.areas.models import Area
from utils.response_code import RETCODE
from django.core.cache import cache


class AreasView(View):
    def get(self, request):

        """
         省   select * from tb_areas where parent_id is null;
         市    select * from tb_areas where parent_id=130000;
         区县   select * from tb_areas where parent_id=130100;
        """
        # 1.接收 外界 传入的 area_id
        area_id = request.GET.get('area_id')

        # 如果area_id没有 就是 省份
        if not area_id:

            # 1.从缓存取出 数据,如果有 不交互数据库, 没有才交互数据库
            province_list = cache.get('province_list')
            if not province_list:
                print('缓存失效了')
                try:
                    provinces = Area.objects.filter(parent__isnull=True)

                    # 组合前端需要的数据格式
                    province_list = []
                    for pro in provinces:
                        province_list.append({'id': pro.id, 'name': pro.name})
                        # province_list = [{'id': pro.id, 'name': pro.name} for pro in provinces]

                except Exception as e:
                    return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '获取失败'})

                # 2. 存入缓存
                cache.set('province_list', province_list, 10 * 60)

            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        else:

            # 1.从缓存取出 数据,如果有 不交互数据库, 没有才交互数据库
            sub_data = cache.get('sub_'+ area_id)

            if not sub_data:
                # 如果area_id有 就是 市 或者区县
                # 根据area_id 获取 上级
                parent_model = Area.objects.get(id=area_id)

                # 根据上级取出下级
                subs = parent_model.subs.all()

                subs_list = []
                for sub in subs:
                    subs_list.append({'id': sub.id, 'name': sub.name})

                sub_data = {
                    'id': parent_model.id,
                    'name': parent_model.name,
                    'subs': subs_list
                }

                # 2. 存入缓存
                cache.set('sub_'+ area_id, sub_data, 10 * 60)



            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})





            # def get(self, request):
            #
            #     """
            #      省   select * from tb_areas where parent_id is null;
            #      市    select * from tb_areas where parent_id=130000;
            #      区县   select * from tb_areas where parent_id=130100;
            #     """
            #     # 1.接收 外界 传入的 area_id
            #     area_id = request.GET.get('area_id')
            #
            #     # 如果area_id没有 就是 省份
            #     if not area_id:
            #
            #         try:
            #             provinces = Area.objects.filter(parent__isnull=True)
            #
            #             # 组合前端需要的数据格式
            #             province_list = []
            #             for pro in provinces:
            #                 province_list.append({'id': pro.id, 'name': pro.name})
            #             # province_list = [{'id': pro.id, 'name': pro.name} for pro in provinces]
            #
            #         except Exception as e:
            #             return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '获取失败'})
            #
            #         return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
            #     else:
            #
            #         # 如果area_id有 就是 市 或者区县
            #         subs = Area.objects.filter(parent_id=area_id)
            #
            #         subs_list = []
            #         for sub in subs:
            #             subs_list.append({'id':sub.id,'name':sub.name})
            #
            #         sub_data = {
            #             'subs':subs_list
            #         }
            #
            #         return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})

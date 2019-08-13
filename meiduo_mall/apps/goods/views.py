from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.views import View

from apps.contents.utils import get_categories
from apps.goods.models import GoodsCategory, SKU, GoodsVisitCount
from apps.goods.utils import get_breadcrumb
from utils.response_code import RETCODE


# 4.访问量
class DetailVisitView(View):
    def post(self, request, category_id):

        # 1.根据id 找 商品分类
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return HttpResponseNotFound('商品分类不存在')

        # 2.获取当天的日期 进行格式化处理
        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        # 将处理完的日期字符串 转换成 日期类型
        today_date = datetime.strptime(today_str, '%Y-%m-%d')

        # 3.判断一下 商品分类-->对应的(当天日期)访问量的数据 有还是没有
        try:
            count_data = category.goodsvisitcount_set.get(date=today_date)
        except Exception as e:
            # 3.2 没有 新建模型对象
            count_data = GoodsVisitCount()

        # 4.无论又还是没有记录  累加 += 1 保存数据
        try:
            count_data.count += 1
            count_data.category = category
            count_data.save()
        except Exception as e:
            return HttpResponseNotFound('记录失败了!')

        # 5. 返回前端 告诉记录成功
        return JsonResponse({'code': 0, 'errmsg': 'OK'})


# 3. 详情页
class DetailView(View):
    def get(self, request, sku_id):

        # 获取当前sku的信息
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)

        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        # 渲染页面
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,
        }
        return render(request, 'detail.html', context)


# 2.热销商品 排行
class HotView(View):
    def get(self, request, category_id):
        # 1.根据 category_id 获取上架商品--安销量降序--取前两个
        try:
            skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]

        except Exception as e:
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '没有当前的商品', 'hot_skus': []})

        # 2.构建前端需要的数据格式
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })

        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})

# 1.列表页
class ListView(View):
    def get(self, request, category_id, page_num):
        # 获取三级分类的对象
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return HttpResponseNotFound('商品分类不存在')

        # 1.商品分类数据
        from apps.contents.utils import get_categories
        categories = get_categories()

        # 2.面包屑组件数据
        from apps.goods.utils import get_breadcrumb
        breadcrumb = get_breadcrumb(category)

        # 3. 排序
        # 3.1 获取sort 里面的参数值 查询参数
        sort = request.GET.get('sort', 'default')

        # 3.2 判断 排序的字段值    sort 模型对象
        if sort == 'price':
            sort_field = 'price'
        elif sort == 'hot':
            sort_field = '-sales'
        else:
            # 默认都是 创建时间排序
            sort_field = 'create_time'

        # 3.3 根据排序规则 获取category_id 对应的所有 上架的商品
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(sort_field)

        # 4. 分页--django提供了分页器
        # 4.1 实例化 分页器(分页的数据,每页显示的个数)==>返回每页显示的数据skus
        from django.core.paginator import Paginator
        paginator = Paginator(skus, 5)
        # 4.2 告诉分页器 当前显示的页数
        try:
            page_skus = paginator.page(page_num)
        except Exception as e:
            return HttpResponseNotFound('当前页数超出范围了!')

        # 4.3 获取总页数
        total_page = paginator.num_pages

        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sort': sort,  # 排序字段
            'category': category,  # 第三级分类
            'page_skus': page_skus,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码

        }
        return render(request, 'list.html', context)

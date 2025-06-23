from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Category, Product, Review, Wishlist
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ReviewSerializer, WishlistSerializer
)

# GET /api/products/ - List all products (replaces store view)
class ProductListView(generics.ListAPIView):

    queryset = Product.objects.all().select_related('category').prefetch_related('reviews', 'images') 
    serializer_class = ProductListSerializer

    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Add filtering options
        category = self.request.query_params.get('category', None)
        search = self.request.query_params.get('search', None)
        
        if category:
            queryset = queryset.filter(category__slug=category)
        if search:
            queryset = queryset.filter(name__icontains=search)
            
        return queryset

# GET /api/categories/ - List all categories
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all().prefetch_related('product')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

# GET /api/products/<slug>/ - Get specific product (replaces product_info view)
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all().select_related('category').prefetch_related(
        'gallery_images', 'reviews__user', 'related_products'
    )
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]

# GET /api/categories/<slug>/products/ - Get products by category (replaces list_category view)
@api_view(['GET'])
@permission_classes([AllowAny])
def category_products(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category).select_related('category').prefetch_related('reviews')
    
    category_data = CategorySerializer(category).data
    products_data = ProductListSerializer(products, many=True).data
    
    return Response({
        'category': category_data,
        'products': products_data,
        'total_products': products.count()
    })

# Additional useful endpoints for your React app

# POST /api/products/<slug>/reviews/ - Add review to product
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_product_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    
    # Check if user already reviewed this product
    if Review.objects.filter(product=product, user=request.user).exists():
        return Response(
            {'error': 'You have already reviewed this product'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(product=product, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# GET/POST /api/wishlist/ - Get user's wishlist or add to wishlist
class WishlistView(generics.ListCreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')
    
    def perform_create(self, serializer):
        product_id = self.request.data.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        # Check if already in wishlist
        if Wishlist.objects.filter(user=self.request.user, product=product).exists():
            return Response(
                {'error': 'Product already in wishlist'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(user=self.request.user, product=product)

# DELETE /api/wishlist/<id>/ - Remove from wishlist
class WishlistDeleteView(generics.DestroyAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    






# views.py
import json
import re
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.db.models import Q
from openai import OpenAI


# استيراد النماذج (تأكد من تعديل المسار حسب تطبيقك)
from .models import Color


# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

@csrf_exempt
@require_http_methods(["POST"])
def product_assistant_stream(request):
    """
    Endpoint يحلل رسالة المستخدم ويحدد إذا كان يحتاج منتج أم لا
    إذا كان يحتاج منتج: يرجع JSON format مع TYPE و COLOR ويبحث في المنتجات
    إذا لم يكن يحتاج: يرجع رد طبيعي من الموقع
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        user_message = data.get('message', '')
        website_name = data.get('website_name', 'موقعنا')
        
        if not user_message:
            return JsonResponse({
                'error': 'الرسالة مطلوبة'
            }, status=400)
        
        # الحصول على الفئات والألوان المتاحة لتحسين دقة البحث
        available_categories = list(Category.objects.values_list('name', flat=True))
        available_colors = list(Color.objects.values_list('name', flat=True))
        
        def generate_response():
            try:
                # System prompt محسن مع بيانات المنتجات الفعلية
                analysis_prompt = f"""
أنت مساعد ذكي لموقع {website_name} للأثاث والمفروشات.

الفئات المتاحة: {', '.join(available_categories)}
الألوان المتاحة: {', '.join(available_colors)}

مهمتك تحليل رسالة المستخدم وتحديد إذا كان:
1. يبحث عن منتج معين (أثاث، مفروشات، ديكور، إلخ)
2. يسأل سؤال عام أو يتحدث بشكل طبيعي

إذا كان المستخدم يبحث عن منتج:
- أرجع JSON format فقط بهذا الشكل: {{"product_search": true, "type": "نوع المنتج", "color": "اللون أو قائمة الألوان", "category": "الفئة إن وجدت"}}
- TYPE يجب أن يكون من الفئات المتاحة أو وصف دقيق للمنتج
- COLOR يجب أن يكون من الألوان المتاحة أو "أي لون" إذا لم يحدد
- CATEGORY يجب أن يكون من الفئات المتاحة

إذا كان المستخدم لا يبحث عن منتج:
- أرجع رد طبيعي ومفيد باسم موقع {website_name}

رسالة المستخدم: "{user_message}"
"""

                # استدعاء ChatGPT للتحليل
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": analysis_prompt}
                    ],
                    max_tokens=300,
                    temperature=0.3,
                    stream=True
                )
                
                full_response = ""
                
                # Stream the response
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        
                        # Send chunk as SSE format
                        yield f"data: {json.dumps({'chunk': content}, ensure_ascii=False)}\n\n"
                
                # تحليل الإجابة النهائية والبحث في المنتجات
                try:
                    if '"product_search": true' in full_response or '"product_search":true' in full_response:
                        # استخراج JSON من الإجابة
                        json_match = re.search(r'\{.*"product_search".*\}', full_response, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            product_data = json.loads(json_str)
                            
                            # البحث في المنتجات الفعلية
                            products_found = search_products_by_criteria(product_data)
                            
                            # إرسال النتائج
                            result_data = {
                                'final_result': 'product_search',
                                'search_criteria': product_data,
                                'products_found': len(products_found),
                                'products': products_found[:10]  # أول 10 منتجات
                            }
                            yield f"data: {json.dumps(result_data, ensure_ascii=False)}\n\n"
                        else:
                            yield f"data: {json.dumps({'final_result': 'normal_response', 'message': full_response}, ensure_ascii=False)}\n\n"
                    else:
                        yield f"data: {json.dumps({'final_result': 'normal_response', 'message': full_response}, ensure_ascii=False)}\n\n"
                        
                except json.JSONDecodeError:
                    yield f"data: {json.dumps({'final_result': 'normal_response', 'message': full_response}, ensure_ascii=False)}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                error_message = f"عذراً، حدث خطأ في {website_name}. يرجى المحاولة مرة أخرى."
                yield f"data: {json.dumps({'error': error_message}, ensure_ascii=False)}\n\n"
        
        response = StreamingHttpResponse(generate_response(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'بيانات JSON غير صحيحة'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'error': 'حدث خطأ في الخادم',
            'details': str(e)
        }, status=500)


def search_products_by_criteria(criteria):
    """
    دالة للبحث في المنتجات حسب المعايير المحددة
    """
    try:
        # بدء الاستعلام الأساسي
        queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('reviews', 'images')
        
        # البحث حسب النوع/الاسم
        if criteria.get('type'):
            product_type = criteria['type']
            queryset = queryset.filter(
                Q(name__icontains=product_type) |
                Q(description__icontains=product_type) |
                Q(short_description__icontains=product_type)
            )
        
        # البحث حسب الفئة
        if criteria.get('category'):
            category = criteria['category']
            queryset = queryset.filter(
                Q(category__name__icontains=category) |
                Q(category__slug__icontains=category)
            )
        
        # البحث حسب اللون
        if criteria.get('color') and criteria['color'] != 'أي لون':
            colors = criteria['color']
            if isinstance(colors, list):
                color_q = Q()
                for color in colors:
                    color_q |= Q(available_colors__name__icontains=color)
                queryset = queryset.filter(color_q)
            else:
                queryset = queryset.filter(available_colors__name__icontains=colors)
        
        # ترتيب النتائج (المنتجات المميزة أولاً، ثم الأحدث)
        queryset = queryset.distinct().order_by('-is_featured', '-created_at')
        
        products = queryset[:20]  # أول 20 منتج
        
        # تحويل إلى JSON format
        products_data = []
        for product in products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'sale_price': float(product.sale_price) if product.sale_price else None,
                'effective_price': float(product.effective_price),
                'discount_percentage': product.discount_percentage,
                'category': product.category.name if product.category else None,
                'is_featured': product.is_featured,
                'is_on_sale': product.is_on_sale,
                'is_in_stock': product.is_in_stock,
                'average_rating': product.average_rating,
                'review_count': product.review_count,
                'colors': [color.name for color in product.available_colors.all()],
                'short_description': product.short_description,
            }
            
            # إضافة الصورة الرئيسية
            main_image = product.images.filter(is_primary=True).first()
            if main_image:
                product_data['main_image'] = main_image.image.url
            
            products_data.append(product_data)
        
        return products_data
        
    except Exception as e:
        return []


# API endpoint منفصل للبحث المباشر في المنتجات
@csrf_exempt
@require_http_methods(["GET"])
def search_products_api(request):
    """
    API endpoint للبحث المباشر في المنتجات
    """
    try:
        # استخراج معايير البحث من query parameters
        search_criteria = {
            'type': request.GET.get('type', ''),
            'color': request.GET.getlist('color'),  # يدعم ألوان متعددة
            'category': request.GET.get('category', ''),
            'min_price': request.GET.get('min_price'),
            'max_price': request.GET.get('max_price'),
            'featured_only': request.GET.get('featured_only', 'false').lower() == 'true',
            'in_stock_only': request.GET.get('in_stock_only', 'true').lower() == 'true'
        }
        
        # تنظيف البيانات الفارغة
        search_criteria = {k: v for k, v in search_criteria.items() if v}
        
        # البحث في المنتجات
        products = search_products_advanced(search_criteria)
        
        return JsonResponse({
            'success': True,
            'search_criteria': search_criteria,
            'products_found': len(products),
            'products': products
        }, json_dumps_params={'ensure_ascii': False})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ في البحث: {str(e)}'
        }, status=500, json_dumps_params={'ensure_ascii': False})


def search_products_advanced(criteria):
    """
    دالة بحث متقدمة للمنتجات مع خيارات إضافية
    """
    try:
        # بدء الاستعلام الأساسي
        queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('reviews', 'images')
        
        # فلترة المنتجات المتوفرة فقط
        if criteria.get('in_stock_only', True):
            queryset = queryset.filter(stock_quantity__gt=0)
        
        # فلترة المنتجات المميزة فقط
        if criteria.get('featured_only'):
            queryset = queryset.filter(is_featured=True)
        
        # البحث حسب النوع/الاسم
        if criteria.get('type'):
            product_type = criteria['type']
            queryset = queryset.filter(
                Q(name__icontains=product_type) |
                Q(description__icontains=product_type) |
                Q(short_description__icontains=product_type)
            )
        
        # البحث حسب الفئة
        if criteria.get('category'):
            category = criteria['category']
            queryset = queryset.filter(
                Q(category__name__icontains=category) |
                Q(category__slug__icontains=category)
            )
        
        # البحث حسب اللون
        colors = criteria.get('color')
        if colors and colors != ['أي لون']:
            if isinstance(colors, list) and len(colors) > 0:
                color_q = Q()
                for color in colors:
                    if color and color != 'أي لون':
                        color_q |= Q(available_colors__name__icontains=color)
                if color_q:
                    queryset = queryset.filter(color_q)
        
        # فلترة حسب السعر
        if criteria.get('min_price'):
            try:
                min_price = float(criteria['min_price'])
                queryset = queryset.filter(price__gte=min_price)
            except ValueError:
                pass
        
        if criteria.get('max_price'):
            try:
                max_price = float(criteria['max_price'])
                queryset = queryset.filter(price__lte=max_price)
            except ValueError:
                pass
        
        # ترتيب النتائج
        queryset = queryset.distinct().order_by('-is_featured', '-is_on_sale', '-created_at')
        
        products = queryset[:20]  # أول 20 منتج
        
        # تحويل إلى JSON format
        products_data = []
        for product in products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'sale_price': float(product.sale_price) if product.sale_price else None,
                'effective_price': float(product.effective_price),
                'discount_percentage': product.discount_percentage,
                'category': {
                    'id': product.category.id if product.category else None,
                    'name': product.category.name if product.category else None,
                    'slug': product.category.slug if product.category else None
                },
                'is_featured': product.is_featured,
                'is_on_sale': product.is_on_sale,
                'is_in_stock': product.is_in_stock,
                'stock_quantity': product.stock_quantity,
                'average_rating': product.average_rating,
                'review_count': product.review_count,
                'colors': [{'id': color.id, 'name': color.name} for color in product.available_colors.all()],
                'short_description': product.short_description,
                'sku': product.sku,
                'condition': product.condition,
            }
            
            # إضافة الصورة الرئيسية
            main_image = product.images.filter(is_primary=True).first()
            if main_image and main_image.image:
                product_data['main_image'] = main_image.image.url
            else:
                # إضافة أول صورة متاحة
                first_image = product.images.first()
                if first_image and first_image.image:
                    product_data['main_image'] = first_image.image.url
                else:
                    product_data['main_image'] = None
            
            products_data.append(product_data)
        
        return products_data
        
    except Exception as e:
        return []

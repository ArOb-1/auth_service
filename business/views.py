from django.views.decorators.http import require_http_methods

from auth_core.permissions import require_permission
from auth_core.utils import parse_body, success, error
from access_control.choices import Resource, Action, Scope

from .models import Shop, Product, Order, Review
from .choices import ProductStatus, OrderStatus


@require_http_methods(['GET'])
@require_permission(Resource.SHOP, Action.READ)
def shop_list(request):
    if request.scope == Scope.OWN:
        shops = Shop.objects.filter(owner=request.user)
    else:
        shops = Shop.objects.all()

    data = [
        {
            'id': str(s.id),
            'name': s.name,
            'description': s.description,
            'owner_id': str(s.owner_id),
            'created_at': s.created_at.isoformat(),
        }
        for s in shops
    ]
    return success({'shops': data})


@require_http_methods(['POST'])
@require_permission(Resource.SHOP, Action.CREATE)
def shop_create(request):
    try:
        body = parse_body(request)
    except ValueError as e:
        return error(str(e))

    name = body.get('name', '').strip()
    description = body.get('description', '').strip()

    if not name:
        return error('name is required')

    shop = Shop.objects.create(
        name=name,
        description=description,
        owner=request.user,
    )
    return success({'shop_id': str(shop.id)}, status=201)


@require_http_methods(['GET'])
@require_permission(Resource.SHOP, Action.READ)
def shop_detail(request, shop_id):
    try:
        shop = Shop.objects.get(id=shop_id)
    except Shop.DoesNotExist:
        return error('Shop not found', status=404)

    return success({
        'id': str(shop.id),
        'name': shop.name,
        'description': shop.description,
        'owner_id': str(shop.owner_id),
        'created_at': shop.created_at.isoformat(),
    })


@require_http_methods(['PATCH'])
@require_permission(Resource.SHOP, Action.UPDATE)
def shop_update(request, shop_id):
    try:
        shop = Shop.objects.get(id=shop_id)
    except Shop.DoesNotExist:
        return error('Shop not found', status=404)

    if request.scope == Scope.OWN and shop.owner != request.user:
        return error('Permission denied', status=403)

    try:
        body = parse_body(request)
    except ValueError as e:
        return error(str(e))

    if 'name' in body:
        shop.name = body['name'].strip()
    if 'description' in body:
        shop.description = body['description'].strip()

    shop.save()
    return success({'shop_id': str(shop.id)})


@require_http_methods(['DELETE'])
@require_permission(Resource.SHOP, Action.DELETE)
def shop_delete(request, shop_id):
    try:
        shop = Shop.objects.get(id=shop_id)
    except Shop.DoesNotExist:
        return error('Shop not found', status=404)

    if request.scope == Scope.OWN and shop.owner != request.user:
        return error('Permission denied', status=403)

    shop.delete()
    return success({'message': 'Shop deleted'})


@require_http_methods(['GET'])
@require_permission(Resource.PRODUCT, Action.READ)
def product_list(request):
    scope = request.scope

    if scope == Scope.ALL:
        products = Product.objects.select_related('shop').all()
    elif scope == Scope.OWN_SHOP:
        products = (Product.objects
                    .select_related('shop')
                    .filter(shop__owner=request.user))
    else:
        products = (Product.objects
                    .select_related('shop')
                    .filter(status=ProductStatus.PUBLISHED))

    data = [
        {
            'id': str(p.id),
            'name': p.name,
            'price': str(p.price),
            'status': p.status,
            'shop_id': str(p.shop_id),
            'created_at': p.created_at.isoformat(),
        }
        for p in products
    ]
    return success({'products': data})


@require_http_methods(['POST'])
@require_permission(Resource.PRODUCT, Action.CREATE)
def product_create(request):
    try:
        body = parse_body(request)
    except ValueError as e:
        return error(str(e))

    name = body.get('name', '').strip()
    price = body.get('price')
    shop_id = body.get('shop_id', '').strip()

    if not name or price is None or not shop_id:
        return error('name, price and shop_id are required')

    try:
        shop = Shop.objects.get(id=shop_id, owner=request.user)
    except Shop.DoesNotExist:
        return error('Shop not found or not yours', status=404)

    product = Product.objects.create(
        name=name,
        price=price,
        shop=shop,
        status=ProductStatus.DRAFT,
    )
    return success({'product_id': str(product.id)}, status=201)


@require_http_methods(['GET'])
@require_permission(Resource.PRODUCT, Action.READ)
def product_detail(request, product_id):
    try:
        product = Product.objects.select_related('shop').get(id=product_id)
    except Product.DoesNotExist:
        return error('Product not found', status=404)

    scope = request.scope

    if scope == Scope.PUBLISHED and product.status != ProductStatus.PUBLISHED:
        return error('Product not found', status=404)

    if scope == Scope.OWN_SHOP and product.shop.owner != request.user:
        return error('Permission denied', status=403)

    return success({
        'id': str(product.id),
        'name': product.name,
        'price': str(product.price),
        'status': product.status,
        'shop_id': str(product.shop_id),
        'created_at': product.created_at.isoformat(),
    })


@require_http_methods(['PATCH'])
@require_permission(Resource.PRODUCT, Action.UPDATE)
def product_update(request, product_id):
    try:
        product = Product.objects.select_related('shop').get(id=product_id)
    except Product.DoesNotExist:
        return error('Product not found', status=404)

    if request.scope == Scope.OWN_SHOP and product.shop.owner != request.user:
        return error('Permission denied', status=403)

    try:
        body = parse_body(request)
    except ValueError as e:
        return error(str(e))

    if 'name' in body:
        product.name = body['name'].strip()
    if 'price' in body:
        product.price = body['price']
    if 'status' in body:
        product.status = body['status']

    product.save()
    return success({'product_id': str(product.id)})


@require_http_methods(['DELETE'])
@require_permission(Resource.PRODUCT, Action.DELETE)
def product_delete(request, product_id):
    try:
        product = Product.objects.select_related('shop').get(id=product_id)
    except Product.DoesNotExist:
        return error('Product not found', status=404)

    if request.scope == Scope.OWN_SHOP and product.shop.owner != request.user:
        return error('Permission denied', status=403)

    product.delete()
    return success({'message': 'Product deleted'})


@require_http_methods(['GET'])
@require_permission(Resource.ORDER, Action.READ)
def order_list(request):
    scope = request.scope

    if scope == Scope.ALL:
        orders = Order.objects.select_related('user', 'product__shop').all()
    elif scope == Scope.OWN_SHOP:
        orders = Order.objects.select_related('user', 'product__shop').filter(
            product__shop__owner=request.user
        )
    else:
        orders = Order.objects.select_related('user', 'product__shop').filter(
            user=request.user
        )

    data = [
        {
            'id': str(o.id),
            'user_id': str(o.user_id),
            'product_id': str(o.product_id),
            'status': o.status,
            'quantity': o.quantity,
            'created_at': o.created_at.isoformat(),
        }
        for o in orders
    ]
    return success({'orders': data})


@require_http_methods(['POST'])
@require_permission(Resource.ORDER, Action.CREATE)
def order_create(request):
    try:
        body = parse_body(request)
    except ValueError as e:
        return error(str(e))

    product_id = body.get('product_id', '').strip()
    quantity = body.get('quantity', 1)

    if not product_id:
        return error('product_id is required')

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return error('Product not found', status=404)

    order = Order.objects.create(
        user=request.user,
        product=product,
        quantity=quantity,
    )

    return success({'order_id': str(order.id)}, status=201)


@require_http_methods(['GET'])
@require_permission(Resource.ORDER, Action.READ)
def order_detail(request, order_id):
    try:
        order = Order.objects.select_related('user', 'product__shop').get(id=order_id)
    except Order.DoesNotExist:
        return error('Order not found', status=404)

    scope = request.scope

    if scope == Scope.OWN and order.user != request.user:
        return error('Permission denied', status=403)
    if scope == Scope.OWN_SHOP and order.product.shop.owner != request.user:
        return error('Permission denied', status=403)

    return success({
        'id': str(order.id),
        'user_id': str(order.user_id),
        'product_id': str(order.product_id),
        'status': order.status,
        'quantity': order.quantity,
        'created_at': order.created_at.isoformat(),
    })


@require_http_methods(['PATCH'])
@require_permission(Resource.ORDER, Action.UPDATE)
def order_update_status(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return error('Order not found', status=404)

    try:
        body = parse_body(request)
    except ValueError as e:
        return error(str(e))

    new_status = body.get('status', '').strip()

    if not new_status:
        return error('status is required')

    if new_status not in OrderStatus.values:
        return error(f'Invalid status. Choices: {OrderStatus.values}')

    order.status = new_status
    order.save()

    return success({'order_id': str(order.id), 'status': order.status})


@require_http_methods(['GET'])
@require_permission(Resource.REVIEW, Action.READ)
def review_list(request):
    scope = request.scope
    product_id = request.GET.get('product_id')

    if scope == Scope.OWN:
        reviews = (Review.objects
                   .select_related('user', 'product')
                   .filter(user=request.user))
    else:
        reviews = Review.objects.select_related('user', 'product').all()

    if product_id:
        reviews = reviews.filter(product_id=product_id)

    data = [
        {
            'id': str(r.id),
            'author_id': str(r.user_id),
            'product_id': str(r.product_id),
            'rating': r.rating,
            'text': r.text,
            'created_at': r.created_at.isoformat(),
        }
        for r in reviews
    ]
    return success({'reviews': data})


@require_http_methods(['POST'])
@require_permission(Resource.REVIEW, Action.CREATE)
def review_create(request):
    try:
        body = parse_body(request)
    except ValueError as e:
        return error(str(e))

    product_id = body.get('product_id', '').strip()
    rating = body.get('rating')
    text = body.get('text', '').strip()

    if not product_id or rating is None:
        return error('product_id and rating are required')

    if not (1 <= int(rating) <= 5):
        return error('Rating must be between 1 and 5')

    try:
        product = Product.objects.get(id=product_id,
                                      status=ProductStatus.PUBLISHED)
    except Product.DoesNotExist:
        return error('Product not found', status=404)

    if Review.objects.filter(user=request.user, product=product).exists():
        return error('You already reviewed this product', status=409)

    review = Review.objects.create(
        user=request.user,
        product=product,
        rating=rating,
        text=text,
    )
    return success({'review_id': str(review.id)}, status=201)


@require_http_methods(['GET'])
@require_permission(Resource.REVIEW, Action.READ)
def review_detail(request, review_id):
    try:
        review = (Review.objects
                  .select_related('user', 'product')
                  .get(id=review_id))
    except Review.DoesNotExist:
        return error('Review not found', status=404)

    return success({
        'id': str(review.id),
        'author_id': str(review.user_id),
        'product_id': str(review.product_id),
        'rating': review.rating,
        'text': review.text,
        'created_at': review.created_at.isoformat(),
    })


@require_http_methods(['DELETE'])
@require_permission(Resource.REVIEW, Action.DELETE)
def review_delete(request, review_id):
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return error('Review not found', status=404)

    if request.scope == Scope.OWN and review.user != request.user:
        return error('Permission denied', status=403)

    review.delete()
    return success({'message': 'Review deleted'})

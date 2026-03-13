import os
import json
import uuid
from products.models import *
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.template.loader import get_template
from accounts.models import Profile, Cart, CartItem, Order, OrderItem
from base.emails import send_account_activation_email
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import redirect, render, get_object_or_404
from accounts.forms import UserUpdateForm, UserProfileForm, CustomPasswordChangeForm


# Create your views here.


def login_page(request):
    # Get the next URL from the query parameter
    next_url = request.GET.get('next')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_obj = User.objects.filter(username=username)

        if not user_obj.exists():
            messages.warning(request, '账号不存在！')
            return HttpResponseRedirect(request.path_info)

        # 跳过邮箱验证检查（开发环境）

        user_obj = authenticate(username=username, password=password)
        if user_obj:
            login(request, user_obj)
            messages.success(request, '登录成功！')

            # Check if the next URL is safe
            if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=request.get_host()):
                return redirect(next_url)
            else:
                return redirect('index')

        messages.warning(request, '用户名或密码错误。')
        return HttpResponseRedirect(request.path_info)

    return render(request, 'accounts/login.html')


def register_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user_obj = User.objects.filter(username=username, email=email)

        if user_obj.exists():
            messages.info(request, '用户名或邮箱已存在！')
            return HttpResponseRedirect(request.path_info)

        user_obj = User.objects.create(
            username=username, first_name=first_name, last_name=last_name, email=email)
        user_obj.set_password(password)
        user_obj.save()

        profile = Profile.objects.get(user=user_obj)
        profile.is_email_verified = True
        profile.save()

        messages.success(request, "注册成功！请登录。")

        return HttpResponseRedirect(request.path_info)

    return render(request, 'accounts/register.html')


@login_required
def user_logout(request):
    logout(request)
    messages.warning(request, "Logged Out Successfully!")
    return redirect('index')


def activate_email_account(request, email_token):
    try:
        user = Profile.objects.get(email_token=email_token)
        user.is_email_verified = True
        user.save()
        messages.success(request, '账户验证成功！')
        return redirect('login')
    except Exception as e:
        return HttpResponse('无效的邮箱验证令牌。')


@login_required
def add_to_cart(request, uid):
    try:
        product = get_object_or_404(Product, uid=uid)
        cart, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        messages.success(request, '已加入购物车！')

    except Exception as e:
        messages.error(request, f'加入购物车失败：{str(e)}')

    return redirect(reverse('cart'))


@login_required
def cart(request):
    cart_obj = None
    user = request.user

    try:
        cart_obj = Cart.objects.get(is_paid=False, user=user)

    except Exception as e:
        messages.warning(request, "购物车为空，请先添加课程。")
        return redirect(reverse('index'))

    if request.method == 'POST':
        coupon = request.POST.get('coupon')
        coupon_obj = Coupon.objects.filter(coupon_code__exact=coupon).first()

        if not coupon_obj:
            messages.warning(request, '优惠券无效。')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if cart_obj and cart_obj.coupon:
            messages.warning(request, '优惠券已使用。')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if coupon_obj and coupon_obj.is_expired:
            messages.warning(request, '优惠券已过期。')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if cart_obj and coupon_obj and cart_obj.get_cart_total() < coupon_obj.minimum_amount:
            messages.warning(
                request, f'订单金额需大于 {coupon_obj.minimum_amount} 元才能使用该优惠券')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if cart_obj and coupon_obj:
            cart_obj.coupon = coupon_obj
            cart_obj.save()
            messages.success(request, '优惠券已成功应用。')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    context = {
        'cart': cart_obj,
        'quantity_range': range(1, 6),
    }
    return render(request, 'accounts/cart.html', context)


@require_POST
@login_required
def update_cart_item(request):
    try:
        data = json.loads(request.body)
        cart_item_id = data.get("cart_item_id")
        quantity = int(data.get("quantity"))

        cart_item = CartItem.objects.get(uid=cart_item_id, cart__user=request.user, cart__is_paid=False)
        cart_item.quantity = quantity
        cart_item.save()

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def remove_cart(request, uid):
    try:
        cart_item = get_object_or_404(CartItem, uid=uid)
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')

    except Exception as e:
        print(e)
        messages.warning(request, 'Error removing item from cart.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def remove_coupon(request, cart_id):
    cart = Cart.objects.get(uid=cart_id)
    cart.coupon = None
    cart.save()

    messages.success(request, 'Coupon Removed.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# 支付成功回调（后续接入国内支付时使用）
def success(request):
    order_id = request.GET.get('order_id')
    cart = get_object_or_404(Cart, uid=order_id)

    cart.is_paid = True
    cart.save()

    order = create_order(cart)

    context = {'order': order}
    return render(request, 'payment_success/payment_success.html', context)


# HTML to PDF Conversion
def render_to_pdf(template_src, context_dict={}):
    from weasyprint import CSS, HTML  # 延迟导入，避免启动时加载 GTK3 DLL
    template = get_template(template_src)
    html = template.render(context_dict)

    static_root = settings.STATIC_ROOT
    css_files = [
        os.path.join(static_root, 'css', 'bootstrap.css'),
        os.path.join(static_root, 'css', 'responsive.css'),
        os.path.join(static_root, 'css', 'ui.css'),
    ]
    css_objects = [CSS(filename=css_file) for css_file in css_files]
    pdf_file = HTML(string=html).write_pdf(stylesheets=css_objects)

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{context_dict["order"].order_id}.pdf"'
    return response


def download_invoice(request, order_id):
    order = Order.objects.filter(order_id=order_id).first()
    order_items = order.order_items.all()

    context = {
        'order': order,
        'order_items': order_items,
    }

    pdf = render_to_pdf('accounts/order_pdf_generate.html', context)
    if pdf:
        return pdf
    return HttpResponse("Error generating PDF", status=400)


@login_required
def profile_view(request, username):
    user_name = get_object_or_404(User, username=username)
    user = request.user
    profile = user.profile

    user_form = UserUpdateForm(instance=user)
    profile_form = UserProfileForm(instance=profile)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(
            request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(
                request, '您的个人资料已成功更新!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    context = {
        'user_name': user_name,
        'user_form': user_form,
        'profile_form': profile_form
    }

    return render(request, 'accounts/profile.html', context)


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(
                request, '您的密码已成功更新!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.warning(request, '请更正以下错误。')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})



# Order history view
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'accounts/order_history.html', {'orders': orders})


def create_order(cart):
    order, created = Order.objects.get_or_create(
        user=cart.user,
        order_id=str(uuid.uuid4()),
        defaults={
            'payment_status': 'Paid',
            'payment_mode': '待接入',
            'order_total_price': cart.get_cart_total(),
            'coupon': cart.coupon,
            'grand_total': cart.get_cart_total_price_after_coupon(),
        }
    )

    cart_items = CartItem.objects.filter(cart=cart)
    for cart_item in cart_items:
        OrderItem.objects.get_or_create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            product_price=cart_item.get_product_price()
        )

    return order


# Order Details view
@login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    context = {
        'order': order,
        'order_items': order_items,
        'order_total_price': sum(item.get_total_price() for item in order_items),
        'coupon_discount': order.coupon.discount_amount if order.coupon else 0,
        'grand_total': order.get_order_total_price()
    }
    return render(request, 'accounts/order_details.html', context)


# Delete user account feature
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(
            request, "您的账户已成功删除。")
        return redirect('index')

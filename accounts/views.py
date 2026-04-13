import os
import json
import uuid
import random
import time
from products.models import *
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.template.loader import get_template
from accounts.models import Profile, Cart, CartItem, Order, OrderItem, UserCourse
from base.emails import send_account_activation_email, send_verification_code_email, send_delivery_email
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


def send_register_code(request):
    """发送注册验证码（AJAX POST）"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方式错误'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
    except Exception:
        return JsonResponse({'success': False, 'message': '参数错误'}, status=400)

    if not email:
        return JsonResponse({'success': False, 'message': '请填写邮箱'})

    # 简单格式校验（必须包含 @ 和 .）
    if '@' not in email or '.' not in email.split('@')[-1]:
        return JsonResponse({'success': False, 'message': '邮箱格式不正确，请填写完整邮箱（如 123456@qq.com）'})

    if User.objects.filter(email=email).exists():
        return JsonResponse({'success': False, 'message': '该邮箱已被注册'})

    # 60 秒冷却检测
    last_sent = request.session.get('reg_code_sent_at', 0)
    if time.time() - last_sent < 60:
        remaining = int(60 - (time.time() - last_sent))
        return JsonResponse({'success': False, 'message': f'请等待 {remaining} 秒后再发送'})

    code = str(random.randint(100000, 999999))
    request.session['reg_code'] = code
    request.session['reg_code_email'] = email
    request.session['reg_code_sent_at'] = time.time()
    # Session 5 分钟后过期（覆盖全局设置，仅作标记，校验时手动判断时间差）

    try:
        send_verification_code_email(email, code)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'邮件发送失败：{str(e)}'})

    return JsonResponse({'success': True, 'message': '验证码已发送，请查收邮件'})


def register_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        input_code = request.POST.get('verify_code', '').strip()

        # ── 验证码校验 ──
        session_code = request.session.get('reg_code')
        session_email = request.session.get('reg_code_email')
        sent_at = request.session.get('reg_code_sent_at', 0)

        if not session_code:
            messages.warning(request, '请先获取验证码')
            return HttpResponseRedirect(request.path_info)

        if email != session_email:
            messages.warning(request, '邮箱与发送验证码的邮箱不一致')
            return HttpResponseRedirect(request.path_info)

        if time.time() - sent_at > 300:  # 5 分钟
            messages.warning(request, '验证码已过期，请重新获取')
            return HttpResponseRedirect(request.path_info)

        if input_code != session_code:
            messages.warning(request, '验证码错误，请重新输入')
            return HttpResponseRedirect(request.path_info)

        # ── 常规注册逻辑 ──
        if User.objects.filter(username=username).exists():
            messages.info(request, '用户名已存在！')
            return HttpResponseRedirect(request.path_info)

        if User.objects.filter(email=email).exists():
            messages.info(request, '该邮箱已被注册！')
            return HttpResponseRedirect(request.path_info)

        user_obj = User.objects.create(
            username=username, email=email)
        user_obj.set_password(password)
        user_obj.save()

        profile = Profile.objects.get(user=user_obj)
        profile.is_email_verified = True
        profile.save()

        # 清除验证码 Session
        for key in ('reg_code', 'reg_code_email', 'reg_code_sent_at'):
            request.session.pop(key, None)

        messages.success(request, '注册成功！请登录。')
        return HttpResponseRedirect(request.path_info)

    return render(request, 'accounts/register.html')


@login_required
def user_logout(request):
    logout(request)
    messages.warning(request, "已退出登录！")
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
        messages.success(request, '商品已从购物车中移除。')

    except Exception as e:
        print(e)
        messages.warning(request, '移除商品失败。')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def remove_coupon(request, cart_id):
    cart = Cart.objects.get(uid=cart_id)
    cart.coupon = None
    cart.save()

    messages.success(request, '优惠券已移除。')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# 支付成功页（由 checkout 视图跳转过来）
def success(request):
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
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
        # 头像单独上传
        if request.POST.get('avatar_upload'):
            avatar_file = request.FILES.get('profile_image')
            if avatar_file:
                profile.profile_image = avatar_file
                profile.save()
                messages.success(request, '头像已更新！')
            else:
                messages.warning(request, '请选择一张图片。')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # 账号信息更新
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, '您的个人资料已成功更新!')
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


@require_POST
@login_required
def checkout(request):
    """模拟支付：接收支付方式，标记订单已付款并触发发货"""
    payment_method = request.POST.get('payment_method', '')
    cart_uid = request.POST.get('cart_uid', '')

    # 校验支付方式
    if payment_method not in ('alipay', 'wechat'):
        return JsonResponse({'success': False, 'message': '无效的支付方式'}, status=400)

    # 获取购物车
    try:
        cart_obj = Cart.objects.get(uid=cart_uid, user=request.user, is_paid=False)
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': '购物车不存在或已支付'}, status=404)

    # 标记已付款
    cart_obj.is_paid = True
    cart_obj.save()

    # 创建订单
    payment_mode_map = {'alipay': '支付宝', 'wechat': '微信支付'}
    order = create_order(cart_obj)
    order.payment_mode = payment_mode_map[payment_method]
    order.save()

    # 自动发货
    import django.utils.timezone as tz
    order_items = order.order_items.select_related('product').all()
    try:
        send_delivery_email(order.user.email, order_items)
    except Exception as e:
        print(f'[发货邮件] 发送失败：{e}')

    for item in order_items:
        if item.product:
            uc, _ = UserCourse.objects.get_or_create(
                user=order.user, product=item.product
            )
            uc.is_delivered = True
            uc.netdisk_link = item.product.full_content_link
            uc.netdisk_password = item.product.netdisk_password
            uc.delivered_at = tz.now()
            uc.save()

    success_url = reverse('success') + f'?order_id={order.order_id}'
    return JsonResponse({'success': True, 'redirect_url': success_url})

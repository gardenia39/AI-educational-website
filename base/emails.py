from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_account_activation_email(email, email_token):
    subject = "Your account needs to be verified"
    email_from = settings.DEFAULT_FROM_EMAIL

    # Use BASE_URL from settings (configured via environment variable)
    activation_link = f'{settings.BASE_URL}/accounts/activate/{email_token}'

    html_message = render_to_string(
        'emails/account_activation.html', {'activation_link': activation_link})
    plain_message = f'Hi, please verify your account by clicking the link: {activation_link}'

    send_mail(
        subject,
        plain_message,
        email_from,
        [email],
        html_message=html_message
    )


def send_verification_code_email(email, code):
    subject = "【课程平台】注册验证码"
    email_from = settings.DEFAULT_FROM_EMAIL
    plain_message = f'您的注册验证码是：{code}\n验证码有效期为5分钟，请勿泄露给他人。'

    send_mail(
        subject,
        plain_message,
        email_from,
        [email],
    )


def send_delivery_email(email, order_items):
    """
    支付成功后自动发货，将课程资源链接发送到用户邮箱。
    order_items: OrderItem queryset
    """
    subject = "【课程平台】您的课程资源已发货"
    email_from = settings.DEFAULT_FROM_EMAIL

    lines = ["感谢您的购买！以下是您购买的课程资源：\n"]
    for item in order_items:
        product = item.product
        lines.append(f"📚 课程名称：{product.product_name}")
        if product.full_content_link:
            lines.append(f"   资源链接：{product.full_content_link}")
        if product.netdisk_password:
            lines.append(f"   提取码：{product.netdisk_password}")
        lines.append("")  # 空行分隔

    lines.append("如有问题请联系客服，祝您学习愉快！")
    plain_message = "\n".join(lines)

    send_mail(
        subject,
        plain_message,
        email_from,
        [email],
    )


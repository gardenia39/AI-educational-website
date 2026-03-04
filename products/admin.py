from django.contrib import admin
from django.utils.html import format_html
from .models import *


# ── Category Admin ──────────────────────────────────────────
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'image_preview']

    def image_preview(self, obj):
        if obj.category_image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.category_image.url)
        return "无图片"
    image_preview.short_description = '预览'


# ── ProductImage inline ───────────────────────────────────────
class ProductImageInline(admin.StackedInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" style="object-fit: contain;" />', obj.image.url)
        return "无图片"
    image_preview.short_description = '预览'


# ── Product Admin ─────────────────────────────────────────────
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'price', 'is_free']
    inlines = [ProductImageInline]
    # slug 自动生成，隐藏避免混淆
    exclude = ['slug']


# ── ProductImage standalone Admin ────────────────────────────
class ProductImageStandaloneAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_thumbnail']
    readonly_fields = ['img_preview']

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "无图片"
    image_thumbnail.short_description = '缩略图'


admin.site.register(Category, CategoryAdmin)
admin.site.register(Coupon)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage, ProductImageStandaloneAdmin)
admin.site.register(ProductReview)

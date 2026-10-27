from django.contrib import admin
from . import models
class ImageInline(admin.TabularInline):
    model = models.ProductImage; extra = 1
@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ImageInline]; list_display = ("name", "category", "price", "stock", "is_active")
for m in (models.Shop, models.Category, models.Order, models.OrderItem, models.Payment, models.Address): admin.site.register(m)

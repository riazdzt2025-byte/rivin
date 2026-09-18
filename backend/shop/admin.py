from django.contrib import admin
from .models import Category, Product, Customer, Order, OrderItem, OrderStatusHistory, StockMovement, AuditLog, Review, DeliveryZone, Coupon, SiteSetting

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('code','name_bn','name_en','name_ar','is_active','sort_order')
    list_filter = ('is_active',)
    search_fields = ('code','name_bn','name_en','name_ar')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku','name_bn','category','price','stock','is_active','is_bestseller')
    list_filter = ('is_active','is_bestseller','category')
    search_fields = ('sku','name_bn','name_en','name_ar')
    list_editable = ('price','stock','is_bestseller')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('line_total',)

class HistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_no','customer','status','total','payment_method','ordered_at')
    list_filter = ('status','payment_method','payment_status')
    search_fields = ('order_no','customer__name','customer__mobile')
    inlines = [OrderItemInline, HistoryInline]
    readonly_fields = ('order_no','total')

admin.site.register(Customer)
admin.site.register(StockMovement)
admin.site.register(AuditLog)
admin.site.register(Review)
admin.site.register(DeliveryZone)
admin.site.register(Coupon)
admin.site.register(SiteSetting)

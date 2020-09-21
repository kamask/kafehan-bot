from django.contrib import admin
from .models import *


class ClientsAdmin(admin.ModelAdmin):
    list_display = ('idu', 'username', 'first_name', 'last_name', 'number', 'created_at', 'updated_at')
    search_fields = ('username', 'first_name', 'last_name', 'number', 'idu')


class CategoriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'order',)
    search_fields = ('name',)
    list_editable = ('order',)


class ProductsAdmin(admin.ModelAdmin):
    list_display = ('title', 'id', 'category', 'weight', 'cost', 'visible',)
    search_fields = ('title', 'description')
    list_editable = ('cost', 'visible',)
    list_filter = ('category', 'weight',)


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'client', 'number', 'status', 'type', 'pay', 'cost', 'comment', 'address', 'table', 'dateOrder', 'dateAccess', 'dateDone', 'dateCanceled', 'update_at',)
    search_fields = ('pk', 'client__idu', 'number', 'comment', 'address',)
    list_filter = ('status', 'type', 'created_at', 'dateOrder', 'dateAccess', 'pay', 'dateDone',)


class OrderListAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'count', 'created_at',)
    search_fields = ('order__pk', 'product__title',)
    list_filter = ('created_at',)
    list_editable = ('count',)


class OrderTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slag',)


class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'slag',)


class OrderPayTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slag',)


class TableAdmin(admin.ModelAdmin):
    list_display = ('num', 'photo')


class AdminKafeHanAdmin(admin.ModelAdmin):
    list_display = ('uid',)
    search_fields = ('uid',)


class OnlinePayAdmin(admin.ModelAdmin):
    list_display = ('order', 'cost', 'status', 'id_pay',)
    search_fields = ('id_pay', 'status', 'order__pk', 'cost',)
    list_filter = ('status',)


admin.site.register(Client, ClientsAdmin)
admin.site.register(Category, CategoriesAdmin)
admin.site.register(Product, ProductsAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderList, OrderListAdmin)
admin.site.register(OrderType, OrderTypeAdmin)
admin.site.register(OrderStatus, OrderStatusAdmin)
admin.site.register(OrderPayType, OrderPayTypeAdmin)
admin.site.register(Table, TableAdmin)
admin.site.register(AdminKafeHan, AdminKafeHanAdmin)
admin.site.register(OnlinePay, OnlinePayAdmin)

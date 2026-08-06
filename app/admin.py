from django.contrib import admin
from reversion.admin import VersionAdmin
import reversion
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group as BaseGroup
from .models import User, Group, Account, Type, Method, Category, BusinessRule, Installment, Transaction


# User Admin
@admin.register(User)
class UserAdmin(VersionAdmin, BaseUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'last_login', 'is_staff', 'is_superuser', 'is_active',)
    search_fields = ('username', 'email', 'first_name', 'last_name', 'observations',)
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups',)
    filter_horizontal = ('groups', 'user_permissions',)
    model = User
    ordering = ('username',)
    fieldsets = (
        (None, {
            'fields': ('username', 'password',)
        }),
        ('Informações pessoais', {
            'fields': ('first_name', 'last_name', 'email',)
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',)
        }),
        ('Datas importantes', {
            'fields': ('last_login', 'date_joined',)
        }),
        ('Observações', {
            'fields': ('observations',)
        }),
    )
    add_fieldsets = (
        (None, {
            'fields': ('username', 'password1', 'password2',),
        }),
    )


# Group Admin
reversion.register(BaseGroup)
reversion.register(Group)
admin.site.unregister(BaseGroup)
@admin.register(Group)
class GroupAdmin(VersionAdmin, BaseGroupAdmin):
    ...


@admin.register(Account)
class AccountAdmin(VersionAdmin):
    list_display = ('description',)
    search_fields = ('description',)


@admin.register(Type)
class TypeAdmin(VersionAdmin):
    list_display = ('description',)
    search_fields = ('description',)


@admin.register(Method)
class MethodAdmin(VersionAdmin):
    list_display = ('description',)
    search_fields = ('description',)


@admin.register(Category)
class CategoryAdmin(VersionAdmin):
    list_display = ('description',)
    search_fields = ('description',)


@admin.register(BusinessRule)
class BusinessRuleAdmin(VersionAdmin):
    list_display = ('account', 'type', 'method',)
    list_filter = ('account', 'type', 'method',)
    search_fields = ('account__description', 'type__description', 'method__description',)
    autocomplete_fields = ('account', 'type', 'method',)


@admin.register(Installment)
class InstallmentAdmin(VersionAdmin):
    list_display = ('user', 'account', 'type', 'method', 'category', 'description', 'value', 'installments', 'datetime',)
    list_filter = ('user', 'account', 'type', 'method', 'category',)
    search_fields = ('description',)
    autocomplete_fields = ('user', 'account', 'type', 'method', 'category',)


@admin.register(Transaction)
class TransactionAdmin(VersionAdmin):
    list_display = ('user', 'account', 'type', 'method', 'category', 'description', 'value', 'datetime',)
    list_filter = ('user', 'account', 'type', 'method', 'category',)
    search_fields = ('description',)
    autocomplete_fields = ('user', 'account', 'type', 'method', 'category',)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.installment_id:
            return ('user', 'account', 'type', 'method', 'category', 'description', 'value', 'installment', 'parcel', 'datetime',)
        return ('installment', 'parcel',)

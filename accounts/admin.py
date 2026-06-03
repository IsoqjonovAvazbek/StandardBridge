from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.contrib import messages
from .models import CustomUser, ExpertProfile, EntrepreneurProfile


class ExpertProfileInline(admin.StackedInline):
    model = ExpertProfile
    can_delete = False
    extra = 0


class EntrepreneurProfileInline(admin.StackedInline):
    model = EntrepreneurProfile
    can_delete = False
    extra = 0


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'get_full_name', 'role', 'company_name', 'region', 'is_active']
    list_filter = ['role', 'region', 'is_active']
    search_fields = ['username', 'email', 'company_name', 'first_name', 'last_name']

    fieldsets = UserAdmin.fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('role', 'company_name', 'phone', 'region', 'industry')
        }),
    )


def verify_experts(modeladmin, request, queryset):
    from experts.emails import send_expert_verified
    updated = 0
    for profile in queryset.filter(is_verified=False):
        profile.is_verified = True
        profile.verified_at = timezone.now()
        profile.save()
        send_expert_verified(profile.user)
        updated += 1
    messages.success(request, f'{updated} ta mutaxassis tasdiqlandi va ularga email yuborildi.')

verify_experts.short_description = "Tanlangan mutaxassislarni tasdiqlash"


def unverify_experts(modeladmin, request, queryset):
    queryset.update(is_verified=False, verified_at=None)
    messages.warning(request, 'Tanlangan mutaxassislar tasdiqdan o\'chirildi.')

unverify_experts.short_description = "Tasdiqni bekor qilish"


@admin.register(ExpertProfile)
class ExpertProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'experience_years', 'rating', 'total_projects', 'is_available', 'is_verified', 'verified_at']
    list_filter = ['is_available', 'is_verified', 'region']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'specializations']
    actions = [verify_experts, unverify_experts]
    readonly_fields = ['verified_at']

    fieldsets = (
        ('Foydalanuvchi', {'fields': ('user',)}),
        ('Profil', {'fields': ('bio', 'specializations', 'standard_tags', 'experience_years', 'region', 'phone', 'certificates')}),
        ('Sertifikat', {'fields': ('cert_number', 'issuing_body', 'cert_expiry')}),
        ('Narx va muddat', {'fields': ('project_price', 'completion_days', 'hourly_rate')}),
        ('Statistika', {'fields': ('rating', 'total_projects')}),
        ('Holat', {'fields': ('is_available', 'is_verified', 'verified_at')}),
    )


@admin.register(EntrepreneurProfile)
class EntrepreneurProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_count', 'export_experience', 'target_markets']
    search_fields = ['user__username', 'user__company_name']
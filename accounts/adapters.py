from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class AccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return '/dashboard/'


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """Google orqali kirgan foydalanuvchini tizimga ulash yoki yangi yaratish."""
        # Agar email bo'yicha mavjud foydalanuvchi topilsa — uning hisobiyla kir
        if sociallogin.is_existing:
            return
        email = sociallogin.account.extra_data.get('email', '')
        if not email:
            return
        from accounts.models import CustomUser
        try:
            existing = CustomUser.objects.get(email__iexact=email)
            sociallogin.connect(request, existing)
        except CustomUser.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """Yangi Google foydalanuvchisi: role=entrepreneur, email tasdiqlangan."""
        user = super().save_user(request, sociallogin, form)
        update_fields = []
        if not user.role:
            user.role = 'entrepreneur'
            update_fields.append('role')
        if not user.is_email_verified:
            user.is_email_verified = True
            update_fields.append('is_email_verified')
        if update_fields:
            user.save(update_fields=update_fields)
        return user

    def get_connect_redirect_url(self, request, socialaccount):
        return '/dashboard/'

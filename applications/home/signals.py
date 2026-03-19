from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount

@receiver(user_signed_up)
def set_staff_status_on_signup(request, user, **kwargs):
    """
    Cuando un usuario se registra a través de una cuenta social (Google),
    le asignamos automáticamente permisos de staff para facilitar las pruebas.
    """
    # Verificamos si el registro viene de una cuenta social
    social_account = SocialAccount.objects.filter(user=user).first()
    
    if social_account:
        # En un sistema real, aquí podrías filtrar por dominio o lista blanca
        user.is_staff = True
        user.is_superuser = True  # Opcional, solo para pruebas
        user.save()

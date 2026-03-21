from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their
    email address instead of their username.
    """

    def authenticate(self, request, email=None, password=None, **kwargs):
        # Support being called with username= kwarg (e.g. from older code paths)
        if email is None:
            email = kwargs.get('username')
        if email is None or password is None:
            return None

        try:
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            # Run the default password hasher to reduce timing attacks
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            # Edge case: take the most recently created one
            user = UserModel.objects.filter(email__iexact=email).order_by('-date_joined').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

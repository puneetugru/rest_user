import base64
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from manticore_django.manticore_django.utils import get_class
from rest_core.rest_core.serializers import BaseModelSerializer

__author__ = 'baylee'


User = get_user_model()


class AuthSerializerMixin(object):
    def restore_object(self, attrs, instance=None):
        if attrs.get("username", None):
            attrs["username"] = attrs["username"].lower()
        if attrs.get("email", None):
            attrs["email"] = attrs["email"].lower()
        if attrs.get("password", None):
            attrs["password"] = make_password(base64.decodestring(attrs["password"]))

        return super(AuthSerializerMixin, self).restore_object(attrs, instance)

    def validate_password(self, attrs, source):
        if len(attrs[source]) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters")
        return attrs


class LoginSerializer(AuthSerializerMixin, serializers.ModelSerializer):
    client_id = serializers.SerializerMethodField('get_client_id')
    client_secret = serializers.SerializerMethodField('get_client_secret')

    class Meta:
        model = User
        fields = ('client_id', 'client_secret')

    def get_client_id(self, obj):
        return obj.application_set.first().client_id

    def get_client_secret(self, obj):
        return obj.application_set.first().client_secret


class SignUpSerializer(LoginSerializer):
    class Meta(LoginSerializer.Meta):
        fields = ('username', 'email', 'password', 'client_id', 'client_secret')
        write_only_fields = ('password',)


class UserSerializer(AuthSerializerMixin, BaseModelSerializer):
    class Meta:
        model = User
        # exclude = ('last_login', 'is_active', 'is_admin', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

    def __init__(self, *args, **kwargs):
        """
        Due to issues with recursive importing, it's difficult to have our project-specific user serializer inherit
        from this model. Instead, each project can define its own UserSerializer. Then we import those fields here
        so that our other rest libraries will serialize the user model correctly.

        TODO: allow graceful failure / default if a project-specific serializer isn't defined.
        """
        super(UserSerializer, self).__init__(*args, **kwargs)
        custom_user_serializer = get_class(settings.USER_SERIALIZER)
        self.fields = custom_user_serializer().fields


class PasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate_password(self, attrs, source):
        if len(attrs[source]) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters")
        return attrs

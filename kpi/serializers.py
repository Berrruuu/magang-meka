from rest_framework import serializers
from .models import Company, KpiTarget, User
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from .models import User, Company
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed



class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class KpiTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = KpiTarget
        fields = '__all__'



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'email',
            'password',
            'role',
            'company',
            'status'
        ]

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return User.objects.create(**validated_data)
    



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['name'] = user.name
        token['email'] = user.email
        token['role'] = user.role
        token['company'] = user.company

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.status:
            raise AuthenticationFailed("Akun tidak aktif")

        companies = Company.objects.filter(id__in=self.user.company)

        data['user'] = {
            "id": self.user.id,
            "name": self.user.name,
            "email": self.user.email,
            "role": self.user.role,
            "status": self.user.status,
            "companies": [
                {
                    "id": c.id,
                    "name": c.name
                } for c in companies
            ]
        }

        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "role",
            "company",
            "status"
        ]
from rest_framework import serializers
from .models import Company, KpiTarget, User
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from .models import User, Company, CompanyUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from .utils.response import success_response, error_response
from django.db import transaction


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name']


class KpiTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = KpiTarget
        fields = '__all__'



class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField()
    status = serializers.BooleanField()
    company_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )

    def create(self, validated_data):
        company_ids = validated_data.pop('company_ids')

        user = User.objects.create_user(**validated_data)

        for cid in company_ids:
            CompanyUser.objects.create(
                user_id=user.id,
                company_id=cid
            )

        companies = Company.objects.using('default').filter(
            id__in=company_ids
        ).values('id', 'name')

        user.company = list(companies)
        user.save()

        return user
    
    



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['name'] = user.name
        token['email'] = user.email
        token['role'] = user.role

        company_ids = list(
            CompanyUser.objects
            .using('carfix_user')
            .filter(user_id=user.id)
            .values_list('company_id', flat=True)
        )

        token['company'] = company_ids

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.status:
            raise AuthenticationFailed("Akun tidak aktif")


        company_ids = list(
            CompanyUser.objects
            .using('carfix_user')
            .filter(user_id=self.user.id)
            .values_list('company_id', flat=True)
        )

        companies = Company.objects.using('default').filter(
            id__in=company_ids
        )


        data['access_company_ids'] = company_ids

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
    companies = serializers.SerializerMethodField()
    company_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role', 'status', 'companies', 'company_ids']

    def get_companies(self, obj):
        return obj.company or []

    @transaction.atomic
    def update(self, instance, validated_data):
        company_ids = validated_data.pop('company_ids', None)

        # 1️⃣ Update field biasa
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save(using='carfix_user')

        # 2️⃣ Kalau ada update company
        if company_ids is not None:

            # Validasi company ada di DB default
            valid_companies = list(
                Company.objects.using('default')
                .filter(id__in=company_ids)
                .values('id', 'name')
            )

            if len(valid_companies) != len(company_ids):
                raise serializers.ValidationError(
                    "Salah satu company tidak ditemukan."
                )

            # 3️⃣ Update pivot table (source of truth)
            CompanyUser.objects.using('carfix_user').filter(
                user_id=instance.id
            ).delete()

            CompanyUser.objects.using('carfix_user').bulk_create([
                CompanyUser(user_id=instance.id, company_id=cid)
                for cid in company_ids
            ])

            # 4️⃣ Sync JSON snapshot
            instance.company = valid_companies
            instance.save(using='carfix_user')

        return instance

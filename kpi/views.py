from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework import status
from django.db import connections
from .serializers import RegisterSerializer
from django.contrib.auth.hashers import check_password
from .models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer,UserSerializer
from rest_framework.generics import ListAPIView
from .utils.response import success_response
from rest_framework.pagination import PageNumberPagination
from math import ceil



from .models import Company, KpiTarget
from .serializers import CompanySerializer, KpiTargetSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer

    def get_queryset(self):
        role = self.request.auth.get('role')
        company_ids = self.request.auth.get('company')

        if role == 'admin':
            return Company.objects.all()

        return Company.objects.filter(id__in=company_ids)

class KpiTargetViewSet(viewsets.ModelViewSet):
    serializer_class = KpiTargetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return KpiTarget.objects.all()

        return KpiTarget.objects.filter(company_id=1)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User berhasil dibuat",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "company": user.company,
                    "status": user.status
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserListView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "admin":
            return User.objects.all()

        return User.objects.filter(id=user.id)
    

class UserPagination(PageNumberPagination):
    page_size_query_param = 'limit'

class UserListView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ADMIN boleh lihat semua user
        if user.role == 'admin':
            return User.objects.all()

        # USER biasa hanya lihat dirinya sendiri
        return User.objects.filter(id=user.id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # ===== FILTER =====
        email = request.GET.get('email')
        if email:
            queryset = queryset.filter(email=email)

        # ===== SORT =====
        sort = request.GET.get('sort')
        if sort == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort == 'name_desc':
            queryset = queryset.order_by('-name')

        # ===== PAGINATION =====
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))

        total_items = queryset.count()
        total_pages = ceil(total_items / limit)

        start = (page - 1) * limit
        end = start + limit
        paginated_qs = queryset[start:end]

        serializer = self.get_serializer(paginated_qs, many=True)

        return Response({
            "status": "success",
            "code": 200,
            "message": "Data users berhasil diambil",
            "data": serializer.data,
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next_page": page < total_pages,
                "has_prev_page": page > 1
            }
        })


class UserCompaniesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = User.objects.get(id=user_id)

        # contoh: user.company adalah array of ID
        companies = Company.objects.filter(id__in=user.company)

        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)
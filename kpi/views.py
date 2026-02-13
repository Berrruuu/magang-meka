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
from .utils.response import success_response, error_response
from rest_framework.pagination import PageNumberPagination
from math import ceil
from rest_framework.viewsets import ModelViewSet
from .utils.pagination import DefaultPagination
from .models import Company, KpiTarget, CompanyUser
from .serializers import CompanySerializer, KpiTargetSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.generics import RetrieveAPIView
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from datetime import datetime
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework.generics import UpdateAPIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.generics import RetrieveUpdateAPIView
from calendar import monthrange
from decimal import Decimal



class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user

        company_ids = list(
            CompanyUser.objects
            .using('carfix_user')
            .filter(user_id=user.id)
            .values_list('company_id', flat=True)
        )

        if not company_ids:
            return Company.objects.none()

        return Company.objects.using('default').filter(id__in=company_ids)
    
    @action(detail=False, methods=["get"], url_path="active")
    def active_companies(self, request):

        if request.user.role != "admin":
            return error_response(
                message="Tidak memiliki akses",
                status_code=403
            )

        queryset = Company.objects.using('default').filter(x_active=True)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="Berhasil mengambil data company aktif",
            data=serializer.data
        )


    
class KpiTargetViewSet(viewsets.ModelViewSet):
    serializer_class = KpiTargetSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user

        # company yang boleh diakses user
        allowed_company_ids = list(
            CompanyUser.objects
            .using('carfix_user')
            .filter(user_id=user.id)
            .values_list('company_id', flat=True)
        )

        if not allowed_company_ids:
            return KpiTarget.objects.none()

        queryset = KpiTarget.objects.using('default') \
            .filter(company_id__in=allowed_company_ids)

        # OPTIONAL FILTER
        company_id = self.request.query_params.get('company_id')
        tahun = self.request.query_params.get('tahun')

        if company_id:
            queryset = queryset.filter(company_id=int(company_id))

        if tahun:
            queryset = queryset.filter(tahun=tahun)

        return queryset


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('User created'),
            400: openapi.Response('Bad request')
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            company_ids = request.data.get('company_ids', [])

            for cid in company_ids:
                CompanyUser.objects.using('carfix_user').create(
                    user_id=user.id,
                    company_id=cid
                )

        return success_response(
            message="User berhasil dibuat",
            data={
                "id": user.id,
                "email": user.email,
                "role": user.role
            },
            status_code=status.HTTP_201_CREATED
        )

        return error_response(
            message="Registrasi gagal",
            errors=serializer.errors,
            status_code=400
        )


    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)

            return success_response(
                message="Login berhasil",
                data=response.data,
                status_code=200
            )

        except AuthenticationFailed as e:
            return error_response(
                message=str(e),
                status_code=401
            )


class UserPagination(PageNumberPagination):
    page_size_query_param = 'limit'

class UserListView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Nomor halaman",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Jumlah data per halaman",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'email',
                openapi.IN_QUERY,
                description="Filter berdasarkan email",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'sort',
                openapi.IN_QUERY,
                description="Urutan data (name_asc / name_desc)",
                type=openapi.TYPE_STRING
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        return User.objects.filter(id=user.id)


class UserCompaniesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        company_ids = list(
            CompanyUser.objects
            .using('carfix_user')
            .filter(user_id=user.id)
            .values_list('company_id', flat=True)
        )

        # ⛔ INI KUNCI NYAWA
        if not company_ids:
            return Response([])

        companies = Company.objects \
            .using('default') \
            .filter(id__in=company_ids)

        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)

    
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return success_response(
            message="Logout berhasil",
            data={"logout": True},
            status_code=status.HTTP_200_OK
        )

class UserDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs.get("pk"))

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        return success_response(
            data=self.get_serializer(instance).data,
            message="Detail user berhasil diambil"
        )

    def update(self, request, *args, **kwargs):
        if request.user.role != "admin":
            raise PermissionDenied("Hanya admin yang dapat mengedit user.")

        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            data=serializer.data,
            message="User berhasil diperbarui"
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != "admin":
            raise PermissionDenied("Hanya admin yang dapat menghapus user.")

        instance = self.get_object()
        instance.delete()

        return success_response(
            data=None,
            message="User berhasil dihapus"
        )


class CompanyKpiView(APIView):
    permission_classes = [IsAuthenticated]

    def get_dummy_invoice_lines(self, company_id):
        
        return [
            # invoice masuk
            {"company_id": company_id, "type": "out_invoice", "price_subtotal": 500000},
            {"company_id": company_id, "type": "out_invoice", "price_subtotal": 700000},
            {"company_id": company_id, "type": "out_invoice", "price_subtotal": 300000},

            # refund
            {"company_id": company_id, "type": "out_refund", "price_subtotal": 200000},
        ]

    def calculate_all_kpi(self, company_id):

        lines = self.get_dummy_invoice_lines(company_id)

        # UE
        ue_masuk = sum(1 for l in lines if l["type"] == "out_invoice")
        ue_retur = sum(1 for l in lines if l["type"] == "out_refund")
        unit_entry = Decimal(ue_masuk - ue_retur)

        # RA
        revenue_in = sum(
            Decimal(str(l["price_subtotal"])) for l in lines
            if l["type"] == "out_invoice"
        )

        revenue_out = sum(
            Decimal(str(l["price_subtotal"])) for l in lines
            if l["type"] == "out_refund"
        )

        revenue_total = revenue_in - revenue_out

        # VPT
        if unit_entry == 0:
            vpt = Decimal("0")
        else:
            vpt = revenue_total / unit_entry

        return {
            "UNIT ENTRY": unit_entry,
            "REVENUE ALL": revenue_total,
            "VPT": vpt
        }


    def get(self, request, company_id):

        now = datetime.now()
        current_month = now.month
        current_day = now.day
        total_days = monthrange(now.year, now.month)[1]

        month_map = {
            1: "jan_01",
            2: "feb_02",
            3: "mar_03",
            4: "apr_04",
            5: "may_05",
            6: "jun_06",
            7: "jul_07",
            8: "aug_08",
            9: "sep_09",
            10: "oct_10",
            11: "nov_11",
            12: "des_12",
        }

        month_column = month_map[current_month]

        with connections['default'].cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    kt.id,
                    kt.kpi,
                    kt.{month_column} as target_month,
                    kt.setahun as target_year
                FROM kpi_target kt
                WHERE kt.company_id = %s
            """, [company_id])

            columns = [col[0] for col in cursor.description]
            results = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

        all_kpi = self.calculate_all_kpi(company_id)

        final_data = []

        for row in results:

            achievement_month = all_kpi.get(row["kpi"].upper(), 0)
            achievement_year = achievement_month  

            target_month = row["target_month"] or 0
            target_year = row["target_year"] or 0

            ratio_month = (achievement_month / target_month * Decimal("100")) if target_month else Decimal("0")
            ratio_year = (achievement_year / target_year * Decimal("100")) if target_year else Decimal("0")

            gap_month = achievement_month - target_month
            gap_year = achievement_year - target_year

            if current_day > 0:
                estimate = (achievement_month / current_day) * total_days
            else:
                estimate = achievement_month

            final_data.append({
                "kpi": row["kpi"],

                "month": {
                    "achievement": round(achievement_month, 2),
                    "target": target_month,
                    "ratio_percent": round(ratio_month, 2),
                    "gap": round(gap_month, 2),
                    "estimate": round(estimate, 2)
                },

                "year_to_month": {
                    "achievement": round(achievement_year, 2),
                    "target": target_year,
                    "ratio_percent": round(ratio_year, 2),
                    "gap": round(gap_year, 2)
                }
            })

        paginator = DefaultPagination()
        paginated = paginator.paginate_queryset(final_data, request)

        return paginator.get_paginated_response(paginated)
    

class CompanyKpiByTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get_dummy_invoice_lines(self, company_id):
        return [
            {"company_id": company_id, "type": "out_invoice", "price_subtotal": 500000},
            {"company_id": company_id, "type": "out_invoice", "price_subtotal": 700000},
            {"company_id": company_id, "type": "out_invoice", "price_subtotal": 300000},
            {"company_id": company_id, "type": "out_refund", "price_subtotal": 200000},
        ]

    def calculate_all_kpi(self, company_id):
        lines = self.get_dummy_invoice_lines(company_id)

        ue_masuk = sum(1 for l in lines if l["type"] == "out_invoice")
        ue_retur = sum(1 for l in lines if l["type"] == "out_refund")
        unit_entry = Decimal(ue_masuk - ue_retur)

        revenue_in = sum(
            Decimal(str(l["price_subtotal"]))
            for l in lines if l["type"] == "out_invoice"
        )

        revenue_out = sum(
            Decimal(str(l["price_subtotal"]))
            for l in lines if l["type"] == "out_refund"
        )

        revenue_total = revenue_in - revenue_out

        vpt = revenue_total / unit_entry if unit_entry else Decimal("0")

        return {
            "UNIT ENTRY": unit_entry,
            "REVENUE ALL": revenue_total,
            "VPT": vpt
        }

    def get(self, request, company_id, kpi):

        now = datetime.now()
        current_month = now.month
        current_day = now.day
        total_days = monthrange(now.year, now.month)[1]

        month_map = {
            1: "jan_01", 2: "feb_02", 3: "mar_03", 4: "apr_04",
            5: "may_05", 6: "jun_06", 7: "jul_07", 8: "aug_08",
            9: "sep_09", 10: "oct_10", 11: "nov_11", 12: "des_12",
        }

        month_column = month_map[current_month]

        kpi_obj = KpiTarget.objects.filter(
            company_id=company_id,
            kpi__iexact=kpi
        ).first()

        if not kpi_obj:
            return Response(
                {"error": "KPI not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        all_kpi = self.calculate_all_kpi(company_id)

        achievement_month = all_kpi.get(kpi_obj.kpi.upper(), Decimal("0"))
        achievement_year = achievement_month

        target_month = getattr(kpi_obj, month_column) or Decimal("0")
        target_year = kpi_obj.setahun or Decimal("0")

        ratio_month = (achievement_month / target_month * Decimal("100")) if target_month else Decimal("0")
        ratio_year = (achievement_year / target_year * Decimal("100")) if target_year else Decimal("0")

        gap_month = achievement_month - target_month
        gap_year = achievement_year - target_year

        estimate = (
            (achievement_month / current_day) * total_days
            if current_day else achievement_month
        )

        data = {
            "company_id": company_id,
            "kpi": kpi_obj.kpi,

            "month": {
                "achievement": round(achievement_month, 2),
                "target": target_month,
                "ratio_percent": round(ratio_month, 2),
                "gap": round(gap_month, 2),
                "estimate": round(estimate, 2)
            },

            "year_to_month": {
                "achievement": round(achievement_year, 2),
                "target": target_year,
                "ratio_percent": round(ratio_year, 2),
                "gap": round(gap_year, 2)
            }
        }

        return Response(data)

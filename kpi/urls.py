from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
router = DefaultRouter()
router.register(r'company', CompanyViewSet, basename='company')
router.register(r'kpi-targets', KpiTargetViewSet, basename='kpi-target')


urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:user_id>/companies', UserCompaniesView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path("companies/<int:company_id>/kpis/",CompanyKpiView.as_view(),name="company-kpis"),



]

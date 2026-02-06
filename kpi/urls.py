from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, KpiTargetViewSet, RegisterView, CustomTokenObtainPairView, UserListView,UserCompaniesView

router = DefaultRouter()
router.register(r'company', CompanyViewSet, basename='company')
router.register(r'kpi-targets', KpiTargetViewSet, basename='kpi-target')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:user_id>/companies', UserCompaniesView.as_view()),

]

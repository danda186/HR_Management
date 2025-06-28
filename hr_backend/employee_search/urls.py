from django.urls import path
from . import views

app_name = 'employee_search'

urlpatterns = [
    # Health check
    path('health/', views.api_health, name='health'),
    
    # Organizations
    path('organizations/', views.list_organizations, name='list_organizations'),
    path('organizations/<uuid:organization_id>/config/', 
         views.organization_config, name='organization_config'),
    
    # Employee search
    path('organizations/<uuid:organization_id>/employees/search/', 
         views.search_employees, name='search_employees'),
]


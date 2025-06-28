from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.http import Http404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Employee, Organization, OrganizationConfig
from .serializers import (
    EmployeeSearchSerializer, 
    DynamicEmployeeSerializer,
    OrganizationSerializer
)
import logging

logger = logging.getLogger(__name__)


class EmployeeSearchPagination(PageNumberPagination):
    """Custom pagination for employee search"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@extend_schema(
    operation_id='search_employees',
    summary='Search employees within an organization',
    description='Search and filter employees within a specific organization with configurable column display',
    parameters=[
        OpenApiParameter(
            name='organization_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the organization'
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search in first name, last name, and email',
            required=False
        ),
        OpenApiParameter(
            name='department',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by department',
            required=False
        ),
        OpenApiParameter(
            name='position',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by position',
            required=False
        ),
        OpenApiParameter(
            name='location',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by location',
            required=False
        ),
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by status',
            required=False,
            enum=['active', 'inactive', 'terminated', 'on_leave']
        ),
        OpenApiParameter(
            name='page',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Page number',
            required=False,
            default=1
        ),
        OpenApiParameter(
            name='page_size',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Number of results per page (max 100)',
            required=False,
            default=50
        ),
    ],
    responses={
        200: DynamicEmployeeSerializer(many=True),
        400: OpenApiExample(
            'Bad Request',
            value={'error': 'Invalid search parameters', 'details': {}}
        ),
        404: OpenApiExample(
            'Not Found',
            value={'error': 'Organization not found or inactive'}
        ),
        429: OpenApiExample(
            'Rate Limited',
            value={'error': 'Rate limit exceeded', 'message': 'Too many requests'}
        )
    },
    tags=['Employee Search']
)
@api_view(['GET'])
def search_employees(request, organization_id):
    """
    Search employees within a specific organization
    
    Query Parameters:
    - search: Search in first name, last name, and email
    - department: Filter by department
    - position: Filter by position  
    - location: Filter by location
    - status: Filter by status (active, inactive, terminated, on_leave)
    - page: Page number (default: 1)
    - page_size: Number of results per page (default: 50, max: 100)
    """
    try:
        # Get organization and ensure it exists and is active
        organization = get_object_or_404(
            Organization, 
            id=organization_id, 
            is_active=True
        )
        
        # Get organization configuration for column display
        try:
            org_config = organization.config
            visible_columns = org_config.get_default_columns()
        except OrganizationConfig.DoesNotExist:
            # Use default columns if no config exists
            visible_columns = [
                'first_name', 'last_name', 'email', 'department', 
                'position', 'location', 'status'
            ]
        
        # Validate search parameters
        search_serializer = EmployeeSearchSerializer(data=request.query_params)
        if not search_serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid search parameters',
                    'details': search_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        search_data = search_serializer.validated_data
        
        # Start with employees from this organization only
        queryset = Employee.objects.filter(organization=organization)
        
        # Apply search filters
        if search_data.get('search'):
            search_term = search_data['search']
            queryset = queryset.filter(
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(email__icontains=search_term)
            )
        
        if search_data.get('department'):
            queryset = queryset.filter(department__icontains=search_data['department'])
        
        if search_data.get('position'):
            queryset = queryset.filter(position__icontains=search_data['position'])
        
        if search_data.get('location'):
            queryset = queryset.filter(location__icontains=search_data['location'])
        
        if search_data.get('status'):
            queryset = queryset.filter(status=search_data['status'])
        
        # Order by last name, first name for consistent results
        queryset = queryset.order_by('last_name', 'first_name')
        
        # Apply pagination
        paginator = EmployeeSearchPagination()
        paginator.page_size = search_data.get('page_size', 50)
        
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            # Serialize with dynamic fields based on organization config
            serializer = DynamicEmployeeSerializer(
                page, 
                many=True, 
                visible_columns=visible_columns
            )
            
            response_data = paginator.get_paginated_response(serializer.data).data
            
            # Add metadata
            response_data['meta'] = {
                'organization': {
                    'id': str(organization.id),
                    'name': organization.name
                },
                'visible_columns': visible_columns,
                'search_params': search_data
            }
            
            return Response(response_data)
        
        # Fallback if pagination fails
        serializer = DynamicEmployeeSerializer(
            queryset, 
            many=True, 
            visible_columns=visible_columns
        )
        
        return Response({
            'results': serializer.data,
            'count': queryset.count(),
            'meta': {
                'organization': {
                    'id': str(organization.id),
                    'name': organization.name
                },
                'visible_columns': visible_columns,
                'search_params': search_data
            }
        })
        
    except Organization.DoesNotExist:
        return Response(
            {'error': 'Organization not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Http404:
        return Response(
            {'error': 'Organization not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValidationError as e:
        return Response(
            {'error': 'Validation error', 'details': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error in employee search: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def list_organizations(request):
    """
    List all active organizations
    """
    try:
        organizations = Organization.objects.filter(is_active=True)
        serializer = OrganizationSerializer(organizations, many=True)
        
        return Response({
            'organizations': serializer.data,
            'count': organizations.count()
        })
        
    except Exception as e:
        logger.error(f"Error listing organizations: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def organization_config(request, organization_id):
    """
    Get organization configuration including visible columns
    """
    try:
        organization = get_object_or_404(
            Organization, 
            id=organization_id, 
            is_active=True
        )
        
        try:
            config = organization.config
            visible_columns = config.get_default_columns()
            column_order = config.column_order or visible_columns
        except OrganizationConfig.DoesNotExist:
            visible_columns = [
                'first_name', 'last_name', 'email', 'department', 
                'position', 'location', 'status'
            ]
            column_order = visible_columns
        
        return Response({
            'organization': {
                'id': str(organization.id),
                'name': organization.name
            },
            'config': {
                'visible_columns': visible_columns,
                'column_order': column_order,
                'available_columns': [
                    {'key': key, 'label': label} 
                    for key, label in OrganizationConfig.AVAILABLE_COLUMNS
                ]
            }
        })
        
    except Organization.DoesNotExist:
        return Response(
            {'error': 'Organization not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting organization config: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def api_health(request):
    """
    Health check endpoint
    """
    return Response({
        'status': 'healthy',
        'service': 'HR Employee Search API',
        'version': '1.0.0'
    })


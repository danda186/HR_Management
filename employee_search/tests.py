from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from rest_framework import status
import json
import uuid

from .models import Organization, OrganizationConfig, Employee, RateLimitRecord


class OrganizationModelTest(TestCase):
    """Test cases for Organization model"""
    
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Organization",
            is_active=True
        )
    
    def test_organization_creation(self):
        """Test organization creation"""
        self.assertEqual(self.organization.name, "Test Organization")
        self.assertTrue(self.organization.is_active)
        self.assertIsInstance(self.organization.id, uuid.UUID)
    
    def test_organization_str_method(self):
        """Test organization string representation"""
        self.assertEqual(str(self.organization), "Test Organization")


class OrganizationConfigModelTest(TestCase):
    """Test cases for OrganizationConfig model"""
    
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Organization",
            is_active=True
        )
        self.config = OrganizationConfig.objects.create(
            organization=self.organization,
            visible_columns=['first_name', 'last_name', 'email'],
            column_order=['first_name', 'last_name', 'email']
        )
    
    def test_config_creation(self):
        """Test organization config creation"""
        self.assertEqual(self.config.organization, self.organization)
        self.assertEqual(len(self.config.visible_columns), 3)
    
    def test_get_default_columns(self):
        """Test get_default_columns method"""
        columns = self.config.get_default_columns()
        self.assertEqual(columns, ['first_name', 'last_name', 'email'])
        
        # Test with empty visible_columns
        self.config.visible_columns = []
        self.config.save()
        default_columns = self.config.get_default_columns()
        expected_default = ['first_name', 'last_name', 'email', 'department', 'position', 'location', 'status']
        self.assertEqual(default_columns, expected_default)


class EmployeeModelTest(TestCase):
    """Test cases for Employee model"""
    
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Organization",
            is_active=True
        )
        self.employee = Employee.objects.create(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            phone="+1-555-123-4567",
            department="Engineering",
            position="Software Engineer",
            location="New York",
            status="active",
            hire_date=date.today()
        )
    
    def test_employee_creation(self):
        """Test employee creation"""
        self.assertEqual(self.employee.first_name, "John")
        self.assertEqual(self.employee.last_name, "Doe")
        self.assertEqual(self.employee.organization, self.organization)
        self.assertIsInstance(self.employee.id, uuid.UUID)
    
    def test_full_name_property(self):
        """Test full_name property"""
        self.assertEqual(self.employee.full_name, "John Doe")
    
    def test_to_dict_method(self):
        """Test to_dict method"""
        data = self.employee.to_dict()
        self.assertIn('first_name', data)
        self.assertIn('last_name', data)
        self.assertEqual(data['first_name'], 'John')
        
        # Test with visible columns
        visible_columns = ['first_name', 'last_name']
        filtered_data = self.employee.to_dict(visible_columns)
        self.assertEqual(len(filtered_data), 2)
        self.assertIn('first_name', filtered_data)
        self.assertIn('last_name', filtered_data)
        self.assertNotIn('email', filtered_data)
    
    def test_employee_str_method(self):
        """Test employee string representation"""
        expected = "John Doe (Test Organization)"
        self.assertEqual(str(self.employee), expected)


class APIEndpointsTest(TestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test organizations
        self.org1 = Organization.objects.create(
            name="Organization 1",
            is_active=True
        )
        self.org2 = Organization.objects.create(
            name="Organization 2",
            is_active=True
        )
        
        # Create organization configs
        OrganizationConfig.objects.create(
            organization=self.org1,
            visible_columns=['first_name', 'last_name', 'email', 'department'],
            column_order=['first_name', 'last_name', 'email', 'department']
        )
        
        # Create test employees
        Employee.objects.create(
            organization=self.org1,
            first_name="Alice",
            last_name="Smith",
            email="alice.smith@org1.com",
            department="Engineering",
            position="Senior Engineer",
            location="San Francisco",
            status="active",
            hire_date=date.today() - timedelta(days=365)
        )
        
        Employee.objects.create(
            organization=self.org1,
            first_name="Bob",
            last_name="Johnson",
            email="bob.johnson@org1.com",
            department="Marketing",
            position="Manager",
            location="New York",
            status="active",
            hire_date=date.today() - timedelta(days=180)
        )
        
        Employee.objects.create(
            organization=self.org2,
            first_name="Charlie",
            last_name="Brown",
            email="charlie.brown@org2.com",
            department="Sales",
            position="Representative",
            location="Chicago",
            status="inactive",
            hire_date=date.today() - timedelta(days=90)
        )
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'HR Employee Search API')
    
    def test_list_organizations(self):
        """Test list organizations endpoint"""
        response = self.client.get('/api/v1/organizations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = json.loads(response.content)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['organizations']), 2)
    
    def test_organization_config(self):
        """Test organization config endpoint"""
        url = f'/api/v1/organizations/{self.org1.id}/config/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = json.loads(response.content)
        self.assertEqual(data['organization']['name'], 'Organization 1')
        self.assertIn('visible_columns', data['config'])
        self.assertEqual(len(data['config']['visible_columns']), 4)
    
    def test_search_employees_basic(self):
        """Test basic employee search"""
        url = f'/api/v1/organizations/{self.org1.id}/employees/search/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = json.loads(response.content)
        self.assertEqual(data['count'], 2)  # 2 employees in org1
        self.assertEqual(len(data['results']), 2)
        
        # Check that only configured columns are returned
        employee = data['results'][0]
        self.assertIn('first_name', employee)
        self.assertIn('last_name', employee)
        self.assertIn('email', employee)
        self.assertIn('department', employee)
        self.assertNotIn('position', employee)  # Not in visible_columns
    
    def test_search_employees_with_filters(self):
        """Test employee search with filters"""
        url = f'/api/v1/organizations/{self.org1.id}/employees/search/'
        
        # Test search by name
        response = self.client.get(url, {'search': 'Alice'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['first_name'], 'Alice')
        
        # Test search by department
        response = self.client.get(url, {'department': 'Engineering'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['department'], 'Engineering')
        
        # Test search by status
        response = self.client.get(url, {'status': 'active'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 2)  # Both employees are active
    
    def test_search_employees_pagination(self):
        """Test employee search pagination"""
        url = f'/api/v1/organizations/{self.org1.id}/employees/search/'
        response = self.client.get(url, {'page_size': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
    
    def test_organization_isolation(self):
        """Test that organizations can only see their own employees"""
        # Search in org1 should return 2 employees
        url1 = f'/api/v1/organizations/{self.org1.id}/employees/search/'
        response1 = self.client.get(url1)
        data1 = json.loads(response1.content)
        self.assertEqual(data1['count'], 2)
        
        # Search in org2 should return 1 employee
        url2 = f'/api/v1/organizations/{self.org2.id}/employees/search/'
        response2 = self.client.get(url2)
        data2 = json.loads(response2.content)
        self.assertEqual(data2['count'], 1)
        
        # Verify no cross-contamination
        org1_emails = [emp['email'] for emp in data1['results']]
        org2_emails = [emp['email'] for emp in data2['results']]
        self.assertNotIn('charlie.brown@org2.com', org1_emails)
        self.assertNotIn('alice.smith@org1.com', org2_emails)
    
    def test_invalid_organization_id(self):
        """Test search with invalid organization ID"""
        invalid_id = uuid.uuid4()
        url = f'/api/v1/organizations/{invalid_id}/employees/search/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_invalid_search_parameters(self):
        """Test search with invalid parameters"""
        url = f'/api/v1/organizations/{self.org1.id}/employees/search/'
        
        # Test invalid status
        response = self.client.get(url, {'status': 'invalid_status'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid page_size
        response = self.client.get(url, {'page_size': 1000})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RateLimitTest(TestCase):
    """Test cases for rate limiting functionality"""
    
    def setUp(self):
        self.client = Client()
        self.organization = Organization.objects.create(
            name="Test Organization",
            is_active=True
        )
        Employee.objects.create(
            organization=self.organization,
            first_name="Test",
            last_name="User",
            email="test@example.com",
            department="IT",
            position="Developer",
            location="Remote",
            status="active",
            hire_date=date.today()
        )
    
    def test_rate_limit_record_creation(self):
        """Test rate limit record creation"""
        record = RateLimitRecord.objects.create(
            ip_address="192.168.1.1",
            organization=self.organization,
            request_count=1
        )
        self.assertEqual(record.ip_address, "192.168.1.1")
        self.assertEqual(record.request_count, 1)
        self.assertEqual(record.organization, self.organization)
    
    def test_rate_limit_middleware_allows_normal_requests(self):
        """Test that rate limiting allows normal request volumes"""
        url = f'/api/v1/organizations/{self.organization.id}/employees/search/'
        
        # Make several requests (under the limit)
        for i in range(5):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_health_endpoint_bypasses_rate_limiting(self):
        """Test that health endpoint bypasses rate limiting"""
        # Health endpoint should always work
        for i in range(10):
            response = self.client.get('/api/v1/health/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)


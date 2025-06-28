from django.db import models
from django.core.validators import EmailValidator
import uuid


class Organization(models.Model):
    """Organization model to support multi-tenancy"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations'
        ordering = ['name']

    def __str__(self):
        return self.name


class OrganizationConfig(models.Model):
    """Configuration for organization-specific column display"""
    AVAILABLE_COLUMNS = [
        ('first_name', 'First Name'),
        ('last_name', 'Last Name'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('department', 'Department'),
        ('position', 'Position'),
        ('location', 'Location'),
        ('status', 'Status'),
    ]

    organization = models.OneToOneField(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='config'
    )
    visible_columns = models.JSONField(
        default=list,
        help_text="List of column names to display for this organization"
    )
    column_order = models.JSONField(
        default=list,
        help_text="Order of columns to display"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization_configs'

    def __str__(self):
        return f"Config for {self.organization.name}"

    def get_default_columns(self):
        """Return default columns if none configured"""
        if not self.visible_columns:
            return ['first_name', 'last_name', 'email', 'department', 'position', 'location', 'status']
        return self.visible_columns


class Employee(models.Model):
    """Employee model with all searchable fields"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
        ('on_leave', 'On Leave'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='employees'
    )
    
    # Personal Information
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    email = models.EmailField(validators=[EmailValidator()], db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Work Information
    department = models.CharField(max_length=100, db_index=True)
    position = models.CharField(max_length=100, db_index=True)
    location = models.CharField(max_length=100, db_index=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active',
        db_index=True
    )
    
    # Metadata
    hire_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'department']),
            models.Index(fields=['organization', 'location']),
            models.Index(fields=['first_name', 'last_name']),
        ]
        # Ensure email is unique within organization
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'email'],
                name='unique_email_per_organization'
            )
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.organization.name})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self, visible_columns=None):
        """Convert employee to dictionary with only visible columns"""
        data = {
            'id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'position': self.position,
            'location': self.location,
            'status': self.status,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
        }
        
        if visible_columns:
            return {key: data[key] for key in visible_columns if key in data}
        return data


class RateLimitRecord(models.Model):
    """Model to track rate limiting per IP/user"""
    ip_address = models.GenericIPAddressField(db_index=True)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    request_count = models.PositiveIntegerField(default=0)
    window_start = models.DateTimeField(auto_now_add=True)
    last_request = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rate_limit_records'
        indexes = [
            models.Index(fields=['ip_address', 'window_start']),
        ]

    def __str__(self):
        return f"Rate limit for {self.ip_address}: {self.request_count} requests"


from rest_framework import serializers
from .models import Employee, Organization, OrganizationConfig


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'is_active']


class EmployeeSerializer(serializers.ModelSerializer):
    """Base employee serializer with all fields"""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 
            'phone', 'department', 'position', 'location', 'status', 
            'hire_date'
        ]


class DynamicEmployeeSerializer(serializers.ModelSerializer):
    """Dynamic serializer that respects organization column configuration"""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Employee
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        # Extract visible_columns from context
        visible_columns = kwargs.pop('visible_columns', None)
        super().__init__(*args, **kwargs)
        
        if visible_columns:
            # Remove fields not in visible_columns
            allowed = set(visible_columns)
            # Always include id for reference
            allowed.add('id')
            # Add full_name if first_name and last_name are both visible
            if 'first_name' in allowed and 'last_name' in allowed:
                allowed.add('full_name')
            
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class EmployeeSearchSerializer(serializers.Serializer):
    """Serializer for search parameters"""
    search = serializers.CharField(
        required=False, 
        help_text="Search in first name, last name, and email"
    )
    department = serializers.CharField(required=False)
    position = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    status = serializers.ChoiceField(
        choices=Employee.STATUS_CHOICES,
        required=False
    )
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(
        min_value=1, 
        max_value=100, 
        required=False, 
        default=50
    )
    
    def validate(self, data):
        """Custom validation for search parameters"""
        # At least one search parameter should be provided
        search_fields = ['search', 'department', 'position', 'location', 'status']
        if not any(data.get(field) for field in search_fields):
            # Allow empty search to return all results (with pagination)
            pass
        return data


from django.core.management.base import BaseCommand
from employee_search.models import Organization, OrganizationConfig, Employee
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--employees',
            type=int,
            default=100,
            help='Number of employees to create per organization'
        )

    def handle(self, *args, **options):
        num_employees = options['employees']
        
        # Create sample organizations
        organizations_data = [
            {
                'name': 'TechCorp Solutions',
                'columns': ['first_name', 'last_name', 'email', 'department', 'position', 'status']
            },
            {
                'name': 'Global Industries',
                'columns': ['first_name', 'last_name', 'department', 'location', 'position']
            },
            {
                'name': 'Innovation Labs',
                'columns': ['first_name', 'last_name', 'email', 'phone', 'department', 'location', 'status']
            }
        ]

        departments = [
            'Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 
            'Operations', 'Product', 'Design', 'Legal', 'IT'
        ]

        positions = [
            'Software Engineer', 'Senior Engineer', 'Team Lead', 'Manager',
            'Director', 'VP', 'Analyst', 'Specialist', 'Coordinator',
            'Associate', 'Principal', 'Architect', 'Consultant'
        ]

        locations = [
            'New York', 'San Francisco', 'London', 'Tokyo', 'Singapore',
            'Berlin', 'Toronto', 'Sydney', 'Mumbai', 'São Paulo'
        ]

        first_names = [
            'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert',
            'Lisa', 'James', 'Maria', 'William', 'Jennifer', 'Richard',
            'Patricia', 'Charles', 'Linda', 'Joseph', 'Elizabeth', 'Thomas',
            'Barbara', 'Christopher', 'Susan', 'Daniel', 'Jessica', 'Matthew'
        ]

        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
            'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez',
            'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor',
            'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White'
        ]

        for org_data in organizations_data:
            # Create organization
            org, created = Organization.objects.get_or_create(
                name=org_data['name'],
                defaults={'is_active': True}
            )
            
            if created:
                self.stdout.write(f"Created organization: {org.name}")
            else:
                self.stdout.write(f"Organization already exists: {org.name}")

            # Create organization config
            config, config_created = OrganizationConfig.objects.get_or_create(
                organization=org,
                defaults={
                    'visible_columns': org_data['columns'],
                    'column_order': org_data['columns']
                }
            )

            if config_created:
                self.stdout.write(f"Created config for: {org.name}")

            # Create employees for this organization
            existing_employees = Employee.objects.filter(organization=org).count()
            employees_to_create = max(0, num_employees - existing_employees)

            if employees_to_create > 0:
                employees = []
                for i in range(employees_to_create):
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    email = f"{first_name.lower()}.{last_name.lower()}{i}@{org.name.lower().replace(' ', '')}.com"
                    
                    employee = Employee(
                        organization=org,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                        department=random.choice(departments),
                        position=random.choice(positions),
                        location=random.choice(locations),
                        status=random.choice(['active', 'active', 'active', 'inactive', 'on_leave']),  # Bias towards active
                        hire_date=date.today() - timedelta(days=random.randint(30, 1825))  # Random hire date within 5 years
                    )
                    employees.append(employee)

                Employee.objects.bulk_create(employees, batch_size=50)
                self.stdout.write(f"Created {employees_to_create} employees for {org.name}")
            else:
                self.stdout.write(f"Organization {org.name} already has {existing_employees} employees")

        total_employees = Employee.objects.count()
        total_orgs = Organization.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated database with {total_orgs} organizations and {total_employees} employees'
            )
        )


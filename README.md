# HR Employee Search API

A Django REST API microservice for searching employees within organizations with rate limiting, configurable column display, and comprehensive filtering capabilities.

## 🚀 Features

- **Employee Search**: Search employees by name, department, position, location, and status
- **Organization-based Multi-tenancy**: Complete data isolation between organizations
- **Configurable Column Display**: Each organization can configure which columns to display
- **Custom Rate Limiting**: Built-in rate limiting without external dependencies
- **Pagination**: Efficient pagination for large datasets
- **OpenAPI Documentation**: Auto-generated API documentation with Swagger UI
- **Containerized**: Ready for deployment with Docker
- **Unit Tests**: Comprehensive test coverage
- **Scalable Design**: Designed to handle millions of users

## 📋 Requirements

- Python 3.11+
- Django 5.2+
- Django REST Framework 3.16+
- Docker (for containerized deployment)

## 🛠️ Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hr_backend
   ```

2. **Create virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Populate sample data**
   ```bash
   python manage.py populate_data --employees 200
   ```

6. **Start development server**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

### Docker Deployment

1. **Quick deployment**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

2. **Manual Docker deployment**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

## 📖 API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## 🔗 API Endpoints

### Health Check
```
GET /api/v1/health/
```

### Organizations
```
GET /api/v1/organizations/
GET /api/v1/organizations/{organization_id}/config/
```

### Employee Search
```
GET /api/v1/organizations/{organization_id}/employees/search/
```

#### Query Parameters:
- `search`: Search in first name, last name, and email
- `department`: Filter by department
- `position`: Filter by position
- `location`: Filter by location
- `status`: Filter by status (active, inactive, terminated, on_leave)
- `page`: Page number (default: 1)
- `page_size`: Results per page (default: 50, max: 100)

## 📊 Usage Examples

### Search Employees
```bash
# Get all employees in an organization
curl "http://localhost:8000/api/v1/organizations/{org_id}/employees/search/"

# Search by name
curl "http://localhost:8000/api/v1/organizations/{org_id}/employees/search/?search=john"

# Filter by department and status
curl "http://localhost:8000/api/v1/organizations/{org_id}/employees/search/?department=Engineering&status=active"

# Pagination
curl "http://localhost:8000/api/v1/organizations/{org_id}/employees/search/?page=2&page_size=25"
```

### Get Organization Configuration
```bash
curl "http://localhost:8000/api/v1/organizations/{org_id}/config/"
```

## 🏗️ Architecture

### Models
- **Organization**: Multi-tenant organization model
- **OrganizationConfig**: Configurable column display per organization
- **Employee**: Employee data with searchable fields
- **RateLimitRecord**: Custom rate limiting tracking

### Rate Limiting
- **Per Minute**: 60 requests per minute per IP
- **Per Hour**: 1000 requests per hour per IP
- **Sliding Window**: Uses sliding window algorithm
- **Configurable**: Limits can be adjusted in settings

### Security Features
- **Data Isolation**: Organizations can only access their own data
- **Rate Limiting**: Prevents API abuse
- **Input Validation**: Comprehensive input validation
- **Error Handling**: Proper error responses

## 🧪 Testing

### Run Unit Tests
```bash
python manage.py test employee_search.tests
```

### Test Coverage
The test suite covers:
- Model functionality
- API endpoints
- Rate limiting
- Organization isolation
- Error handling
- Pagination

### Rate Limiting Test
```bash
python test_rate_limit.py
```

## ⚙️ Configuration

### Environment Variables
```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# CORS Settings
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOW_CREDENTIALS=True
```

### Organization Column Configuration
Each organization can configure which columns to display:

```python
# Available columns
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
```

## 🚀 Deployment

### Production Considerations
1. **Database**: Consider using PostgreSQL for production
2. **Static Files**: Configure proper static file serving
3. **Security**: Update SECRET_KEY and security settings
4. **Monitoring**: Add application monitoring
5. **Backup**: Implement database backup strategy

### Scaling
- **Database Indexing**: Optimized indexes for search performance
- **Pagination**: Efficient pagination for large datasets
- **Rate Limiting**: Prevents abuse and ensures fair usage
- **Caching**: Consider adding Redis for caching

## 📝 Management Commands

### Populate Sample Data
```bash
python manage.py populate_data --employees 500
```

### Generate OpenAPI Schema
```bash
python manage.py spectacular --file openapi-schema.yml
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
1. Check the API documentation at `/api/docs/`
2. Review the test cases for usage examples
3. Check the health endpoint at `/api/v1/health/`

## 🔧 Troubleshooting

### Common Issues

1. **Rate Limiting**: If you're getting 429 errors, wait a minute or adjust rate limits
2. **Organization Not Found**: Ensure you're using the correct organization UUID
3. **Empty Results**: Check if the organization has employees and your filters are correct

### Debug Mode
For development, set `DEBUG=True` in settings for detailed error messages.

### Logs
Check Django logs for detailed error information:
```bash
# Docker logs
docker-compose logs web

# Local development
python manage.py runserver --verbosity=2
```


from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import RateLimitRecord, Organization
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Custom rate limiting middleware using sliding window algorithm
    
    Rate limits are applied per IP address with configurable limits:
    - Requests per minute
    - Requests per hour
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Get rate limit settings from Django settings
        self.requests_per_minute = getattr(settings, 'RATE_LIMIT_REQUESTS_PER_MINUTE', 60)
        self.requests_per_hour = getattr(settings, 'RATE_LIMIT_REQUESTS_PER_HOUR', 1000)
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Process incoming request and apply rate limiting
        """
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limiting(request):
            return None
        
        # Get client IP address
        ip_address = self._get_client_ip(request)
        
        # Get organization from URL if available
        organization = self._get_organization_from_request(request)
        
        # Check rate limits
        if self._is_rate_limited(ip_address, organization):
            return self._rate_limit_response(ip_address)
        
        # Record this request
        self._record_request(ip_address, organization)
        
        return None
    
    def _should_skip_rate_limiting(self, request):
        """
        Determine if rate limiting should be skipped for this request
        """
        # Skip for health check and admin endpoints
        skip_paths = ['/api/v1/health/', '/admin/']
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _get_client_ip(self, request):
        """
        Extract client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def _get_organization_from_request(self, request):
        """
        Extract organization from URL path if available
        """
        try:
            # Parse organization ID from URL path like /api/v1/organizations/{org_id}/...
            path_parts = request.path.strip('/').split('/')
            if len(path_parts) >= 4 and path_parts[2] == 'organizations':
                org_id = path_parts[3]
                return Organization.objects.get(id=org_id, is_active=True)
        except (Organization.DoesNotExist, ValueError, IndexError):
            pass
        return None
    
    def _is_rate_limited(self, ip_address, organization=None):
        """
        Check if the IP address has exceeded rate limits
        """
        now = timezone.now()
        
        # Clean up old records first
        self._cleanup_old_records(ip_address, now)
        
        # Get or create rate limit record
        rate_record, created = RateLimitRecord.objects.get_or_create(
            ip_address=ip_address,
            organization=organization,
            defaults={
                'request_count': 0,
                'window_start': now
            }
        )
        
        # Check minute-based rate limit (sliding window)
        minute_ago = now - timedelta(minutes=1)
        minute_requests = self._count_requests_since(ip_address, organization, minute_ago)
        
        if minute_requests >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP {ip_address}: {minute_requests} requests in last minute")
            return True
        
        # Check hour-based rate limit (sliding window)
        hour_ago = now - timedelta(hours=1)
        hour_requests = self._count_requests_since(ip_address, organization, hour_ago)
        
        if hour_requests >= self.requests_per_hour:
            logger.warning(f"Rate limit exceeded for IP {ip_address}: {hour_requests} requests in last hour")
            return True
        
        return False
    
    def _count_requests_since(self, ip_address, organization, since_time):
        """
        Count requests from IP address since given time
        """
        # For simplicity, we'll use a basic counting approach
        # In production, you might want to use a more sophisticated sliding window
        try:
            records = RateLimitRecord.objects.filter(
                ip_address=ip_address,
                organization=organization,
                last_request__gte=since_time
            )
            return sum(record.request_count for record in records)
        except Exception as e:
            logger.error(f"Error counting requests: {e}")
            return 0
    
    def _record_request(self, ip_address, organization=None):
        """
        Record the current request
        """
        try:
            now = timezone.now()
            
            # Get or create rate limit record for current window
            rate_record, created = RateLimitRecord.objects.get_or_create(
                ip_address=ip_address,
                organization=organization,
                defaults={
                    'request_count': 1,
                    'window_start': now,
                    'last_request': now
                }
            )
            
            if not created:
                # Update existing record
                rate_record.request_count += 1
                rate_record.last_request = now
                rate_record.save()
                
        except Exception as e:
            logger.error(f"Error recording request: {e}")
    
    def _cleanup_old_records(self, ip_address, current_time):
        """
        Clean up old rate limit records to prevent database bloat
        """
        try:
            # Remove records older than 24 hours
            cutoff_time = current_time - timedelta(hours=24)
            RateLimitRecord.objects.filter(
                ip_address=ip_address,
                last_request__lt=cutoff_time
            ).delete()
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
    
    def _rate_limit_response(self, ip_address):
        """
        Return rate limit exceeded response
        """
        return JsonResponse(
            {
                'error': 'Rate limit exceeded',
                'message': f'Too many requests from IP {ip_address}. Please try again later.',
                'limits': {
                    'requests_per_minute': self.requests_per_minute,
                    'requests_per_hour': self.requests_per_hour
                }
            },
            status=429
        )


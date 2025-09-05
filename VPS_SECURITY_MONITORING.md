# VPS Security Monitoring & Log Management

## Issue: "Invalid HTTP request received" Warnings

These warnings are **harmless** and typically caused by:
- Bot traffic and security scanners
- Health check probes from CDNs/load balancers  
- Malformed HTTP requests from automated tools

### Solution Applied ✅
- Configured logging to suppress these warnings at ERROR level
- Added enhanced security logging for admin endpoints

## Issue: 401 Unauthorized on Admin Endpoints

Log entries like:
```
INFO: 24.142.25.79:0 - "POST /api/deployment/check-updates HTTP/1.1" 401 Unauthorized
```

This is **correct security behavior** - the system is properly rejecting unauthorized access attempts.

### Security Enhancements Added ✅
1. **Enhanced Logging**: Unauthorized admin endpoint access attempts now log IP address and User-Agent
2. **Request Monitoring**: Added client IP logging for legitimate admin requests
3. **Custom Exception Handler**: Better tracking of security events

## Recommended VPS Security Actions

### 1. Monitor Suspicious Activity
```bash
# Check for repeated unauthorized attempts
pm2 logs taxsale-backend | grep "401 Unauthorized" | tail -20

# Monitor unique IPs accessing admin endpoints
pm2 logs taxsale-backend | grep "Unauthorized access attempt" | tail -20
```

### 2. Optional: Rate Limiting (Nginx)
Add to your Nginx site configuration:
```nginx
# Rate limit admin endpoints
location /api/deployment {
    limit_req zone=admin burst=5 nodelay;
    proxy_pass http://localhost:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

# Add rate limiting zone to nginx.conf http block:
limit_req_zone $binary_remote_addr zone=admin:10m rate=10r/m;
```

### 3. Security Best Practices
- ✅ Admin endpoints require JWT authentication
- ✅ Unauthorized access is properly logged
- ✅ Invalid HTTP requests are handled gracefully
- ✅ Security events are monitored and logged

## Normal vs Concerning Log Patterns

### ✅ Normal (Security Working):
- `401 Unauthorized` responses to unauthenticated requests
- `Invalid HTTP request received` warnings (bots/probes)
- Occasional failed login attempts

### ⚠️ Investigate If You See:
- High volume of requests from single IP (>50/hour)
- Successful admin logins from unknown IPs
- 500 server errors on admin endpoints
- Repeated attempts to access sensitive endpoints

## Monitoring Commands for VPS

```bash
# View recent backend logs
pm2 logs taxsale-backend --lines 50

# Check for security events
pm2 logs taxsale-backend | grep -E "(Unauthorized|WARNING|ERROR)" | tail -20

# Monitor admin access
pm2 logs taxsale-backend | grep "Deployment.*requested by admin" | tail -10

# Check nginx access logs for unusual patterns
sudo tail -f /var/log/nginx/access.log | grep -E "(POST|admin|deployment)"
```

## Summary
The warnings you're seeing are normal security logs indicating the system is working correctly. The enhancements made will provide better monitoring while reducing log noise.
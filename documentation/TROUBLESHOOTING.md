# Troubleshooting Guide

## 🚨 Authentication Issues

### "Invalid API key" Error

**Symptoms:**
- Login form shows "Invalid API key" message
- API calls return 401 Unauthorized
- Can't access admin interface

**Diagnostic Steps:**
```bash
# 1. Check if ADMIN_API_KEY is set in Cloud Run
gcloud run services describe pixel-management \
  --region=us-central1 \
  --format='value(spec.template.spec.template.spec.containers[0].env[?name="ADMIN_API_KEY"].value)'

# 2. Check Cloud Run logs for auth errors
gcloud logs read "resource.type=cloud_run_revision" \
  --filter="textPayload:\"Invalid API key\"" \
  --limit=10

# 3. Verify API key format (should be long and secure)
echo "Your API key should be 40+ characters and cryptographically secure"
```

**Solutions:**
1. **Environment variable not set:**
   - Go to Cloud Run console → Edit & Deploy New Revision
   - Add `ADMIN_API_KEY` environment variable
   - Use a secure 32+ character key
   
2. **Wrong API key format:**
   ```bash
   # Generate proper API key
   openssl rand -base64 32
   ```

3. **Extra spaces/characters:**
   - Check environment variable for trailing spaces
   - Copy-paste carefully, avoid line breaks

### Login Form Not Appearing

**Symptoms:**
- Page loads but no login form visible
- Blank screen or loading spinner indefinitely
- Browser console errors

**Diagnostic Steps:**
```bash
# 1. Check React build exists
curl -I https://your-domain.com/static/js/main.*.js
# Should return 200 OK

# 2. Check for JavaScript errors
# Open browser console (F12) and look for errors
```

**Solutions:**
1. **Frontend build failed:**
   ```bash
   # Rebuild and redeploy
   docker-compose -f docker-compose.production.yml build frontend
   ./deploy-pixel-management.sh
   ```

2. **Browser cache issues:**
   - Hard refresh (Ctrl+F5 or Cmd+Shift+R)
   - Clear browser cache and cookies
   - Try incognito/private mode

3. **JavaScript errors:**
   - Check browser console for specific error messages
   - Common fix: Clear browser storage and refresh

### Successful Login but No Admin Interface

**Symptoms:**
- Login form accepts API key
- Redirected to dashboard but shows blank/loading
- Network requests failing

**Diagnostic Steps:**
```bash
# 1. Check sessionStorage has API key
# In browser console:
sessionStorage.getItem('admin_api_key')

# 2. Check API connectivity
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://your-domain.com/api/v1/admin/clients

# 3. Check routing is working
curl -I https://your-domain.com/admin/dashboard
# Should return 200, not 404
```

**Solutions:**
1. **API key not persisted:**
   - Check browser's sessionStorage in DevTools
   - Clear storage and log in again
   
2. **API connectivity issues:**
   - Verify CORS configuration allows your domain
   - Check Cloud Run logs for API errors
   
3. **Routing problems:**
   - Ensure nginx configuration has SPA fallback
   - Check that `try_files` directive is configured

## 🛣 Routing Issues

### Direct URL Navigation Returns 404

**Symptoms:**
- Navigating to `/admin/dashboard` shows "Not Found"
- Works when clicking links within the app
- Refreshing page breaks the app

**Root Cause:** Missing SPA fallback routing

**Diagnostic Steps:**
```bash
# Test different route types
curl -I https://your-domain.com/                    # Should work
curl -I https://your-domain.com/admin/dashboard     # Might return 404
curl -I https://your-domain.com/api/v1/admin/clients # Should work
```

**Solutions:**
1. **Development environment:**
   ```bash
   # Check nginx.conf has proper SPA routing
   grep -A 10 "location /" nginx/nginx.conf
   # Should see try_files directive
   ```

2. **Production environment:**
   ```bash
   # Verify nginx configuration is deployed
   docker-compose -f docker-compose.production.yml restart nginx
   ```

### API Routes Returning HTML Instead of JSON

**Symptoms:**
- API calls return React app HTML instead of JSON
- Postman/curl returns HTML page
- Admin interface shows parsing errors

**Root Cause:** API routes being caught by SPA fallback

**Diagnostic Steps:**
```bash
# Test API route directly
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Accept: application/json" \
     https://your-domain.com/api/v1/admin/clients

# Should return JSON, not HTML
```

**Solutions:**
1. **Check nginx configuration:**
   ```nginx
   # API routes should be handled BEFORE SPA fallback
   location /api/ {
       proxy_pass http://backend;
       # ... headers
   }
   
   location / {
       try_files $uri $uri/ @frontend;  # This comes AFTER /api/
   }
   ```

2. **Verify route order:**
   - API routes must be defined before catch-all routes
   - Check nginx configuration reload

## 🔧 Development Environment Issues

### Docker Services Won't Start

**Symptoms:**
- `docker-compose up` fails
- Port conflicts
- Service dependency issues

**Diagnostic Steps:**
```bash
# 1. Check port conflicts
netstat -tulpn | grep :3000  # Frontend port
netstat -tulpn | grep :8000  # Backend port
netstat -tulpn | grep :80    # Nginx port

# 2. Check Docker daemon
docker version
docker-compose version

# 3. Check for running containers
docker ps -a
```

**Solutions:**
1. **Port conflicts:**
   ```bash
   # Kill processes using required ports
   sudo lsof -ti:3000 | xargs kill -9
   sudo lsof -ti:8000 | xargs kill -9
   
   # Or change ports in docker-compose.local.yml
   ```

2. **Docker issues:**
   ```bash
   # Clean Docker state
   docker-compose down -v
   docker system prune -f
   docker-compose up --build
   ```

### Frontend Hot Reload Not Working

**Symptoms:**
- Changes to React code don't update browser
- Need to manually refresh
- Console shows connection errors

**Solutions:**
```bash
# 1. Check WebSocket connection
# In browser console, should see WebSocket connections

# 2. Verify nginx WebSocket proxy
# Check nginx.conf has:
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";

# 3. Restart development environment
docker-compose -f docker-compose.local.yml restart frontend
```

## 🌐 Production Deployment Issues

### Cloud Run Deployment Fails

**Symptoms:**
- `./deploy-pixel-management.sh` script fails
- Build errors during deployment
- Service doesn't start after deployment

**Diagnostic Steps:**
```bash
# 1. Check Google Cloud authentication
gcloud auth list
gcloud config get-value project

# 2. Check build logs
gcloud builds log [BUILD_ID]

# 3. Check service logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50
```

**Solutions:**
1. **Authentication issues:**
   ```bash
   # Re-authenticate
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Build failures:**
   ```bash
   # Test build locally first
   docker build -t pixel-management .
   docker run -p 8080:8080 pixel-management
   ```

3. **Memory/CPU limits:**
   - Increase Cloud Run memory allocation
   - Check for memory leaks in application logs

### Firestore Connection Errors

**Symptoms:**
- API returns 500 errors
- Logs show Firestore connection failures
- Admin interface shows "Failed to load data"

**Diagnostic Steps:**
```bash
# 1. Check Firestore API is enabled
gcloud services list --enabled | grep firestore

# 2. Check service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID

# 3. Test Firestore connectivity
# Check logs for Firestore connection errors
gcloud logs read "resource.type=cloud_run_revision" \
  --filter="textPayload:firestore" --limit=20
```

**Solutions:**
1. **Enable Firestore API:**
   ```bash
   gcloud services enable firestore.googleapis.com
   ```

2. **Service account permissions:**
   - Ensure Cloud Run service account has Firestore access
   - Check IAM roles in Google Cloud Console

## 📊 Performance Issues

### Slow Page Load Times

**Symptoms:**
- Admin interface takes >5 seconds to load
- API responses are slow
- High bounce rate

**Diagnostic Steps:**
```bash
# 1. Test response times
curl -w "@curl-format.txt" -o /dev/null -s https://your-domain.com/
# Create curl-format.txt with timing info

# 2. Check Cloud Run metrics
# Go to Cloud Run console → Metrics tab

# 3. Profile API endpoints
curl -w "Time: %{time_total}s\n" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     https://your-domain.com/api/v1/admin/clients
```

**Solutions:**
1. **Frontend optimization:**
   ```bash
   # Enable gzip in nginx (check nginx.conf)
   # Optimize React bundle size
   npm run build -- --analyze
   ```

2. **Backend optimization:**
   - Check for N+1 queries in Firestore operations
   - Add caching for frequently accessed data
   - Optimize Docker image size

3. **Network issues:**
   - Use CDN for static assets
   - Optimize images and fonts
   - Enable HTTP/2

## 🔍 Debugging Commands

### Get Current System Status
```bash
# Check all services
docker-compose ps

# Check logs
docker-compose logs frontend
docker-compose logs backend
docker-compose logs nginx

# Check Cloud Run status
gcloud run services list
gcloud run services describe pixel-management --region=us-central1
```

### Test Authentication Flow
```bash
# 1. Test login endpoint exists
curl -I https://your-domain.com/login

# 2. Test API with auth
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://your-domain.com/api/v1/admin/clients

# 3. Check sessionStorage (in browser console)
sessionStorage.getItem('admin_api_key')
```

### Network Diagnostics
```bash
# Test connectivity
ping your-domain.com
nslookup your-domain.com

# Check SSL certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Test specific routes
curl -I https://your-domain.com/health
curl -I https://your-domain.com/api/v1/config/domain/example.com
```

## 📞 Getting Help

### Information to Include in Bug Reports
1. **Environment:** Development/Production
2. **Browser:** Chrome/Firefox/Safari version
3. **Error messages:** Exact text from console/logs
4. **Steps to reproduce:** What you did before the error
5. **Expected vs actual behavior**
6. **Relevant logs:** Cloud Run, browser console, network tab

### Log Collection Commands
```bash
# Frontend logs (development)
docker-compose logs frontend --tail=100

# Backend logs (development)  
docker-compose logs backend --tail=100

# Production logs
gcloud logs read "resource.type=cloud_run_revision" \
  --freshness=1h --limit=100

# Browser logs
# Open DevTools (F12) → Console tab → Copy all messages
```

This troubleshooting guide covers the most common issues. For complex problems, start with the diagnostic steps to gather information before attempting solutions.
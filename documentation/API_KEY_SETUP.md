# Admin API Key Setup Guide

## 🚀 Quick Start

After deploying with `./deploy-pixel-management.sh`, follow these steps to secure your admin interface with API key authentication.

### Step 1: Access Cloud Run Console
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **Cloud Run** service
3. Click on **pixel-management** service

### Step 2: Configure Environment Variables
1. Click **"EDIT & DEPLOY NEW REVISION"** button
2. Click on **"Variables & Secrets"** tab
3. In the **Environment Variables** section, click **"ADD VARIABLE"**

### Step 3: Add Admin API Key
Add this environment variable:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `ADMIN_API_KEY` | `[your secure API key]` | Admin authentication token |

**API Key Requirements:**
- Minimum 32 characters recommended
- Use cryptographically secure random generation
- Store securely (never commit to code)

**Generate a secure API key:**
```bash
# Option 1: Using openssl (recommended)
openssl rand -base64 32

# Option 2: Using Python
python3 -c "import secrets; print(f'evothesis_admin_{secrets.token_urlsafe(32)}')"

# Option 3: Online generator (use reputable source)
# https://randomkeygen.com/ (use "Fort Knox" strength)
```

### Step 4: Deploy Changes
1. Click **"DEPLOY"** button at the bottom
2. Wait for deployment to complete (1-2 minutes)
3. Service will restart with API key authentication enabled

## 🔒 Accessing the Admin Interface

### Web Interface Login
1. Visit your service URL
2. You'll see the admin login form
3. Enter your API key in the **"Admin API Key"** field
4. Click **"Sign In"**
5. You'll be redirected to the admin dashboard

### API Access
Use the API key in the Authorization header:

```bash
# List all clients
curl -H "Authorization: Bearer YOUR_API_KEY_HERE" \
     https://your-service-url.run.app/api/v1/admin/clients

# Create a new client
curl -X POST \
     -H "Authorization: Bearer YOUR_API_KEY_HERE" \
     -H "Content-Type: application/json" \
     -d '{"name":"Test Client","email":"test@example.com","client_type":"business","owner":"owner123","privacy_level":"standard","deployment_type":"shared"}' \
     https://your-service-url.run.app/api/v1/admin/clients
```

## 🆘 Troubleshooting

### Issue: "Invalid API key" error
**Symptoms:** Login form shows error, API calls return 401
**Solutions:**
1. Verify `ADMIN_API_KEY` is set correctly in Cloud Run console
2. Check for extra spaces or newlines in the environment variable
3. Ensure you're copying the full API key (no truncation)
4. Redeploy the revision after making changes

### Issue: Login form not appearing
**Symptoms:** Page loads but no login form visible
**Solutions:**
1. Check browser console for JavaScript errors
2. Clear browser cache and cookies
3. Try incognito/private browsing mode
4. Verify the service is fully deployed and running

### Issue: Can't access after successful login
**Symptoms:** Login succeeds but admin interface doesn't load
**Solutions:**
1. Check browser storage for the API key (should be in sessionStorage)
2. Verify routing is working by manually navigating to `/admin/dashboard`
3. Check network tab for failed API calls
4. Look at Cloud Run logs for authentication errors

### Issue: No API key was generated
**Symptoms:** Logs show "Generated admin key: ..." message
**Solution:** This happens when `ADMIN_API_KEY` is not set
1. The system generates a temporary key for development
2. Check Cloud Run logs for the generated key (search for "Generated admin key")
3. Set the `ADMIN_API_KEY` environment variable properly
4. Redeploy to use your permanent key

## 🔧 Advanced Configuration

### Rotating API Keys
To change the admin API key:
1. Generate a new secure API key (see generation commands above)
2. Update `ADMIN_API_KEY` in Cloud Run console
3. Click **"DEPLOY"** to create new revision
4. All existing sessions will be invalidated
5. Users must log in again with the new key

### Multiple Environments
For staging/production separation:
1. Deploy separate Cloud Run services
2. Use different API keys for each environment
3. Use different service names (e.g., `pixel-management-staging`)
4. Document which key belongs to which environment

### Monitoring Access
Check Cloud Run logs for authentication events:
```
# Successful authentication
✅ Admin access granted to admin_key_...abc12345

# Failed authentication attempt  
⚠️ Invalid API key used for admin access: ...xyz67890

# Admin actions (audit trail)
📝 ADMIN_AUDIT: {"action":"create_client","api_key_id":"admin_key_...abc12345"}
```

## 🔐 Security Best Practices

### API Key Management:
1. **Generate strong keys** (32+ characters, cryptographically secure)
2. **Store securely** (use password managers, secure environment variables)
3. **Rotate regularly** (every 90 days recommended)
4. **Limit access** to only necessary team members
5. **Monitor usage** through Cloud Run logs
6. **Never commit keys** to version control

### Network Security:
- ✅ **HTTPS only** (Cloud Run provides this automatically)
- ✅ **CORS configured** (limited to specific origins)
- ✅ **Rate limiting** (built into the application)

### Team Access:
- Document who has access to the admin API key
- Use a secure password manager for credential sharing
- Consider implementing multiple API keys for different team members (future enhancement)
- Regularly audit who has access

## 🛠 Development vs Production

### Development Mode
If `ADMIN_API_KEY` is not set, the system will:
- Generate a temporary API key automatically
- Log the key to the console (last 8 characters shown)
- Show a warning message to set the environment variable

### Production Mode
Always set `ADMIN_API_KEY` explicitly:
- No automatic key generation
- No keys logged to console  
- Secure authentication required for all admin operations

### Environment Variable Priority
```
1. ADMIN_API_KEY (explicit) ← Use this for production
2. Auto-generated key ← Development fallback only
```

## 📱 Supported Clients

The API key authentication works with:
- ✅ **Web interface** (React admin panel)
- ✅ **API clients** (curl, Postman, custom applications)
- ✅ **Mobile applications** (via HTTP Authorization header)
- ✅ **Automated scripts** (deployment, monitoring tools)

## 🔄 Migration from Basic Auth

If you previously used username/password authentication:
1. Remove old `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables
2. Add new `ADMIN_API_KEY` environment variable
3. Update any scripts or tools to use Bearer token authentication
4. Test the new authentication flow thoroughly

The new API key system is more secure and easier to manage than username/password authentication.
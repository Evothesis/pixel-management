# Cloud Run Authentication Setup Guide

## 🚀 Quick Start

After deploying with `./deploy-production.sh`, follow these steps to secure your admin interface:

### Step 1: Access Cloud Run Console
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **Cloud Run** service
3. Click on **pixel-management** service

### Step 2: Configure Environment Variables
1. Click **"EDIT & DEPLOY NEW REVISION"** button
2. Click on **"Variables & Secrets"** tab
3. In the **Environment Variables** section, click **"ADD VARIABLE"**

### Step 3: Add Authentication Variables
Add these two environment variables:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `ADMIN_USERNAME` | `admin` | Admin login username |
| `ADMIN_PASSWORD` | `[your secure password]` | Admin login password (8+ chars) |

**Password Requirements:**
- Minimum 8 characters
- Use a strong, unique password
- Consider using a password manager

### Step 4: Deploy Changes
1. Click **"DEPLOY"** button at the bottom
2. Wait for deployment to complete (1-2 minutes)
3. Service will restart with authentication enabled

## 🔒 Verification

### Check Authentication Status
1. Visit your service URL
2. You should see a browser login prompt
3. Enter your username and password
4. You should be able to access the admin interface

### Check Logs (Optional)
1. Go to **"LOGS"** tab in Cloud Run console
2. Look for authentication status messages:
   ```
   ✅ Basic auth configured for user: admin
   🔐 Authentication status: username=admin, password_set=True
   ```

## 🆘 Troubleshooting

### Issue: Still seeing temporary password in logs
**Solution:** Environment variables not set correctly
1. Verify `ADMIN_PASSWORD` is set in Cloud Run console
2. Redeploy the revision
3. Check logs again

### Issue: Browser not prompting for login
**Solution:** Clear browser cache and cookies
1. Clear browser cache for your domain
2. Try incognito/private browsing mode
3. Ensure you're accessing the correct URL

### Issue: "Invalid credentials" error
**Solution:** Check username/password
1. Verify `ADMIN_USERNAME` matches what you're typing
2. Verify `ADMIN_PASSWORD` matches exactly (case-sensitive)
3. Check for extra spaces in environment variables

## 🔧 Advanced Configuration

### Change Username
To use a different admin username:
1. Set `ADMIN_USERNAME` to your preferred value
2. Redeploy the revision
3. Use the new username when logging in

### Rotate Password
To change the admin password:
1. Update `ADMIN_PASSWORD` in Cloud Run console
2. Redeploy the revision
3. Use the new password when logging in

### Multiple Environments
For staging/production separation:
1. Deploy separate Cloud Run services
2. Use different environment variable values
3. Use different service names (e.g., `pixel-management-staging`)

## 📱 Mobile/API Access

The Basic Auth works with:
- ✅ Web browsers (Chrome, Firefox, Safari)
- ✅ API clients (curl, Postman, etc.)
- ✅ Mobile browsers

Example API call with authentication:
```bash
curl -u admin:yourpassword https://your-service-url.run.app/api/v1/admin/clients
```

## 🔐 Security Best Practices

### For Production Use:
1. **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
2. **Rotate passwords regularly** (every 90 days)
3. **Limit access** to only necessary team members
4. **Monitor logs** for authentication attempts
5. **Use HTTPS only** (Cloud Run provides this automatically)

### For Team Access:
- Consider implementing JWT-based auth in the future for multiple users
- Document who has access to the admin credentials
- Use a secure password manager for credential sharing
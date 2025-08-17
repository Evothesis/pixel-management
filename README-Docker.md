# Docker Compose Environment Guide

## Overview
This project uses a single `docker-compose.yml` file with environment-specific configuration files. This approach ensures consistency across environments while allowing different settings per deployment.

## Environment Files

- `.env.development` - Local development with hot-reload
- `.env.staging` - Staging environment configuration  
- `.env.production` - Production environment configuration
- `.env.local` - Legacy local development file (use `.env.development` instead)

## Usage

### Development
```bash
# Full development environment with PostgreSQL + geolocation data
docker compose --env-file .env.development up --build

# Just backend and database (for frontend development)
docker compose --env-file .env.development --profile database --profile backend up

# Initialize geolocation database (run once)
docker compose --env-file .env.development --profile init up postgres-init
```

### Staging
```bash
# Staging deployment
docker compose --env-file .env.staging up -d

# With Nginx reverse proxy
docker compose --env-file .env.staging --profile production up -d
```

### Production
```bash
# Production deployment with all services
docker compose --env-file .env.production --profile all up -d

# Production with Nginx and SSL
docker compose --env-file .env.production --profile production up -d
```

## Service Profiles

The docker-compose file uses profiles to control which services run:

- `database` - PostgreSQL database only
- `backend` - FastAPI pixel management service
- `frontend` - React admin interface
- `nginx` - Reverse proxy with SSL support
- `init` - One-time database initialization
- `production` - Full production stack (backend + frontend + nginx)
- `all` - All services including database

## Environment Variables

### Required for All Environments
- `ADMIN_API_KEY` - Secure API key for admin access
- `COLLECTION_API_URL` - External collection service endpoint
- `CORS_ORIGINS` - Allowed origins for CORS

### Development-Specific
- `BACKEND_VOLUME_MOUNT=./backend/app` - Hot-reload for backend
- `FRONTEND_SRC_MOUNT=./frontend/src` - Hot-reload for frontend
- `BACKEND_COMMAND` - Includes `--reload` flag

### Production-Specific  
- `NGINX_SSL_CERTS` - Path to SSL certificates
- `BACKEND_COMMAND` - Includes `--workers 4` for performance
- Hot-reload mounts disabled (`/dev/null`)

## Geolocation Data Management

The system uses DB-IP Lite database (7.9M+ records) for IP geolocation with optimized two-stage initialization:

### One-Time Data Download
```bash
# Download and cache geolocation data locally (677MB CSV)
./scripts/download-geolocation-data.sh
```

This downloads the uncompressed CSV database to `./data/geolocation/` and caches it locally. The data is reused across container rebuilds.

### Database Population Process
```bash
# Populate PostgreSQL with cached data using optimized process
docker compose --env-file .env.development run --rm postgres-init
```

**Two-Stage Database Initialization:**
1. **Schema Creation** - Table structure without indexes (via init_geolocation_db.sql)
2. **Data Population** - ~30 seconds via PostgreSQL COPY FROM for maximum performance
3. **Index Creation** - ~3 minutes after data load for optimal performance

**Performance Characteristics:**
- Total setup time: Under 4 minutes
- Uses PostgreSQL COPY FROM (fastest bulk import method)
- Skip-if-exists logic prevents duplicate population
- Persistent volumes maintain database between restarts

**Benefits of this approach:**
- ✅ **Optimal performance** - PostgreSQL COPY FROM is fastest import method
- ✅ **No memory issues** - processes local CSV file directly
- ✅ **Faster rebuilds** - data persists across container rebuilds
- ✅ **Bandwidth efficient** - downloads once, reuses many times
- ✅ **Offline development** - works without internet after initial download

## Port Mapping

Default ports (configurable via environment):
- Frontend: 3000
- Backend API: 8000  
- PostgreSQL: 5433
- Nginx HTTP: 80
- Nginx HTTPS: 443

## Development Workflow

### First Time Setup (Recommended)
```bash
# Automated setup (downloads data, starts services, initializes DB)
./scripts/setup-development.sh
```

### Manual Setup
1. **Download geolocation data:**
   ```bash
   ./scripts/download-geolocation-data.sh
   ```

2. **Start database and initialize:**
   ```bash
   docker compose --env-file .env.development --profile database up -d
   docker compose --env-file .env.development run --rm postgres-init
   ```

3. **Start all services:**
   ```bash
   docker compose --env-file .env.development --profile database --profile backend --profile frontend up -d
   ```

### Daily Development
```bash
# Start all services (data already exists)
docker compose --env-file .env.development --profile database --profile backend --profile frontend up

# Backend only (if running frontend separately)
docker compose --env-file .env.development --profile database --profile backend up
```

## Production Deployment

1. **Configure environment:**
   ```bash
   cp .env.production .env.prod
   # Edit .env.prod with actual values
   ```

2. **Deploy:**
   ```bash
   docker compose --env-file .env.prod --profile production up -d
   ```

## Troubleshooting

- **Database connection issues:** Ensure PostgreSQL is healthy before backend starts
- **Frontend proxy errors:** Check `REACT_APP_API_URL` matches backend service
- **CORS errors:** Verify `CORS_ORIGINS` includes your frontend URL
- **Hot-reload not working:** Check volume mounts in development environment file
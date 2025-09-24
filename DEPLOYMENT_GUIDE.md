# SynVectorDB githubshare - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying SynVectorDB githubshare in various environments.

## Prerequisites

- **Python**: 3.8 or higher
- **Memory**: 4GB+ RAM recommended
- **Storage**: 2GB+ available disk space
- **Network**: Internet connection for initial setup

## Local Deployment

### Method 1: Management Script (Recommended)

```bash
# Start the service
./manage.sh start

# Check status
./manage.sh status

# Run comprehensive tests
./manage.sh test

# View logs
./manage.sh logs

# Stop the service
./manage.sh stop
```

### Method 2: Manual Setup

```bash
# Install dependencies
cd streamlit_app
pip install -r requirements.txt

# Start application
streamlit run Home.py --server.port 8501 --server.address 0.0.0.0
```

### Method 3: Direct Python

```bash
# From project root
python -m streamlit run streamlit_app/Home.py --server.port 8501
```

## Docker Deployment

### Build Docker Image

```bash
# Build the image
docker build -t synvectordb-githubshare .

# Check image size
docker images synvectordb-githubshare
```

### Run Docker Container

```bash
# Run container
docker run -d \
  --name synvectordb-app \
  -p 8501:8501 \
  -v $(pwd)/logs:/app/logs \
  synvectordb-githubshare

# Check container status
docker ps

# View logs
docker logs synvectordb-app

# Stop container
docker stop synvectordb-app
docker rm synvectordb-app
```

### Docker Compose (If Available)

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs

# Stop services
docker-compose down
```

## Testing

### Comprehensive Test Suite

```bash
# Run all tests
python3 test_suite.py

# Expected output:
# Database Functionality: ✅ PASS
# Streamlit Application: ✅ PASS  
# Performance Benchmarks: ✅ PASS
# Data Integrity: ✅ PASS
# Overall: 4/4 tests passed (100.0%)
```

### Docker Testing

```bash
# Test Docker build (if Docker available)
./docker-test.sh --build

# Test Docker run
./docker-test.sh --run

# Run all Docker tests
./docker-test.sh
```

### Manual Testing

```bash
# Test database connectivity
curl http://localhost:8501/healthz

# Test main page
curl http://localhost:8501

# Test application responsiveness
curl -w '%{time_total}' http://localhost:8501
```

## Performance Optimization

### Database Performance

- **Connection Pooling**: Implemented in utils.py
- **Query Optimization**: Indexed searches on key fields
- **Caching**: Streamlit caching for expensive operations

### Application Performance

- **Memory Usage**: ~200MB baseline
- **Response Time**: <3s for most operations
- **Concurrent Users**: Supports 10+ simultaneous users

### Monitoring

```bash
# Monitor resource usage
./manage.sh status

# View performance logs
./manage.sh logs | grep "Performance"

# Run benchmarks
python3 test_suite.py | grep "Performance"
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check database files
   ls -la data/parts.*
   
   # Verify permissions
   chmod 644 data/parts.db
   ```

2. **Port Already in Use**
   ```bash
   # Find process using port 8501
   lsof -i :8501
   
   # Kill process
   kill -9 <PID>
   ```

3. **Memory Issues**
   ```bash
   # Check memory usage
   free -h
   
   # Restart with lower memory settings
   STREAMLIT_SERVER_MAX_UPLOAD_SIZE=50 ./manage.sh start
   ```

4. **Permission Denied**
   ```bash
   # Fix script permissions
   chmod +x manage.sh docker-test.sh test_suite.py
   
   # Fix data permissions
   chmod -R 644 data/
   ```

### Debug Mode

```bash
# Start in debug mode
STREAMLIT_LOGGER_LEVEL=debug ./manage.sh start

# View detailed logs
./manage.sh logs 100
```

## Production Deployment

### Security Considerations

1. **Network Security**
   - Use reverse proxy (nginx/Apache)
   - Enable HTTPS
   - Configure firewall rules

2. **Application Security**
   - Run as non-root user
   - Limit file permissions
   - Regular security updates

3. **Data Security**
   - Backup database files
   - Monitor access logs
   - Implement rate limiting

### Scaling

1. **Horizontal Scaling**
   - Use load balancer
   - Deploy multiple instances
   - Shared database storage

2. **Vertical Scaling**
   - Increase memory allocation
   - Use faster storage (SSD)
   - Optimize database queries

### Monitoring

1. **Application Monitoring**
   - Health checks every 30s
   - Performance metrics collection
   - Error rate monitoring

2. **Infrastructure Monitoring**
   - CPU/Memory usage
   - Disk space monitoring
   - Network connectivity

## Environment Variables

```bash
# Streamlit Configuration
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Application Configuration
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Performance Tuning
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
export STREAMLIT_SERVER_ENABLE_CORS=false
```

## Backup and Recovery

### Database Backup

```bash
# Backup database files
cp data/parts.db backup/parts_$(date +%Y%m%d).db
cp data/parts.duckdb backup/parts_$(date +%Y%m%d).duckdb

# Verify backup
sqlite3 backup/parts_$(date +%Y%m%d).db "SELECT COUNT(*) FROM parts;"
```

### Application Backup

```bash
# Backup entire application
tar -czf synvectordb_backup_$(date +%Y%m%d).tar.gz \
  streamlit_app/ data/ logs/ *.sh *.py *.md

# Restore from backup
tar -xzf synvectordb_backup_YYYYMMDD.tar.gz
```

## Support

### Getting Help

1. **Documentation**: Check README.md and this guide
2. **Testing**: Run test_suite.py for diagnostics
3. **Logs**: Check logs/ directory for error details
4. **Community**: Submit issues to project repository

### Contact Information

- **Principal Investigator**: Dr. Jie Song
- **Email**: jiesong@whu.edu.cn
- **Institution**: Wuhan University
- **Project Repository**: https://github.com/AilurusBio/synbio-parts-db

---

**Note**: This deployment guide covers the githubshare demonstration version. For production deployment with full features, refer to the main project documentation.

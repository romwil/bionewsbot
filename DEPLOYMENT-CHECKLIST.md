# BioNewsBot Deployment Checklist

## Pre-Deployment

### System Requirements
- [ ] Ubuntu 20.04+ or compatible Linux distribution
- [ ] Docker Engine 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] Minimum 16GB RAM available
- [ ] Minimum 100GB storage available
- [ ] Ports 80, 443 available (production)

### Security Setup
- [ ] Create dedicated user account for BioNewsBot
- [ ] Configure firewall rules (UFW or iptables)
- [ ] Generate strong passwords for all services
- [ ] Obtain SSL certificates (Let's Encrypt recommended)
- [ ] Configure fail2ban for brute force protection

### API Keys & Credentials
- [ ] OpenAI API key obtained and tested
- [ ] PubMed API key registered
- [ ] News API key acquired
- [ ] Slack workspace configured with bot token
- [ ] Slack signing secret and app token configured

## Deployment Steps

### 1. Environment Configuration
- [ ] Clone repository to production server
- [ ] Copy `.env.example` to `.env`
- [ ] Update all environment variables in `.env`
- [ ] Set strong passwords for PostgreSQL and Redis
- [ ] Configure domain names and URLs

### 2. Initial Setup
- [ ] Run `./setup.sh` to initialize platform
- [ ] Verify all Docker images built successfully
- [ ] Confirm database migrations completed
- [ ] Check initial seed data loaded

### 3. Service Verification
- [ ] Run `./health-check.py` to verify all services
- [ ] Access frontend at configured URL
- [ ] Test API endpoints via `/docs`
- [ ] Verify Slack notifications working
- [ ] Check scheduler is processing tasks

### 4. SSL/TLS Configuration
- [ ] Install certbot: `sudo apt-get install certbot`
- [ ] Generate certificates: `sudo certbot certonly --standalone -d yourdomain.com`
- [ ] Update nginx configuration with SSL settings
- [ ] Restart nginx service
- [ ] Verify HTTPS access working

### 5. Monitoring Setup
- [ ] Enable monitoring profile: `docker-compose --profile monitoring up -d`
- [ ] Access Prometheus at port 9090
- [ ] Configure Grafana admin password
- [ ] Import BioNewsBot dashboards
- [ ] Set up alerting rules

### 6. Backup Configuration
- [ ] Configure automated database backups
- [ ] Set up backup retention policy
- [ ] Test backup restoration process
- [ ] Configure offsite backup storage
- [ ] Schedule cron jobs for regular backups

### 7. Performance Optimization
- [ ] Configure PostgreSQL performance settings
- [ ] Optimize Redis memory settings
- [ ] Set up CDN for static assets (optional)
- [ ] Configure nginx caching rules
- [ ] Enable gzip compression

### 8. Security Hardening
- [ ] Disable root SSH access
- [ ] Configure SSH key-only authentication
- [ ] Set up intrusion detection (fail2ban)
- [ ] Configure log rotation
- [ ] Enable audit logging

## Post-Deployment

### Testing
- [ ] Run integration tests: `./run-tests.sh`
- [ ] Perform load testing
- [ ] Test disaster recovery procedures
- [ ] Verify all API endpoints
- [ ] Test notification delivery

### Documentation
- [ ] Document server access procedures
- [ ] Create runbook for common operations
- [ ] Document backup/restore procedures
- [ ] Update team wiki with deployment info
- [ ] Create incident response plan

### Monitoring
- [ ] Set up uptime monitoring (UptimeRobot, Pingdom)
- [ ] Configure error tracking (Sentry)
- [ ] Set up log aggregation
- [ ] Create alerting rules for critical events
- [ ] Configure performance monitoring

## Maintenance Tasks

### Daily
- [ ] Check service health status
- [ ] Review error logs
- [ ] Monitor disk space usage
- [ ] Verify backup completion

### Weekly
- [ ] Review performance metrics
- [ ] Check for security updates
- [ ] Analyze usage patterns
- [ ] Test backup restoration

### Monthly
- [ ] Update dependencies
- [ ] Review and rotate logs
- [ ] Performance optimization review
- [ ] Security audit
- [ ] Capacity planning review

## Troubleshooting Checklist

### Service Won't Start
- [ ] Check Docker logs: `docker-compose logs [service]`
- [ ] Verify environment variables set correctly
- [ ] Check port conflicts
- [ ] Verify file permissions
- [ ] Check disk space

### Database Connection Issues
- [ ] Verify PostgreSQL is running
- [ ] Check connection string in .env
- [ ] Test with psql client
- [ ] Check firewall rules
- [ ] Verify user permissions

### Performance Issues
- [ ] Check CPU and memory usage
- [ ] Review slow query logs
- [ ] Check Redis hit rate
- [ ] Analyze nginx access logs
- [ ] Review application metrics

## Emergency Procedures

### Service Outage
1. Run health check: `./health-check.py`
2. Check Docker status: `docker-compose ps`
3. Review logs: `docker-compose logs --tail=100`
4. Restart affected service: `docker-compose restart [service]`
5. If persistent, rebuild: `./setup.sh rebuild`

### Data Recovery
1. Stop affected services: `docker-compose stop`
2. Restore from backup: `./scripts/restore-backup.sh [backup-file]`
3. Verify data integrity
4. Restart services: `docker-compose up -d`
5. Run health checks

### Security Incident
1. Isolate affected systems
2. Preserve logs for analysis
3. Reset all credentials
4. Apply security patches
5. Conduct post-mortem analysis

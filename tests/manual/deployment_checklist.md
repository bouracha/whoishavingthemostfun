# Deployment Manual Testing Checklist

Use this checklist to verify production deployment functionality on EC2.

## Prerequisites
- [ ] Access to EC2 instance via SSH
- [ ] Domain `whoishavingmostfun.com` configured
- [ ] SSL certificate installed and valid
- [ ] Nginx configured as reverse proxy

---

## Pre-Deployment Checks

### Code & Configuration
- [ ] Latest code pulled from GitHub (`git pull`)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Virtual environment activated
- [ ] Configuration files updated if needed

### Infrastructure
- [ ] EC2 instance running and accessible
- [ ] Security groups allow ports 80, 443, 22
- [ ] DNS resolves correctly (`nslookup whoishavingmostfun.com`)
- [ ] SSL certificate valid and not expired

---

## Deployment Process

### Update Script Execution
- [ ] Run `./update.sh` from `/home/ec2-user/site/`
- [ ] Script completes without errors
- [ ] Flask server starts successfully
- [ ] Charts regenerate for all games
- [ ] No Python import errors

### Service Status
- [ ] Flask server running (`ps aux | grep python`)
- [ ] Nginx running (`systemctl status nginx`)
- [ ] Flask listening on port 8080 (`netstat -tlnp | grep 8080`)
- [ ] Nginx listening on ports 80/443 (`netstat -tlnp | grep -E ':(80|443)'`)

---

## HTTPS & SSL Verification

### Certificate Validation
- [ ] `https://whoishavingmostfun.com` loads without warnings
- [ ] `https://www.whoishavingmostfun.com` loads without warnings
- [ ] SSL certificate shows valid and trusted
- [ ] Certificate expiry date is in the future
- [ ] Green lock icon appears in browser

### HTTP Redirect
- [ ] `http://whoishavingmostfun.com` redirects to HTTPS
- [ ] `http://www.whoishavingmostfun.com` redirects to HTTPS
- [ ] Redirect happens automatically (301/302 status)

---

## API Functionality

### Health Endpoint
- [ ] `curl https://whoishavingmostfun.com/api/health` returns 200
- [ ] Response contains `{"status": "healthy"}`
- [ ] Response time under 1 second
- [ ] CORS headers present

### Player Management API
- [ ] POST to `/api/players/chess` works
- [ ] POST to `/api/players/pingpong` works  
- [ ] POST to `/api/players/backgammon` works
- [ ] Invalid game returns 400 error
- [ ] Missing player name returns 400 error
- [ ] Successful addition returns 200 with success message

---

## Static File Serving

### HTML Pages
- [ ] `https://whoishavingmostfun.com/` serves index.html
- [ ] `https://whoishavingmostfun.com/chess.html` serves chess page
- [ ] `https://whoishavingmostfun.com/pingpong.html` serves pingpong page
- [ ] `https://whoishavingmostfun.com/backgammon.html` serves backgammon page

### Generated Charts
- [ ] Chess leaderboard image loads
- [ ] Chess rating progress chart loads
- [ ] Ping pong leaderboard image loads
- [ ] Ping pong rating progress chart loads
- [ ] Backgammon leaderboard image loads
- [ ] Backgammon rating progress chart loads

### Static Assets
- [ ] Player photos load from `/images/players/`
- [ ] Medal icons load from `/images/medals/`
- [ ] Monica image loads from `/images/`
- [ ] No 404 errors for static assets

---

## Performance Testing

### Response Times
- [ ] Homepage loads in under 2 seconds
- [ ] Game pages load in under 3 seconds
- [ ] API health check responds in under 500ms
- [ ] Add player API responds in under 5 seconds

### Concurrent Users
- [ ] Multiple browser tabs work simultaneously
- [ ] API handles concurrent requests properly
- [ ] No 500 errors under normal load
- [ ] Charts display correctly for all users

---

## Mobile & Cross-Browser

### Mobile Devices
- [ ] Site loads on mobile Safari (iOS)
- [ ] Site loads on mobile Chrome (Android)
- [ ] Touch interactions work properly
- [ ] Responsive layout functions correctly

### Desktop Browsers
- [ ] Chrome: All functionality works
- [ ] Firefox: All functionality works
- [ ] Safari: All functionality works
- [ ] Edge: All functionality works

---

## Backend Operations

### Player Management
- [ ] `cd code && python3 manage_players.py list chess` works
- [ ] Player deletion works with confirmation
- [ ] Charts regenerate after player deletion
- [ ] Database CSV files are properly managed

### Logging & Monitoring
- [ ] Flask logs available (`tail -f server.log`)
- [ ] Nginx logs available (`tail -f /var/log/nginx/access.log`)
- [ ] No critical errors in logs
- [ ] Log rotation working properly

### Backup & Recovery
- [ ] Database CSV files backed up if needed
- [ ] Configuration files documented
- [ ] Recovery procedures tested

---

## Security Verification

### HTTPS Configuration
- [ ] Only secure protocols enabled (TLS 1.2+)
- [ ] HTTP redirects to HTTPS
- [ ] HSTS headers present (if configured)
- [ ] No mixed content warnings

### API Security
- [ ] CORS configured properly
- [ ] No sensitive information exposed
- [ ] Input validation working
- [ ] Error messages don't leak system info

### System Security
- [ ] Only necessary ports open (22, 80, 443)
- [ ] SSH key authentication working
- [ ] File permissions secure
- [ ] No unnecessary services running

---

## Rollback Plan

### If Deployment Fails
- [ ] Previous version code available
- [ ] Database backup available
- [ ] Rollback procedure documented
- [ ] Emergency contacts available

### Recovery Steps
1. [ ] SSH to EC2 instance
2. [ ] Stop current Flask server (`kill $(cat server.pid)`)
3. [ ] Revert code changes (`git checkout previous_commit`)
4. [ ] Restart server (`./update.sh`)
5. [ ] Verify functionality

---

## Post-Deployment Verification

### Full User Journey
- [ ] Visit homepage
- [ ] Navigate to each game page
- [ ] Add a test player to each game
- [ ] Verify charts update
- [ ] Delete test players
- [ ] Verify charts update again

### Monitoring Setup
- [ ] Set up alerts for server downtime
- [ ] Monitor SSL certificate expiry
- [ ] Track API response times
- [ ] Monitor disk space usage

---

## Test Results

**Date:** ___________  
**Deployer:** ___________  
**Commit Hash:** ___________  
**Environment:** Production EC2

### Deployment Status:
- [ ] Successful deployment - All tests passed
- [ ] Deployment with minor issues - Documented below
- [ ] Failed deployment - Rollback initiated

### Issues Found:
1. 
2. 
3. 

### Performance Metrics:
- Homepage load time: _____ seconds
- API health response: _____ ms
- Add player response: _____ seconds

### Next Steps:
- [ ] Monitor for 24 hours
- [ ] Update documentation if needed
- [ ] Schedule next deployment window
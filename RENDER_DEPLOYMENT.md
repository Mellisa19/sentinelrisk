# 🚀 Render Deployment Guide

## 📋 Render Cloud Deployment

### **Step 1: Prepare for Render**

#### **Create Render Account**
1. Go to [render.com](https://render.com)
2. Sign up (GitHub integration recommended)
3. Create a new account

#### **Prepare Repository**
1. Push your code to GitHub (we had issues earlier, but let's try again)
2. Ensure all files are committed

### **Step 2: Render Services Configuration**

#### **Backend Service (Web Service)**
```yaml
# render.yaml
services:
  - type: web
    name: sentinelrisk-api
    env: python
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn src.services.api:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        value: postgresql://user:pass@host:5432/dbname
      - key: SECRET_KEY
        generateValue: true
      - key: MODEL_PATH
        value: models/xgboost_fraud.pkl
      - key: PREPROCESSOR_PATH
        value: models/preprocessor.pkl
```

#### **Frontend Service (Static Site)**
```yaml
# Add to render.yaml
  - type: web
    name: sentinelrisk-frontend
    env: static
    plan: free
    buildCommand: "cd app && npm install && npm run build"
    publishPath: app/dist
    envVars:
      - key: VITE_API_URL
        value: https://sentinelrisk-api.onrender.com
```

#### **Database Service (PostgreSQL)**
```yaml
# Add to render.yaml
  - type: postgres
    name: sentinelrisk-db
    plan: free
    databaseName: sentinelrisk
    user: sentinel_user
```

### **Step 3: Environment Variables**

#### **Production Environment**
```bash
# Security
SECRET_KEY=your-generated-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Database (Render provides this)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Model Paths
MODEL_PATH=models/xgboost_fraud.pkl
PREPROCESSOR_PATH=models/preprocessor.pkl

# CORS
ALLOWED_ORIGINS=https://your-frontend-url.onrender.com

# Monitoring
LOG_LEVEL=INFO
```

### **Step 4: Deployment Process**

#### **Option 1: GitHub Integration (Recommended)**
1. Connect Render to your GitHub repository
2. Render automatically deploys on push
3. Zero-downtime deployments

#### **Option 2: Manual Deployment**
1. Create services manually on Render dashboard
2. Connect each service to your repo
3. Configure environment variables

### **Step 5: Post-Deployment**

#### **Verify Services**
1. **Backend**: https://sentinelrisk-api.onrender.com/health
2. **Frontend**: https://sentinelrisk-frontend.onrender.com
3. **Database**: Connected via Render's internal network

#### **Test Integration**
1. Test fraud detection API
2. Verify frontend-backend connection
3. Check model loading and predictions

## 🔧 **Render-Specific Optimizations**

### **Performance**
- **Free Plan**: 750 hours/month, 512MB RAM
- **Starter Plan**: $7/month, 1GB RAM, custom domains
- **Standard Plan**: $25/month, 2GB RAM, better performance

### **Security**
- **HTTPS**: Automatic SSL certificates
- **Environment Variables**: Secure secret management
- **Private Networking**: Database not exposed to internet

### **Scaling**
- **Auto-scaling**: Available on paid plans
- **Load Balancing**: Built-in load balancing
- **CDN**: Global content delivery

## 🎯 **Quick Deploy Commands**

### **Push to GitHub First**
```bash
# Try pushing to GitHub again
git add .
git commit -m "🚀 Ready for Render deployment"
git push origin main
```

### **Render Setup**
```bash
# After GitHub push:
# 1. Go to render.com
# 2. Connect GitHub repository
# 3. Create services using render.yaml
# 4. Deploy automatically
```

## 🌟 **Render Benefits**

### **Why Render is Perfect for SentinelRisk**
- **Easy Deployment**: One-click deployment from GitHub
- **Free Tier**: Perfect for development and testing
- **Managed Database**: PostgreSQL included
- **SSL Certificates**: Automatic HTTPS
- **Environment Variables**: Secure configuration
- **Zero-Downtime**: Seamless deployments

### **Production Ready**
- **Scalable**: Easy scaling as traffic grows
- **Reliable**: 99.9% uptime SLA
- **Secure**: Built-in security features
- **Monitoring**: Built-in metrics and logs

---

**🚀 Ready to deploy SentinelRisk to the cloud with Render?**

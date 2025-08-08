#!/bin/bash
# Deploy FastAPI to Google Cloud Run

set -e

# Configuration
PROJECT_ID="thermal-setup-458600-q8"
SERVICE_NAME="inventory-api"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Inventory API to Google Cloud Run..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not installed. Please install it first:"
    echo "   brew install google-cloud-sdk"
    exit 1
fi

# Set project
echo "📋 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🛠️ Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create secret for MongoDB URI (if not exists)
echo "🔐 Setting up secrets..."
if ! gcloud secrets describe MONGO_URI --quiet >/dev/null 2>&1; then
    echo "Creating MongoDB URI secret (MONGO_URI)..."
    echo "Please enter your MongoDB connection string:"
    read -s MONGODB_URI
    echo -n "$MONGODB_URI" | gcloud secrets create MONGO_URI --data-file=-
else
    echo "Secret MONGO_URI already exists."
fi

# Build and push image
echo "🏗️ Building container image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars ENVIRONMENT=production,MONGO_DB=inventory_demo \
    --set-secrets MONGO_URI=MONGO_URI:latest

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')

echo "✅ Deployment successful!"
printf "\n🌐 Your API is now live at:\n"
echo "   API URL: ${SERVICE_URL}"
echo "   Health Check: ${SERVICE_URL}/health"
echo "   Documentation: ${SERVICE_URL}/docs"
echo "   Tableau CSV: ${SERVICE_URL}/tableau/fact_daily.csv"
echo ""
echo "💡 Use the Tableau CSV URL in Tableau Public to create your dashboard!"

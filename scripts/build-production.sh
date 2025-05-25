#!/bin/bash

# Production Build Optimization Script
# This script builds the Angular app with optimizations for production deployment

set -e

echo "🚀 Starting production build optimization..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/
rm -rf www/

# Install dependencies if needed
echo "📦 Checking dependencies..."
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm ci --prefer-offline --no-audit
fi

# Build with production configuration
echo "🔨 Building with production optimizations..."
npm run build:prod

# Generate bundle analysis
echo "📊 Generating bundle analysis..."
npm run build:stats
npm run analyze

# Copy for Capacitor
echo "📱 Preparing for mobile deployment..."
npm run cap:copy

# Security scan (if available)
if command -v npm audit &> /dev/null; then
    echo "🔒 Running security audit..."
    npm audit --audit-level high
fi

# Performance analysis
echo "⚡ Analyzing bundle performance..."
BUILD_SIZE=$(du -sh dist/mobile | cut -f1)
echo "Total build size: $BUILD_SIZE"

# Check if gzip is available for compression analysis
if command -v gzip &> /dev/null; then
    echo "🗜️  Compression analysis:"
    find dist/mobile -name "*.js" -exec gzip -9 -c {} \; | wc -c | awk '{print "Compressed JS size: " $1/1024 " KB"}'
    find dist/mobile -name "*.css" -exec gzip -9 -c {} \; | wc -c | awk '{print "Compressed CSS size: " $1/1024 " KB"}'
fi

echo "✅ Production build optimization complete!"
echo "📂 Output directory: dist/mobile"
echo "📱 Capacitor ready: www/"

# Optional: Deploy to staging/production
if [ "$1" = "--deploy" ]; then
    echo "🚀 Deploying to production..."
    # Add your deployment commands here
    # Example: firebase deploy, aws s3 sync, etc.
fi

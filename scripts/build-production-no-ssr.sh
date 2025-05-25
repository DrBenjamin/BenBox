#!/bin/bash

# Production Build Script for BenBox Angular App
# Optimized for deployment without SSR

echo "🚀 Starting BenBox Production Build..."

# Set environment variables
export NODE_ENV=production
export NG_PRODUCTION=true

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/
rm -rf .angular/cache/

# Install dependencies if needed
echo "📦 Checking dependencies..."
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build with production configuration
echo "🔨 Building production bundle..."
npx ng build --configuration=production --aot --optimization=true

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
    
    # Show bundle sizes
    echo "📊 Bundle Analysis:"
    ls -lh dist/mobile/
    
    # Optional: Generate bundle analysis
    if command -v npx &> /dev/null; then
        echo "📈 Generating bundle analysis..."
        npx ng build --configuration=production --stats-json
        
        if [ -f "dist/mobile/stats.json" ]; then
            echo "📊 Bundle stats generated: dist/mobile/stats.json"
            echo "📊 To analyze bundle: npx webpack-bundle-analyzer dist/mobile/stats.json"
        fi
    fi
    
    # Copy service worker and manifest
    echo "📋 Copying PWA files..."
    cp public/sw.js dist/mobile/ 2>/dev/null || echo "⚠️  Service worker not found"
    cp public/manifest.json dist/mobile/ 2>/dev/null || echo "⚠️  Manifest not found"
    cp public/browserconfig.xml dist/mobile/ 2>/dev/null || echo "⚠️  Browser config not found"
    
    echo "🎉 Production build ready in dist/mobile/"
    echo "📱 Deploy the contents of dist/mobile/ to your web server"
    
else
    echo "❌ Build failed!"
    exit 1
fi

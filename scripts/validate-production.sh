#!/bin/bash

# BenBox Production Build Test & Validation Script
echo "🧪 BenBox Production Build Validation"
echo "====================================="

# Check if build exists
if [ ! -d "dist/mobile/browser" ]; then
    echo "❌ Production build not found. Run ./scripts/build-production-no-ssr.sh first"
    exit 1
fi

echo "✅ Production build found"

# Check essential files
echo ""
echo "📁 Checking essential files..."
required_files=(
    "dist/mobile/browser/index.html"
    "dist/mobile/browser/main-*.js"
    "dist/mobile/browser/polyfills-*.js"
    "dist/mobile/browser/manifest.json"
    "dist/mobile/browser/sw.js"
    "dist/mobile/browser/favicon.ico"
)

all_files_exist=true
for pattern in "${required_files[@]}"; do
    if ls $pattern 1> /dev/null 2>&1; then
        echo "  ✅ $(basename "$pattern")"
    else
        echo "  ❌ $(basename "$pattern") - MISSING"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    echo "❌ Some essential files are missing"
    exit 1
fi

# Bundle size analysis
echo ""
echo "📊 Bundle Size Analysis..."
main_size=$(ls -la dist/mobile/browser/main-*.js | awk '{print $5}')
polyfills_size=$(ls -la dist/mobile/browser/polyfills-*.js | awk '{print $5}')
total_size=$((main_size + polyfills_size))

echo "  📦 Main bundle: $(numfmt --to=iec-i --suffix=B $main_size)"
echo "  📦 Polyfills: $(numfmt --to=iec-i --suffix=B $polyfills_size)"
echo "  📦 Total JS: $(numfmt --to=iec-i --suffix=B $total_size)"

# Check if within budget (400KB = 409600 bytes)
if [ $total_size -le 409600 ]; then
    echo "  ✅ Bundle size within budget (< 400KB)"
else
    echo "  ⚠️  Bundle size exceeds budget (> 400KB)"
fi

# Test gzip compression
echo ""
echo "🗜️  Testing compression..."
if command -v gzip &> /dev/null; then
    main_gzipped=$(gzip -c dist/mobile/browser/main-*.js | wc -c)
    echo "  📦 Main bundle (gzipped): $(numfmt --to=iec-i --suffix=B $main_gzipped)"
    
    compression_ratio=$(( (main_size - main_gzipped) * 100 / main_size ))
    echo "  📈 Compression ratio: ${compression_ratio}%"
else
    echo "  ⚠️  gzip not available for compression testing"
fi

# Check PWA files
echo ""
echo "📱 PWA Configuration..."
if [ -f "dist/mobile/browser/manifest.json" ]; then
    echo "  ✅ Web App Manifest present"
    # Check manifest content
    if grep -q "BenBox" dist/mobile/browser/manifest.json; then
        echo "  ✅ Manifest properly configured"
    else
        echo "  ⚠️  Manifest may need configuration"
    fi
else
    echo "  ❌ Web App Manifest missing"
fi

if [ -f "dist/mobile/browser/sw.js" ]; then
    echo "  ✅ Service Worker present"
    # Check service worker content
    if grep -q "CACHE_NAME" dist/mobile/browser/sw.js; then
        echo "  ✅ Service Worker properly configured"
    else
        echo "  ⚠️  Service Worker may need configuration"
    fi
else
    echo "  ❌ Service Worker missing"
fi

# Security headers check
echo ""
echo "🔒 Security Configuration..."
if grep -q "Content-Security-Policy" dist/mobile/browser/index.html; then
    echo "  ✅ CSP headers configured"
else
    echo "  ⚠️  Consider adding CSP headers"
fi

# Test if server can be started
echo ""
echo "🌐 Testing local server..."
port=8081
if lsof -i :$port > /dev/null 2>&1; then
    echo "  ⚠️  Port $port is already in use"
else
    echo "  ✅ Port $port is available"
    echo "  💡 You can test with: cd dist/mobile/browser && python3 -m http.server $port"
fi

# Performance recommendations
echo ""
echo "⚡ Performance Recommendations..."
echo "  📊 Monitor Core Web Vitals with built-in dashboard"
echo "  🔄 Enable Service Worker for offline support"
echo "  📱 Test PWA installation on mobile devices"
echo "  📈 Use analytics to track user engagement"
echo "  🗜️  Enable server-side compression (gzip/brotli)"

# Deployment checklist
echo ""
echo "🚀 Deployment Checklist..."
echo "  ☐ Upload dist/mobile/browser/* to web server"
echo "  ☐ Configure server for SPA routing (fallback to index.html)"
echo "  ☐ Enable compression (gzip/brotli)"
echo "  ☐ Set up cache headers for static assets"
echo "  ☐ Configure HTTPS for Service Worker"
echo "  ☐ Update Analytics tracking ID in environment"
echo "  ☐ Test PWA installation"
echo "  ☐ Verify offline functionality"

echo ""
echo "🎉 Production build validation complete!"
echo "📖 See PRODUCTION_DEPLOYMENT_GUIDE.md for detailed deployment instructions"

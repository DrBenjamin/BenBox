// filepath: #file:mobile/src/environments/environment.prod.ts
export const environment = {
    production: true,
    apiUrl: '/api',
    
    // Performance monitoring settings
    monitoring: {
        enabled: true,
        sampleRate: 0.1, // Sample 10% of sessions for detailed monitoring
        maxEvents: 1000,
        flushInterval: 30000, // 30 seconds
        enableResourceTiming: true,
        enableUserTiming: true,
        enableNavigationTiming: true
    },
    
    // Analytics settings
    analytics: {
        enabled: true,
        trackingId: 'GA_MEASUREMENT_ID', // Replace with your GA4 measurement ID
        anonymizeIp: true,
        sampleRate: 100
    },
    
    // Cache settings
    cache: {
        enabled: true,
        maxAge: 24 * 60 * 60 * 1000, // 24 hours
        maxSize: 50 * 1024 * 1024 // 50MB
    },
    
    // Feature flags for production
    features: {
        enableServiceWorker: true,
        enableOfflineSupport: true,
        enablePrefetching: true,
        enableLazyLoading: true
    }
};

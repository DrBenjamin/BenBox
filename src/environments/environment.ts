// filepath: #file:mobile/src/environments/environment.ts
export const environment = {
    production: false,
    apiUrl: '/api',
    
    // Performance monitoring settings (more verbose in dev)
    monitoring: {
        enabled: true,
        sampleRate: 1.0, // Monitor all sessions in development
        maxEvents: 5000,
        flushInterval: 10000, // 10 seconds for faster feedback
        enableResourceTiming: true,
        enableUserTiming: true,
        enableNavigationTiming: true
    },
    
    // Analytics settings (disabled in dev)
    analytics: {
        enabled: false,
        trackingId: '',
        anonymizeIp: true,
        sampleRate: 0
    },
    
    // Cache settings (more aggressive refresh in dev)
    cache: {
        enabled: false,
        maxAge: 5 * 60 * 1000, // 5 minutes
        maxSize: 10 * 1024 * 1024 // 10MB
    },
    
    // Feature flags for development
    features: {
        enableServiceWorker: false,
        enableOfflineSupport: false,
        enablePrefetching: false,
        enableLazyLoading: true
    }
};

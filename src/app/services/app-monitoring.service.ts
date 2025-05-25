import { Injectable } from '@angular/core';
import { PerformanceMonitorService } from './performance-monitor.service';
import { AnalyticsService } from './analytics.service';

export interface MonitoringReport {
  timestamp: number;
  sessionId: string;
  performanceMetrics: any;
  analyticsEvents: any[];
  systemInfo: any;
}

@Injectable({
  providedIn: 'root'
})
export class AppMonitoringService {
  private monitoringStartTime: number;

  constructor(
    private performanceMonitor: PerformanceMonitorService,
    private analytics: AnalyticsService
  ) {
    this.monitoringStartTime = Date.now();
    this.initializeMonitoring();
  }

  private initializeMonitoring(): void {
    // Set up periodic performance monitoring
    this.setupPeriodicMonitoring();
    
    // Set up Core Web Vitals monitoring
    this.setupCoreWebVitalsMonitoring();
    
    // Monitor resource loading
    this.monitorResourceLoading();
  }

  private setupPeriodicMonitoring(): void {
    // Temporarily disabled to isolate TypeError issue
    // Only setup periodic monitoring in browser environment
    if (typeof window === 'undefined') {
      return;
    }
    
    // Log performance summary every 30 seconds - DISABLED FOR DEBUGGING
    /*
    setInterval(() => {
      try {
        this.logPeriodicSummary();
      } catch (error) {
        console.warn('Error in periodic monitoring:', error instanceof Error ? error.message : 'Unknown error');
      }
    }, 30000);
    */
  }

  private setupCoreWebVitalsMonitoring(): void {
    // Monitor LCP (Largest Contentful Paint) - only in browser
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        if (lastEntry && typeof lastEntry.startTime === 'number') {
          this.analytics.trackPerformanceMetric('largest_contentful_paint', lastEntry.startTime);
          console.log('🎯 LCP (Largest Contentful Paint):', `${lastEntry.startTime.toFixed(2)}ms`);
        }
      });
      
      try {
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      } catch (e) {
        console.warn('LCP monitoring not supported');
      }

      // Monitor FID (First Input Delay)
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (typeof entry.processingStart === 'number' && typeof entry.startTime === 'number') {
            const fid = entry.processingStart - entry.startTime;
            this.analytics.trackPerformanceMetric('first_input_delay', fid);
            console.log('⚡ FID (First Input Delay):', `${fid.toFixed(2)}ms`);
          }
        });
      });

      try {
        fidObserver.observe({ entryTypes: ['first-input'] });
      } catch (e) {
        console.warn('FID monitoring not supported');
      }

      // Monitor CLS (Cumulative Layout Shift)
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput && typeof entry.value === 'number') {
            clsValue += entry.value;
          }
        });
        this.analytics.trackPerformanceMetric('cumulative_layout_shift', clsValue);
        console.log('📐 CLS (Cumulative Layout Shift):', clsValue.toFixed(4));
      });

      try {
        clsObserver.observe({ entryTypes: ['layout-shift'] });
      } catch (e) {
        console.warn('CLS monitoring not supported');
      }
    }
  }

  private monitorResourceLoading(): void {
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      const resourceObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          // Track slow resources (> 1000ms)
          if (entry.duration > 1000) {
            this.analytics.trackEvent('slow_resource', {
              name: entry.name,
              duration: entry.duration,
              type: entry.initiatorType,
              size: entry.transferSize || 0
            });
          }
        });
      });

      try {
        resourceObserver.observe({ entryTypes: ['resource'] });
      } catch (e) {
        console.warn('Resource monitoring not supported');
      }
    }
  }

  private logPeriodicSummary(): void {
    try {
      const report = this.generateMonitoringReport();
      console.group('🔄 Periodic Monitoring Summary');
      console.log('⏱️ Session Duration:', `${((Date.now() - this.monitoringStartTime) / 1000).toFixed(1)}s`);
      console.log('📊 Performance Metrics Count:', report.performanceMetrics?.metricsCount || 0);
      console.log('📈 Analytics Events Count:', report.analyticsEvents?.length || 0);
      console.groupEnd();
    } catch (error) {
      console.warn('Error logging periodic summary:', error instanceof Error ? error.message : 'Unknown error');
    }
  }

  // Generate comprehensive monitoring report
  generateMonitoringReport(): MonitoringReport {
    try {
      const performanceMetrics = {
        navigationTiming: this.performanceMonitor.getNavigationTiming() || {},
        memoryUsage: this.performanceMonitor.getMemoryUsage() || {},
        firstContentfulPaint: this.performanceMonitor.getFirstContentfulPaint() || 0,
        largestContentfulPaint: this.performanceMonitor.getLargestContentfulPaint() || 0,
        allMetrics: this.performanceMonitor.getMetrics() || [],
        metricsCount: this.performanceMonitor.getMetrics()?.length || 0
      };

      const analyticsEvents = this.analytics.getEvents() || [];

      const systemInfo = {
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
        platform: typeof navigator !== 'undefined' ? navigator.platform : 'unknown',
        language: typeof navigator !== 'undefined' ? navigator.language : 'unknown',
        cookieEnabled: typeof navigator !== 'undefined' ? navigator.cookieEnabled : false,
        onLine: typeof navigator !== 'undefined' ? navigator.onLine : true,
        screenResolution: typeof screen !== 'undefined' ? `${screen.width}x${screen.height}` : 'unknown',
        colorDepth: typeof screen !== 'undefined' ? screen.colorDepth : 0,
        timeZone: typeof Intl !== 'undefined' ? Intl.DateTimeFormat().resolvedOptions().timeZone : 'unknown',
        sessionDuration: Date.now() - this.monitoringStartTime
      };

      return {
        timestamp: Date.now(),
        sessionId: analyticsEvents[0]?.sessionId || 'unknown',
        performanceMetrics,
        analyticsEvents,
        systemInfo
      };
    } catch (error) {
      console.warn('Error generating monitoring report:', error instanceof Error ? error.message : 'Unknown error');
      // Return a safe default report
      return {
        timestamp: Date.now(),
        sessionId: 'error',
        performanceMetrics: {
          navigationTiming: {},
          memoryUsage: {},
          firstContentfulPaint: 0,
          largestContentfulPaint: 0,
          allMetrics: [],
          metricsCount: 0
        },
        analyticsEvents: [],
        systemInfo: {
          userAgent: 'unknown',
          platform: 'unknown',
          language: 'unknown',
          cookieEnabled: false,
          onLine: true,
          screenResolution: 'unknown',
          colorDepth: 0,
          timeZone: 'unknown',
          sessionDuration: 0
        }
      };
    }
  }

  // Get performance score based on Core Web Vitals
  getPerformanceScore(): { score: number; details: any } {
    const fcp = this.performanceMonitor.getFirstContentfulPaint();
    const lcp = this.performanceMonitor.getLargestContentfulPaint();
    const memoryUsage = this.performanceMonitor.getMemoryUsage();
    
    let score = 100;
    const details: any = {};

    // Score FCP (good: <1.8s, needs improvement: 1.8s-3s, poor: >3s)
    if (fcp) {
      if (fcp > 3000) {
        score -= 30;
        details.fcp = 'poor';
      } else if (fcp > 1800) {
        score -= 15;
        details.fcp = 'needs-improvement';
      } else {
        details.fcp = 'good';
      }
    }

    // Score LCP (good: <2.5s, needs improvement: 2.5s-4s, poor: >4s)
    if (lcp) {
      if (lcp > 4000) {
        score -= 30;
        details.lcp = 'poor';
      } else if (lcp > 2500) {
        score -= 15;
        details.lcp = 'needs-improvement';
      } else {
        details.lcp = 'good';
      }
    }

    // Score memory usage
    if (memoryUsage) {
      const memoryUsagePercent = (memoryUsage.usedJSHeapSize / memoryUsage.jsHeapSizeLimit) * 100;
      if (memoryUsagePercent > 80) {
        score -= 20;
        details.memory = 'high-usage';
      } else if (memoryUsagePercent > 60) {
        score -= 10;
        details.memory = 'moderate-usage';
      } else {
        details.memory = 'good';
      }
    }

    return { score: Math.max(0, score), details };
  }

  // Export comprehensive monitoring data
  exportMonitoringData(): string {
    try {
      const report = this.generateMonitoringReport();
      const performanceScore = this.getPerformanceScore();
      
      const exportData = {
        ...report,
        performanceScore,
        exportTimestamp: new Date().toISOString()
      };

      return JSON.stringify(exportData, null, 2);
    } catch (error: any) {
      console.warn('Error exporting monitoring data:', error instanceof Error ? error.message : 'Unknown error');
      // Return a safe empty string instead of undefined
      return '{"error": "Failed to export data", "timestamp": "' + new Date().toISOString() + '"}';
    }
  }

  // Clear all monitoring data
  clearMonitoringData(): void {
    this.performanceMonitor.clearMetrics();
    this.analytics.clearEvents();
  }

  // Get monitoring summary for display
  getMonitoringSummary(): any {
    try {
      let performanceScore;
      let navigationTiming;
      let memoryUsage;
      let eventCounts;
      let events = [];
      
      try {
        performanceScore = this.getPerformanceScore() || { score: 0, details: {} };
      } catch (e) {
        console.warn('Error getting performance score for summary:', e);
        performanceScore = { score: 0, details: {} };
      }
      
      try {
        navigationTiming = this.performanceMonitor.getNavigationTiming() || {};
      } catch (e) {
        console.warn('Error getting navigation timing for summary:', e);
        navigationTiming = {};
      }
      
      try {
        memoryUsage = this.performanceMonitor.getMemoryUsage() || {};
      } catch (e) {
        console.warn('Error getting memory usage for summary:', e);
        memoryUsage = {};
      }
      
      try {
        events = this.analytics.getEvents() || [];
        eventCounts = this.getEventCounts() || {};
      } catch (e) {
        console.warn('Error getting events for summary:', e);
        events = [];
        eventCounts = {};
      }

      return {
        performanceScore: performanceScore.score,
        performanceDetails: performanceScore.details,
        loadTime: navigationTiming?.loadComplete || 0,
        memoryUsed: memoryUsage?.usedJSHeapSize || 0,
        totalEvents: events.length,
        eventBreakdown: eventCounts,
        sessionDuration: Date.now() - this.monitoringStartTime
      };
    } catch (error: any) {
      console.warn('Error generating monitoring summary:', error instanceof Error ? error.message : 'Unknown error');
      // Return a safe default object
      return {
        performanceScore: 0,
        performanceDetails: {},
        loadTime: 0,
        memoryUsed: 0,
        totalEvents: 0,
        eventBreakdown: {},
        sessionDuration: 0
      };
    }
  }

  private getEventCounts(): any {
    try {
      const events = this.analytics.getEvents() || [];
      const counts: any = {};
      
      events.forEach(event => {
        if (event && event.eventName) {
          counts[event.eventName] = (counts[event.eventName] || 0) + 1;
        }
      });

      return counts;
    } catch (error: any) {
      console.warn('Error counting events:', error instanceof Error ? error.message : 'Unknown error');
      return {};
    }
  }
}

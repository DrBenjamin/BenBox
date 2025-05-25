import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { environment } from '../../environments/environment';

export interface PerformanceMetric {
  name: string;
  value: number;
  type: string;
  timestamp: number;
}

@Injectable({
  providedIn: 'root'
})
export class PerformanceMonitorService {
  private metrics: PerformanceMetric[] = [];
  private observer: PerformanceObserver | null = null;
  private isBrowser: boolean;

  constructor(@Inject(PLATFORM_ID) private platformId: Object) {
    this.isBrowser = isPlatformBrowser(this.platformId);
    
    if (this.isBrowser && environment.monitoring.enabled) {
      this.initializePerformanceObserver();
      this.scheduleMetricsFlush();
    }
  }

  private initializePerformanceObserver(): void {
    if (this.isBrowser && typeof PerformanceObserver !== 'undefined' && environment.monitoring.enableUserTiming) {
      try {
        this.observer = new PerformanceObserver((list) => {
          try {
            const entries = list.getEntries();
            entries.forEach((entry) => {
              const metric: PerformanceMetric = {
                name: entry.name || 'unknown',
                value: entry.startTime || 0,
                type: entry.entryType || 'unknown',
                timestamp: Date.now()
              };
              this.addMetric(metric);
              
              // Safer console logging with proper error handling
              const entryType = entry.entryType || 'unknown';
              const entryName = entry.name || 'unknown';
              const startTime = entry.startTime || 0;
              
              // Only log if we have valid data
              if (entryType && entryName && typeof startTime === 'number') {
                console.log(`Performance Metric - ${entryType}: ${entryName} at ${startTime.toFixed(2)}ms`);
              }
            });
          } catch (error) {
            console.warn('Error processing performance entries:', error instanceof Error ? error.message : 'Unknown error');
          }
        });

        // Observe paint, navigation, and measure events
        this.observer.observe({ entryTypes: ['paint', 'navigation', 'measure', 'mark'] });
      } catch (error) {
        console.warn('Failed to initialize PerformanceObserver:', error instanceof Error ? error.message : 'Unknown error');
      }
    }
  }

  private addMetric(metric: PerformanceMetric): void {
    // Respect environment settings for maximum events
    if (this.metrics.length >= environment.monitoring.maxEvents) {
      // Remove oldest metrics to stay within limit
      this.metrics = this.metrics.slice(-environment.monitoring.maxEvents + 100);
    }
    
    // Sample metrics based on sample rate in production
    if (environment.production && Math.random() > environment.monitoring.sampleRate) {
      return; // Skip this metric
    }
    
    this.metrics.push(metric);
  }

  // Flush metrics periodically in production
  private scheduleMetricsFlush(): void {
    if (environment.production && environment.monitoring.flushInterval > 0) {
      setInterval(() => {
        this.flushMetrics();
      }, environment.monitoring.flushInterval);
    }
  }

  private flushMetrics(): void {
    if (this.metrics.length > 0) {
      // In a real app, send metrics to analytics service
      console.log(`Flushing ${this.metrics.length} performance metrics`);
      
      // Keep only recent metrics
      const recentMetrics = this.metrics.slice(-100);
      this.metrics = recentMetrics;
    }
  }

  // Mark a custom performance point
  markPerformance(name: string): void {
    if (this.isBrowser && typeof performance !== 'undefined' && performance.mark) {
      performance.mark(name);
    }
  }

  // Measure time between two marks
  measurePerformance(name: string, startMark: string, endMark: string): void {
    if (this.isBrowser && typeof performance !== 'undefined' && performance.measure) {
      performance.measure(name, startMark, endMark);
    }
  }

  // Get navigation timing metrics
  getNavigationTiming(): any {
    if (typeof performance !== 'undefined' && performance.timing) {
      const timing = performance.timing;
      return {
        domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
        loadComplete: timing.loadEventEnd - timing.navigationStart,
        domInteractive: timing.domInteractive - timing.navigationStart,
        firstByte: timing.responseStart - timing.navigationStart
      };
    }
    return null;
  }

  // Get memory usage (if available)
  getMemoryUsage(): any {
    if (typeof performance !== 'undefined' && (performance as any).memory) {
      const memory = (performance as any).memory;
      return {
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit
      };
    }
    return null;
  }

  // Get all collected metrics
  getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  // Clear metrics
  clearMetrics(): void {
    this.metrics = [];
  }

  // Get FCP (First Contentful Paint) specifically
  getFirstContentfulPaint(): number | null {
    const fcpEntry = this.metrics.find(metric => 
      metric.type === 'paint' && metric.name === 'first-contentful-paint'
    );
    return fcpEntry ? fcpEntry.value : null;
  }

  // Get LCP (Largest Contentful Paint) if available
  getLargestContentfulPaint(): number | null {
    const lcpEntry = this.metrics.find(metric => 
      metric.type === 'largest-contentful-paint'
    );
    return lcpEntry ? lcpEntry.value : null;
  }

  // Log performance summary
  logPerformanceSummary(): void {
    const navigationTiming = this.getNavigationTiming();
    const memoryUsage = this.getMemoryUsage();
    const fcp = this.getFirstContentfulPaint();

    console.group('🚀 Performance Summary');
    
    if (navigationTiming) {
      console.log('📊 Navigation Timing:', navigationTiming);
    }
    
    if (memoryUsage) {
      console.log('💾 Memory Usage:', memoryUsage);
    }
    
    if (fcp) {
      console.log('🎨 First Contentful Paint:', `${fcp.toFixed(2)}ms`);
    }
    
    console.log('📋 All Metrics:', this.getMetrics());
    console.groupEnd();
  }

  // Cleanup observer
  destroy(): void {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
}

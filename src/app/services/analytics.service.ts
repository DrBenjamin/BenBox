import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

export interface AnalyticsEvent {
  eventName: string;
  data: any;
  timestamp: number;
  sessionId: string;
}

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private events: AnalyticsEvent[] = [];
  private sessionId: string;

  constructor() {
    this.sessionId = this.generateSessionId();
    if (environment.analytics.enabled) {
      this.trackPageLoad();
    }
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Track custom events
  trackEvent(eventName: string, data: any = {}): void {
    if (!environment.analytics.enabled) {
      return; // Skip tracking if analytics disabled
    }
    
    try {
      // Validate eventName is not undefined
      if (!eventName || typeof eventName !== 'string') {
        console.warn('Invalid event name provided to trackEvent:', eventName);
        return;
      }

      const event: AnalyticsEvent = {
        eventName,
        data: {
          ...data,
          userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
          url: typeof window !== 'undefined' ? window.location.href : 'unknown',
          timestamp: new Date().toISOString()
        },
        timestamp: Date.now(),
        sessionId: this.sessionId
      };

      this.events.push(event);
      
      // Safer console logging
      if (eventName && typeof eventName === 'string') {
        console.log(`📊 Analytics Event: ${eventName}`, event);
      }
      
      // In a real application, you would send this to an analytics server
      this.sendToAnalyticsServer(event);
    } catch (error) {
      console.warn('Error tracking event:', error instanceof Error ? error.message : 'Unknown error');
    }
  }

  // Track button clicks
  trackButtonClick(buttonName: string, additionalData: any = {}): void {
    this.trackEvent('button_click', {
      buttonName,
      ...additionalData
    });
  }

  // Track page load
  trackPageLoad(): void {
    // Check if we're in a browser environment
    if (typeof document !== 'undefined') {
      this.trackEvent('page_load', {
        referrer: document.referrer,
        title: document.title
      });
    }
  }

  // Track iframe load
  trackIframeLoad(url: string, query: number): void {
    this.trackEvent('iframe_load', {
      url,
      query,
      loadTime: Date.now()
    });
  }

  // Track user interaction duration
  trackInteractionStart(interactionType: string): string {
    const interactionId = `interaction_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
    this.trackEvent('interaction_start', {
      interactionType,
      interactionId
    });
    return interactionId;
  }

  trackInteractionEnd(interactionId: string, interactionType: string): void {
    this.trackEvent('interaction_end', {
      interactionType,
      interactionId
    });
  }

  // Track errors
  trackError(error: Error, context: string = 'unknown'): void {
    this.trackEvent('error', {
      message: error.message || 'Unknown error',
      stack: error.stack || 'No stack trace available',
      context,
      name: error.name || 'Error'
    });
  }

  // Track performance metrics
  trackPerformanceMetric(metricName: string, value: number, unit: string = 'ms'): void {
    this.trackEvent('performance_metric', {
      metricName,
      value,
      unit
    });
  }

  // Get all events
  getEvents(): AnalyticsEvent[] {
    return [...this.events];
  }

  // Get events by type
  getEventsByType(eventName: string): AnalyticsEvent[] {
    return this.events.filter(event => event.eventName === eventName);
  }

  // Clear events
  clearEvents(): void {
    this.events = [];
  }

  // Export analytics data
  exportAnalyticsData(): string {
    return JSON.stringify({
      sessionId: this.sessionId,
      events: this.events,
      exportTimestamp: Date.now()
    }, null, 2);
  }

  // Private method to simulate sending data to analytics server
  private sendToAnalyticsServer(event: AnalyticsEvent): void {
    // In a real application, you would send this data to your analytics backend
    // For now, we'll just store it locally or log it
    
    // Example: You could use fetch to send to your backend
    /*
    fetch('/api/analytics', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(event)
    }).catch(error => {
      console.error('Failed to send analytics event:', error);
    });
    */
  }

  // Initialize error tracking
  initializeErrorTracking(): void {
    // Only initialize in browser environment
    if (typeof window !== 'undefined') {
      window.addEventListener('error', (event) => {
        const errorMessage = event.message || 'Unknown error occurred';
        this.trackError(new Error(errorMessage), 'global_error_handler');
      });

      window.addEventListener('unhandledrejection', (event) => {
        const reason = event.reason || 'Unknown rejection reason';
        const errorMessage = typeof reason === 'string' ? reason : 'Promise rejection occurred';
        this.trackError(new Error(errorMessage), 'unhandled_promise_rejection');
      });
    }
  }

  // Track user engagement metrics
  trackUserEngagement(): void {
    // Only track in browser environment
    if (typeof window !== 'undefined' && typeof document !== 'undefined') {
      let startTime = Date.now();
      let isActive = true;

      // Track time on page
      const trackTimeOnPage = () => {
        if (isActive) {
          const timeSpent = Date.now() - startTime;
          this.trackEvent('time_on_page', { timeSpent });
        }
      };

      // Track when user becomes inactive
      const handleVisibilityChange = () => {
        if (document.hidden) {
          isActive = false;
          trackTimeOnPage();
        } else {
          isActive = true;
          startTime = Date.now();
        }
      };

      // Track before page unload
      window.addEventListener('beforeunload', trackTimeOnPage);
      document.addEventListener('visibilitychange', handleVisibilityChange);
    }
  }
}

import { Component, OnInit } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { AnalyticsService } from './services/analytics.service';
import { PerformanceMonitorService } from './services/performance-monitor.service';
import { AppMonitoringService } from './services/app-monitoring.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'BenBox';
  urlSafe: SafeResourceUrl | null = null;
  // Plain URL string for iframe src interpolation to avoid Angular resource URL sanitization errors
  urlStr: string | null = null;
  buttonsVisible = true;
  baseUrl = 'http://212.227.102.172:8501/?embed=true&angular=true';

  // Mobile and responsive properties
  isLoading = false;
  isMobile = false;
  screenWidth = 0;
  
  // VNC interaction properties
  isVncInteractive = true;
  vncBaseUrl = 'http://212.227.102.172:6080/vnc.html';
  
  // Touch interaction properties
  touchStartX = 0;
  touchStartY = 0;

  constructor(
    private sanitizer: DomSanitizer,
    private analytics: AnalyticsService,
    private performanceMonitor: PerformanceMonitorService,
    private appMonitoring: AppMonitoringService
  ) {
    console.log('BenBox app starting...');
    
    // Track app initialization
    this.analytics.trackEvent('app_initialized', {
      component: 'AppComponent',
      timestamp: new Date().toISOString()
    });
    
    // Mark performance start point
    this.performanceMonitor.markPerformance('app-start');
  }

  ngOnInit(): void {
    // Mark app ready and measure initialization time
    this.performanceMonitor.markPerformance('app-ready');
    this.performanceMonitor.measurePerformance('app-init-time', 'app-start', 'app-ready');
    
    // Initialize mobile detection and responsive features
    this.initializeMobileFeatures();

    
    // Initialize comprehensive monitoring summary after app is ready
    setTimeout(() => {
      this.performanceMonitor.logPerformanceSummary();
      
      // Log comprehensive monitoring status
      console.group('🔍 AppMonitoringService Status');
      console.log('✅ AppMonitoringService initialized and running');
      console.log('📊 Core Web Vitals monitoring active');
      console.log('🔄 Resource loading monitoring active');
      console.log('📱 Mobile device:', this.isMobile ? 'Yes' : 'No');
      console.log('📏 Screen width:', this.screenWidth + 'px');
      console.groupEnd();
    }, 1000);
  }

  private initializeMobileFeatures(): void {
    // Detect mobile device
    this.isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    // Get screen dimensions
    this.screenWidth = window.innerWidth;
    
    // Add window resize listener
    window.addEventListener('resize', () => {
      this.screenWidth = window.innerWidth;
      this.onWindowResize();
    });
    
    // Add orientation change listener for mobile
    window.addEventListener('orientationchange', () => {
      setTimeout(() => {
        this.screenWidth = window.innerWidth;
        this.onOrientationChange();
      }, 100); // Small delay to allow browser to adjust
    });
    
    // Track mobile metrics
    this.analytics.trackEvent('device_info', {
      isMobile: this.isMobile,
      screenWidth: this.screenWidth,
      userAgent: navigator.userAgent,
      viewport: `${window.innerWidth}x${window.innerHeight}`,
      devicePixelRatio: window.devicePixelRatio || 1
    });
    
    console.log('📱 Mobile features initialized:', {
      isMobile: this.isMobile,
      screenWidth: this.screenWidth,
      orientation: screen.orientation?.angle || 'unknown'
    });
  }

  private onWindowResize(): void {
    // Handle window resize events
    this.analytics.trackEvent('window_resize', {
      newWidth: this.screenWidth,
      timestamp: Date.now()
    });
    
    // Adjust layout if needed based on screen size
    if (this.screenWidth < 768 && !this.isMobile) {
      console.log('📱 Switching to mobile layout due to small screen');
    }
  }
  
  private onOrientationChange(): void {
    // Handle orientation changes on mobile devices
    const orientation = screen.orientation?.angle || 0;
    
    this.analytics.trackEvent('orientation_change', {
      angle: orientation,
      screenWidth: this.screenWidth,
      timestamp: Date.now()
    });
    
    console.log('🔄 Orientation changed:', orientation + '°');
    
    // Force layout recalculation after orientation change
    setTimeout(() => {
      this.performanceMonitor.markPerformance('orientation-change-complete');
    }, 200);
  }

  loadQuery(query: number): void {
    console.log('🚀 loadQuery called with query:', query);
    console.log('📊 Current state before loadQuery:');
    console.log('  - buttonsVisible:', this.buttonsVisible);
    console.log('  - urlSafe:', this.urlSafe);
    console.log('  - baseUrl:', this.baseUrl);
    
    // Show loading state for better mobile UX
    this.isLoading = true;
    
    // Mark performance point for query loading
    this.performanceMonitor.markPerformance(`query-${query}-start`);
    
    // Track button click with mobile context
    this.analytics.trackButtonClick(`Query ${query}`, {
      queryNumber: query,
      feature: 'iframe_load',
      isMobile: this.isMobile,
      screenWidth: this.screenWidth
    });
    
    // Mobile-specific loading timeout
    const loadingTimeout = this.isMobile ? 2000 : 1500;
    
    setTimeout(() => {
      this.isLoading = false;
      console.log('⏰ Loading timeout finished, isLoading set to false');
    }, loadingTimeout);
    
    const url = `${this.baseUrl}&query=${query}`;
    console.log('🔗 Generated URL:', url);
    
    // Store plain URL for direct src binding
    try {
      this.urlSafe = this.sanitizer.bypassSecurityTrustResourceUrl(url);
      console.log('✅ URL sanitization successful');
      console.log('🔒 urlSafe created:', this.urlSafe);
    } catch (error) {
      console.error('❌ URL sanitization failed:', error);
      // Continue with urlStr for binding
    }
    
    this.buttonsVisible = false;
    console.log('👁️ Set buttonsVisible to false, iframe section should now be visible');
    
    // Force change detection
    setTimeout(() => {
      console.log('🔄 Checking state after 100ms:');
      console.log('  - buttonsVisible:', this.buttonsVisible);
      console.log('  - urlSafe exists:', !!this.urlSafe);
      console.log('  - urlSafe value:', this.urlSafe);
    }, 100);
    
    // Track iframe load
    this.analytics.trackIframeLoad(url, query);
    
    // Measure query load time after a brief delay
    setTimeout(() => {
      this.performanceMonitor.markPerformance(`query-${query}-end`);
      this.performanceMonitor.measurePerformance(
        `query-${query}-load-time`, 
        `query-${query}-start`, 
        `query-${query}-end`
      );
    }, 500);
  }

  // Loading BenBox desktop application
  loadBenBox(): void {
    console.log('🚀 Starting BenBox Desktop app...');
    this.isLoading = true;
    
    this.performanceMonitor.markPerformance('benbox-start');
    
    // Track button click with mobile context
    this.analytics.trackButtonClick('BenBox Desktop', {
      feature: 'benbox_desktop',
      isMobile: this.isMobile,
      screenWidth: this.screenWidth
    });
    
    // Mobile-specific loading timeout
    const loadingTimeout = this.isMobile ? 2000 : 1500;
    
    setTimeout(() => {
      this.isLoading = false;
      console.log('⏰ Loading timeout finished, isLoading set to false');
    }, loadingTimeout);

    // Testing VNC connection first for mobile devices
    if (this.isMobile) {
      console.log('📱 Mobile device detected, testing VNC connection...');
      this.testVncConnection();
    }

    const viewOnlyParam = this.isVncInteractive ? '0' : '1';
    const mobileOptimizations = this.optimizeVncForMobile();
    const url = `${this.vncBaseUrl}?view_only=${viewOnlyParam}&autoconnect=1&reconnect=1&reconnect_delay=2000${mobileOptimizations}`;
    console.log('🔗 Loading BenBox VNC URL with mouse interaction:', this.isVncInteractive ? 'enabled' : 'disabled', url);
    
    // Store sanitized URL for iframe
    try {
      this.urlSafe = this.sanitizer.bypassSecurityTrustResourceUrl(url);
      console.log('✅ URL sanitization successful for BenBox VNC');
      console.log('🔒 urlSafe created:', this.urlSafe);
    } catch (error) {
      console.error('❌ URL sanitization failed for BenBox VNC:', error);
    }
    
    this.buttonsVisible = false;
    console.log('👁️ Set buttonsVisible to false, BenBox VNC iframe should now be visible');
    
    // Force change detection
    setTimeout(() => {
      console.log('🔄 Checking state after 100ms:');
      console.log('  - buttonsVisible:', this.buttonsVisible);
      console.log('  - urlSafe exists:', !!this.urlSafe);
      console.log('  - urlSafe value:', this.urlSafe);
    }, 100);
    
    // Track iframe load
    this.analytics.trackIframeLoad(url, -1); // Using -1 for BenBox desktop app
    
    // Measure BenBox load time after a brief delay
    setTimeout(() => {
      this.performanceMonitor.markPerformance('benbox-end');
      this.performanceMonitor.measurePerformance(
        'benbox-load-time', 
        'benbox-start', 
        'benbox-end'
      );
    }, 500);
  }

  // Mobile-specific VNC optimization
  optimizeVncForMobile(): string {
    if (this.isMobile) {
      console.log('📱 Applying mobile optimizations for VNC');
      // On mobile, enable touch events and gestures
      const mobileParams = '&show_dot=1&view_clip=0&resize=remote&quality=6&compression=2';
      return mobileParams;
    }
    return '';
  }

  // Adding VNC connection test method
  testVncConnection(): void {
    console.log('🔍 Testing VNC server connection...');
    const testUrl = 'http://212.227.102.172:6080';
    
    fetch(testUrl)
      .then(response => {
        console.log('🔗 VNC server test response:', response.status, response.statusText);
        if (response.ok) {
          console.log('✅ VNC server is reachable!');
        } else {
          console.warn('⚠️ VNC server returned non-OK status:', response.status);
        }
      })
      .catch(error => {
        console.error('❌ VNC server connection failed:', error);
        console.log('💡 This might be expected due to CORS, but indicates connection issues');
      });
  }

  // Adding VNC troubleshooting method
  troubleshootVnc(): void {
    console.log('🔍 Running VNC troubleshooting...');
    
    // Check if we're on the correct network
    console.log('🌐 Current location:', window.location.href);
    console.log('📱 Mobile device:', this.isMobile);
    console.log('📏 Screen dimensions:', this.screenWidth + 'x' + window.innerHeight);
    
    // Test basic connectivity
    const vncUrl = 'http://212.227.102.172:6080';
    console.log('🔗 Testing VNC endpoint:', vncUrl);
    
    // Try to fetch the VNC page
    fetch(vncUrl + '/vnc.html')
      .then(response => {
        if (response.ok) {
          console.log('✅ VNC HTML page is accessible');
          return response.text();
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      })
      .then(html => {
        if (html.includes('noVNC')) {
          console.log('✅ noVNC application is properly served');
        } else {
          console.warn('⚠️ VNC page loaded but may not contain noVNC application');
        }
      })
      .catch(error => {
        console.error('❌ VNC troubleshooting failed:', error);
        console.log('💡 Possible issues:');
        console.log('   - VNC server is not running');
        console.log('   - Network connectivity issues');
        console.log('   - CORS policy blocking the request');
        console.log('   - Server IP address may have changed');
      });
  }

  // Toggle VNC interaction mode
  toggleVncInteraction(): void {
    this.isVncInteractive = !this.isVncInteractive;
    console.log('🖱️ VNC interaction toggled:', this.isVncInteractive ? 'enabled' : 'disabled');
    
    // Reload the VNC iframe with new interaction setting
    if (this.urlSafe) {
      const viewOnlyParam = this.isVncInteractive ? '0' : '1';
      const mobileOptimizations = this.optimizeVncForMobile();
      const newUrl = `${this.vncBaseUrl}?view_only=${viewOnlyParam}&autoconnect=1&reconnect=1&reconnect_delay=2000${mobileOptimizations}`;
      
      try {
        this.urlSafe = this.sanitizer.bypassSecurityTrustResourceUrl(newUrl);
        console.log('✅ VNC URL updated for interaction mode:', newUrl);
        
        // Track the interaction toggle
        this.analytics.trackEvent('vnc_interaction_toggled', {
          interactive: this.isVncInteractive,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        console.error('❌ Failed to update VNC URL for interaction toggle:', error);
      }
    }
  }

  // Navigation methods
  showMenu(): void {
    console.log('Returning to main menu...');
    this.buttonsVisible = true;
    this.urlSafe = null;
    this.isLoading = false;
    
    // Track navigation
    this.analytics.trackEvent('back_to_menu', {
      timestamp: new Date().toISOString(),
      source: 'iframe_controls'
    });
  }
  
  reloadIframe(): void {
    console.log('Reloading iframe...');
    if (this.urlSafe) {
      // Force iframe reload by temporarily clearing and resetting the URL
      const currentUrl = this.urlSafe;
      this.urlSafe = null;
      this.isLoading = true;
      
      setTimeout(() => {
        this.urlSafe = currentUrl;
        this.isLoading = false;
      }, 100);
      
      // Track reload
      this.analytics.trackEvent('iframe_reload', {
        timestamp: new Date().toISOString(),
        url: currentUrl.toString()
      });
    }
  }

  // Iframe event handlers for debugging
  onIframeLoad(): void {
    console.log('✅ Iframe loaded successfully');
    this.analytics.trackEvent('iframe_loaded', {
      timestamp: new Date().toISOString(),
      url: this.urlSafe?.toString() || 'unknown'
    });
  }
  
  onIframeError(event: any): void {
    console.error('❌ Iframe failed to load:', event);
    this.analytics.trackEvent('iframe_error', {
      timestamp: new Date().toISOString(),
      error: event.toString(),
      url: this.urlSafe?.toString() || 'unknown'
    });
    
    // Show user-friendly error message
    alert('Failed to load content. Please check your connection and try again.');
  }
  
  testConnection(): void {
    console.log('Testing Streamlit connection...');
    console.log('Base URL:', this.baseUrl);
    
    // Test the connection
    fetch(this.baseUrl.replace('/?embed=true&angular=true', ''))
      .then(response => {
        console.log('Connection test response:', response.status, response.statusText);
        if (response.ok) {
          alert('✅ Streamlit server is reachable!');
        } else {
          alert(`❌ Server responded with status: ${response.status}`);
        }
      })
      .catch(error => {
        console.error('Connection test failed:', error);
        alert('❌ Cannot reach Streamlit server: ' + error.message);
      });
  }

  // Performance methods with PerformanceMonitorService integration
  showPerformanceSummary(): void {
    console.log('Performance Summary - Enhanced version');
    this.analytics.trackButtonClick('Performance Summary', { feature: 'performance' });
    
    // Get performance data
    const navigationTiming = this.performanceMonitor.getNavigationTiming();
    const memoryUsage = this.performanceMonitor.getMemoryUsage();
    const fcp = this.performanceMonitor.getFirstContentfulPaint();
    
    let summary = 'Performance Summary:\n\n';
    
    if (navigationTiming) {
      summary += `⚡ Load Time: ${navigationTiming.loadComplete}ms\n`;
      summary += `📊 DOM Ready: ${navigationTiming.domContentLoaded}ms\n`;
      summary += `🌐 First Byte: ${navigationTiming.firstByte}ms\n\n`;
    }
    
    if (memoryUsage) {
      summary += `💾 Memory Used: ${(memoryUsage.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB\n`;
      summary += `📊 Total Heap: ${(memoryUsage.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB\n\n`;
    }
    
    if (fcp) {
      summary += `🎨 First Paint: ${fcp.toFixed(2)}ms\n\n`;
    }
    
    summary += 'Check console for detailed metrics!';
    alert(summary);
    
    // Log detailed summary to console
    this.performanceMonitor.logPerformanceSummary();
  }

  getPerformanceScore(): void {
    console.log('Performance Score - Enhanced version');
    this.analytics.trackButtonClick('Performance Score', { feature: 'performance' });
    
    // Calculate a simple performance score based on available metrics
    let score = 100;
    
    const navigationTiming = this.performanceMonitor.getNavigationTiming();
    const memoryUsage = this.performanceMonitor.getMemoryUsage();
    const fcp = this.performanceMonitor.getFirstContentfulPaint();
    
    if (navigationTiming) {
      // Deduct points for slow load times
      if (navigationTiming.loadComplete > 3000) score -= 20;
      else if (navigationTiming.loadComplete > 1500) score -= 10;
      
      if (navigationTiming.domContentLoaded > 2000) score -= 15;
      else if (navigationTiming.domContentLoaded > 1000) score -= 5;
    }
    
    if (fcp) {
      // Deduct points for slow first contentful paint
      if (fcp > 3000) score -= 20;
      else if (fcp > 1800) score -= 10;
    }
    
    if (memoryUsage) {
      // Deduct points for high memory usage (>50MB)
      const memoryMB = memoryUsage.usedJSHeapSize / 1024 / 1024;
      if (memoryMB > 100) score -= 15;
      else if (memoryMB > 50) score -= 5;
    }
    
    score = Math.max(0, score); // Ensure score doesn't go below 0
    
    let rating = 'Excellent';
    if (score < 80) rating = 'Good';
    if (score < 60) rating = 'Needs Improvement';
    if (score < 40) rating = 'Poor';
    
    alert(`Performance Score: ${score}/100 (${rating})\n\nCheck console for detailed analysis!`);
  }

  generateDemoData(): void {
    console.log('Generate Demo Data - Simple version');
    this.analytics.trackButtonClick('Generate Demo Data', { feature: 'demo' });
    alert('Demo data generated successfully!');
  }

  simulateUserSession(): void {
    console.log('Simulate User Session - Simple version');
    this.analytics.trackButtonClick('Simulate User Session', { feature: 'simulation' });
    alert('User session simulation started!');
  }

  clearDemoData(): void {
    console.log('Clear Demo Data - Simple version');
    this.analytics.trackButtonClick('Clear Demo Data', { feature: 'demo' });
    alert('Demo data cleared successfully!');
  }

  // New method to show analytics data
  showAnalyticsData(): void {
    console.log('Show Analytics Data');
    this.analytics.trackButtonClick('Show Analytics Data', { feature: 'analytics' });
    
    const events = this.analytics.getEvents();
    const eventSummary = events.map(event => 
      `${event.eventName} - ${new Date(event.timestamp).toLocaleTimeString()}`
    ).join('\n');
    
    alert(`Analytics Events (${events.length} total):\n\n${eventSummary}`);
  }

  // New method to show comprehensive monitoring summary
  showMonitoringSummary(): void {
    console.log('Show Monitoring Summary');
    this.analytics.trackButtonClick('Show Monitoring Summary', { feature: 'monitoring' });
    
    const summary = this.appMonitoring.getMonitoringSummary();
    
    console.group('📊 Comprehensive Monitoring Summary');
    console.log('🎯 Performance Score:', `${summary.performanceScore}/100`);
    console.log('⚡ Load Time:', `${summary.loadTime.toFixed(2)}ms`);
    console.log('💾 Memory Used:', `${(summary.memoryUsed / 1024 / 1024).toFixed(2)}MB`);
    console.log('📈 Total Events:', summary.totalEvents);
    console.log('⏱️ Session Duration:', `${(summary.sessionDuration / 1000).toFixed(1)}s`);
    console.log('📋 Event Breakdown:', summary.eventBreakdown);
    console.groupEnd();
    
    const summaryText = `Performance Score: ${summary.performanceScore}/100
Load Time: ${summary.loadTime.toFixed(2)}ms
Memory Used: ${(summary.memoryUsed / 1024 / 1024).toFixed(2)}MB
Total Events: ${summary.totalEvents}
Session Duration: ${(summary.sessionDuration / 1000).toFixed(1)}s

Check console for detailed breakdown!`;
    
    alert(summaryText);
  }

  // New method to export monitoring data
  exportMonitoringData(): void {
    console.log('Export Monitoring Data');
    this.analytics.trackButtonClick('Export Monitoring Data', { feature: 'export' });
    
    const data = this.appMonitoring.exportMonitoringData();
    
    // Create and download file
    const blob = new Blob([data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `benbox-monitoring-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    alert('Monitoring data exported successfully!');
  }

  // New method to generate detailed monitoring report
  generateMonitoringReport(): void {
    console.log('Generate Monitoring Report');
    this.analytics.trackButtonClick('Generate Monitoring Report', { feature: 'report' });
    
    const report = this.appMonitoring.generateMonitoringReport();
    
    console.group('📋 Detailed Monitoring Report');
    console.log('🕐 Timestamp:', new Date(report.timestamp).toLocaleString());
    console.log('🔐 Session ID:', report.sessionId);
    console.log('⚡ Performance Metrics:', report.performanceMetrics);
    console.log('📊 Analytics Events:', report.analyticsEvents);
    console.log('💻 System Info:', report.systemInfo);
    console.groupEnd();
    
    alert(`Monitoring Report Generated!\n\nSession: ${report.sessionId}\nTimestamp: ${new Date(report.timestamp).toLocaleString()}\n\nCheck console for full details!`);
  }

  // New method to clear all monitoring data
  clearMonitoringData(): void {
    console.log('Clear Monitoring Data');
    this.analytics.trackButtonClick('Clear Monitoring Data', { feature: 'clear' });
    
    this.appMonitoring.clearMonitoringData();
    alert('All monitoring data cleared successfully!');
  }
}

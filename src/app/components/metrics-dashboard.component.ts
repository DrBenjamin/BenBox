import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppMonitoringService } from '../services/app-monitoring.service';
import { PerformanceMonitorService } from '../services/performance-monitor.service';
import { AnalyticsService } from '../services/analytics.service';

@Component({
  selector: 'app-metrics-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="metrics-dashboard" *ngIf="isVisible">
      <div class="dashboard-header">
        <h3>📊 BenBox Metrics Dashboard</h3>
        <button (click)="toggleDashboard()" class="close-btn">✖</button>
      </div>
      
      <div class="metrics-grid">
        <!-- Performance Score -->
        <div class="metric-card">
          <h4>🏆 Performance Score</h4>
          <div class="score" [ngClass]="getScoreClass(performanceScore)">
            {{ performanceScore }}/100
          </div>
          <small>{{ getScoreDescription(performanceScore) }}</small>
        </div>

        <!-- Load Time -->
        <div class="metric-card">
          <h4>⚡ Load Time</h4>
          <div class="metric-value">{{ loadTime }}ms</div>
          <small>Time to fully load</small>
        </div>

        <!-- Memory Usage -->
        <div class="metric-card">
          <h4>💾 Memory Usage</h4>
          <div class="metric-value">{{ formatBytes(memoryUsed) }}</div>
          <small>JavaScript heap size</small>
        </div>

        <!-- Session Duration -->
        <div class="metric-card">
          <h4>⏱️ Session Duration</h4>
          <div class="metric-value">{{ formatDuration(sessionDuration) }}</div>
          <small>Time on page</small>
        </div>

        <!-- Total Events -->
        <div class="metric-card">
          <h4>📈 Total Events</h4>
          <div class="metric-value">{{ totalEvents }}</div>
          <small>User interactions tracked</small>
        </div>

        <!-- Most Used Feature -->
        <div class="metric-card">
          <h4>🎯 Top Feature</h4>
          <div class="metric-value">{{ topFeature }}</div>
          <small>Most clicked button</small>
        </div>
      </div>

      <!-- Core Web Vitals -->
      <div class="web-vitals-section">
        <h4>🌐 Core Web Vitals</h4>
        <div class="vitals-grid">
          <div class="vital-metric">
            <span class="vital-label">FCP</span>
            <span class="vital-value" [ngClass]="getVitalClass('fcp', fcp)">
              {{ fcp ? (fcp + 'ms') : 'N/A' }}
            </span>
          </div>
          <div class="vital-metric">
            <span class="vital-label">LCP</span>
            <span class="vital-value" [ngClass]="getVitalClass('lcp', lcp)">
              {{ lcp ? (lcp + 'ms') : 'N/A' }}
            </span>
          </div>
          <div class="vital-metric">
            <span class="vital-label">CLS</span>
            <span class="vital-value">
              {{ cls !== null && cls !== undefined ? cls.toFixed(3) : 'N/A' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Recent Events -->
      <div class="recent-events-section">
        <h4>📋 Recent Events</h4>
        <div class="events-list">
          <div *ngFor="let event of recentEvents" class="event-item">
            <span class="event-name">{{ event.eventName }}</span>
            <span class="event-time">{{ formatEventTime(event.timestamp) }}</span>
          </div>
        </div>
      </div>

      <!-- Dashboard Actions -->
      <div class="dashboard-actions">
        <button (click)="refreshMetrics()" class="action-btn refresh">🔄 Refresh</button>
        <button (click)="exportData()" class="action-btn export">📁 Export</button>
        <button (click)="clearData()" class="action-btn clear">🗑️ Clear</button>
      </div>
    </div>

    <!-- Dashboard Toggle Button -->
    <button *ngIf="!isVisible" (click)="toggleDashboard()" class="dashboard-toggle">
      📊 Metrics
    </button>
  `,
  styles: [`
    .metrics-dashboard {
      position: fixed;
      top: 20px;
      right: 20px;
      width: 400px;
      max-height: 80vh;
      background: white;
      border: 1px solid #ddd;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 1000;
      overflow-y: auto;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
    }

    .dashboard-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 15px;
      border-bottom: 1px solid #eee;
      background: #f8f9fa;
    }

    .dashboard-header h3 {
      margin: 0;
      font-size: 16px;
      color: #333;
    }

    .close-btn {
      background: none;
      border: none;
      font-size: 14px;
      cursor: pointer;
      color: #666;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      padding: 15px;
    }

    .metric-card {
      background: #f8f9fa;
      padding: 12px;
      border-radius: 6px;
      text-align: center;
    }

    .metric-card h4 {
      margin: 0 0 8px 0;
      font-size: 12px;
      color: #666;
    }

    .metric-value, .score {
      font-size: 18px;
      font-weight: bold;
      color: #333;
      margin-bottom: 4px;
    }

    .score.good { color: #28a745; }
    .score.moderate { color: #ffc107; }
    .score.poor { color: #dc3545; }

    .metric-card small {
      font-size: 10px;
      color: #888;
    }

    .web-vitals-section {
      padding: 15px;
      border-top: 1px solid #eee;
    }

    .web-vitals-section h4 {
      margin: 0 0 10px 0;
      font-size: 14px;
      color: #333;
    }

    .vitals-grid {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 10px;
    }

    .vital-metric {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 8px;
      background: #f8f9fa;
      border-radius: 4px;
    }

    .vital-label {
      font-size: 11px;
      color: #666;
      margin-bottom: 4px;
    }

    .vital-value {
      font-size: 14px;
      font-weight: bold;
    }

    .vital-value.good { color: #28a745; }
    .vital-value.needs-improvement { color: #ffc107; }
    .vital-value.poor { color: #dc3545; }

    .recent-events-section {
      padding: 15px;
      border-top: 1px solid #eee;
    }

    .recent-events-section h4 {
      margin: 0 0 10px 0;
      font-size: 14px;
      color: #333;
    }

    .events-list {
      max-height: 120px;
      overflow-y: auto;
    }

    .event-item {
      display: flex;
      justify-content: space-between;
      padding: 6px 0;
      border-bottom: 1px solid #f0f0f0;
      font-size: 12px;
    }

    .event-name {
      color: #333;
      font-weight: 500;
    }

    .event-time {
      color: #888;
    }

    .dashboard-actions {
      padding: 15px;
      border-top: 1px solid #eee;
      display: flex;
      gap: 8px;
    }

    .action-btn {
      flex: 1;
      padding: 8px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 500;
    }

    .action-btn.refresh {
      background: #28a745;
      color: white;
    }

    .action-btn.export {
      background: #17a2b8;
      color: white;
    }

    .action-btn.clear {
      background: #dc3545;
      color: white;
    }

    .dashboard-toggle {
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 10px 15px;
      background: #007bff;
      color: white;
      border: none;
      border-radius: 20px;
      cursor: pointer;
      font-size: 12px;
      z-index: 1000;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }

    .dashboard-toggle:hover {
      background: #0056b3;
    }
  `]
})
export class MetricsDashboardComponent implements OnInit, OnDestroy {
  isVisible = false;
  performanceScore = 0;
  loadTime = 0;
  memoryUsed = 0;
  sessionDuration = 0;
  totalEvents = 0;
  topFeature = 'None';
  fcp: number | null = null;
  lcp: number | null = null;
  cls: number | null = null;
  recentEvents: any[] = [];

  private refreshInterval: any;

  constructor(
    private appMonitoring: AppMonitoringService,
    private performanceMonitor: PerformanceMonitorService,
    private analytics: AnalyticsService
  ) {}

  ngOnInit(): void {
    this.refreshMetrics();
    // Auto-refresh every 5 seconds
    this.refreshInterval = setInterval(() => {
      if (this.isVisible) {
        this.refreshMetrics();
      }
    }, 5000);
  }

  ngOnDestroy(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  toggleDashboard(): void {
    this.isVisible = !this.isVisible;
    if (this.isVisible) {
      this.refreshMetrics();
    }
  }

  refreshMetrics(): void {
    try {
      // Use safe defaults in case methods return undefined
      let summary;
      let scoreData;
      
      try {
        summary = this.appMonitoring.getMonitoringSummary() || {};
      } catch (e) {
        summary = {};
        console.warn('Error getting monitoring summary:', e);
      }
      
      try {
        scoreData = this.appMonitoring.getPerformanceScore() || { score: 0, details: {} };
      } catch (e) {
        scoreData = { score: 0, details: {} };
        console.warn('Error getting performance score:', e);
      }
      
      this.performanceScore = scoreData?.score || 0;
      this.loadTime = summary?.loadTime || 0;
      this.memoryUsed = summary?.memoryUsed || 0;
      this.sessionDuration = summary?.sessionDuration || 0;
      this.totalEvents = summary?.totalEvents || 0;
      
      // Get top feature
      const eventBreakdown = summary?.eventBreakdown || {};
      if (eventBreakdown?.button_click) {
        this.topFeature = 'Button Clicks';
      } else if (eventBreakdown?.iframe_load) {
        this.topFeature = 'Iframe Loads';
      } else {
        this.topFeature = 'Page Views';
      }

      // Get Core Web Vitals with defensive coding
      try {
        this.fcp = this.performanceMonitor.getFirstContentfulPaint() || 0;
      } catch (e) {
        this.fcp = 0;
        console.warn('Error getting FCP:', e);
      }
      
      try {
        this.lcp = this.performanceMonitor.getLargestContentfulPaint() || 0;
      } catch (e) {
        this.lcp = 0;
        console.warn('Error getting LCP:', e);
      }
      
      this.cls = 0; // CLS would be tracked by the monitoring service - set to 0 for now

      // Get recent events with defensive coding
      try {
        const allEvents = this.analytics.getEvents() || [];
        this.recentEvents = allEvents.slice(-5).reverse();
      } catch (e) {
        this.recentEvents = [];
        console.warn('Error getting analytics events:', e);
      }
    } catch (error: any) {
      console.warn('Error refreshing metrics:', error instanceof Error ? error.message : 'Unknown error');
      // Set safe default values
      this.performanceScore = 0;
      this.loadTime = 0;
      this.memoryUsed = 0;
      this.sessionDuration = 0;
      this.totalEvents = 0;
      this.topFeature = 'N/A';
      this.fcp = 0;
      this.lcp = 0;
      this.recentEvents = [];
    }
  }

  exportData(): void {
    try {
      const data = this.appMonitoring.exportMonitoringData();
      if (data === undefined || data === null || data === '') {
        console.warn('No monitoring data available for export');
        return;
      }
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `benbox-metrics-${Date.now()}.json`;
      if (typeof document !== 'undefined') {
        a.click();
      }
      URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('Error exporting data:', error instanceof Error ? error.message : 'Unknown error');
    }
  }

  clearData(): void {
    try {
      this.appMonitoring.clearMonitoringData();
      this.refreshMetrics();
    } catch (error) {
      console.error('Error clearing data:', error);
    }
  }

  getScoreClass(score: number | null | undefined): string {
    if (score === null || score === undefined || isNaN(score) || score < 0) return 'poor';
    if (score >= 80) return 'good';
    if (score >= 60) return 'moderate';
    return 'poor';
  }

  getScoreDescription(score: number | null | undefined): string {
    if (score === null || score === undefined || isNaN(score) || score < 0) return 'No data available';
    if (score >= 80) return 'Excellent performance';
    if (score >= 60) return 'Good performance';
    if (score >= 40) return 'Needs improvement';
    return 'Poor performance';
  }

  getVitalClass(vital: string, value: number | null): string {
    if (value === null || value === undefined || isNaN(value)) return '';
    
    if (vital === 'fcp') {
      if (value <= 1800) return 'good';
      if (value <= 3000) return 'needs-improvement';
      return 'poor';
    }
    
    if (vital === 'lcp') {
      if (value <= 2500) return 'good';
      if (value <= 4000) return 'needs-improvement';
      return 'poor';
    }
    
    return '';
  }

  formatBytes(bytes: number | null | undefined): string {
    if (bytes === null || bytes === undefined || isNaN(bytes) || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatDuration(ms: number | null | undefined): string {
    if (ms === null || ms === undefined || isNaN(ms) || ms === 0) return '0s';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  formatEventTime(timestamp: number | null | undefined): string {
    if (timestamp === null || timestamp === undefined || isNaN(timestamp)) return 'Unknown';
    const now = Date.now();
    const diff = now - timestamp;
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
  }
}

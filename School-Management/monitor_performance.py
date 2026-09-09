
#!/usr/bin/env python3
"""
System Performance Monitor
"""

import time
import psutil
import requests
from datetime import datetime
import json

class PerformanceMonitor:
    def __init__(self, base_url="http://0.0.0.0:5000"):
        self.base_url = base_url
        self.metrics = []
        
    def get_system_metrics(self):
        """Get system resource metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'available_memory': psutil.virtual_memory().available / (1024**3),  # GB
            'process_count': len(psutil.pids())
        }
    
    def test_response_times(self):
        """Test response times for different endpoints"""
        endpoints = [
            '/',
            '/dashboard',
            '/students',
            '/teachers',
            '/classes',
            '/attendance',
            '/fees',
            '/sms_management',
            '/reports',
            '/settings'
        ]
        
        response_times = {}
        session = requests.Session()
        
        # Login first
        try:
            login_data = {'username': 'admin', 'password': 'admin123'}
            session.post(f"{self.base_url}/login", data=login_data)
        except:
            pass
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = session.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                response_times[endpoint] = {
                    'response_time': round((end_time - start_time) * 1000, 2),  # ms
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                }
            except Exception as e:
                response_times[endpoint] = {
                    'response_time': None,
                    'status_code': None,
                    'success': False,
                    'error': str(e)
                }
        
        return response_times
    
    def check_database_performance(self):
        """Check database performance"""
        from replit import db as repldb
        
        start_time = time.time()
        
        # Count all records
        total_records = 0
        collections = ['student', 'teacher', 'class', 'attendance', 'fee', 'sms_log']
        
        for collection in collections:
            try:
                count = len(list(repldb.prefix(f"{collection}:")))
                total_records += count
            except:
                pass
        
        db_time = (time.time() - start_time) * 1000  # ms
        
        return {
            'total_records': total_records,
            'query_time_ms': round(db_time, 2),
            'records_per_second': round(total_records / (db_time/1000), 2) if db_time > 0 else 0
        }
    
    def run_performance_test(self, duration_minutes=5):
        """Run comprehensive performance test"""
        print("🚀 Starting Performance Monitoring...")
        print(f"Duration: {duration_minutes} minutes")
        print("=" * 60)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            # Collect metrics
            system_metrics = self.get_system_metrics()
            response_times = self.test_response_times()
            db_performance = self.check_database_performance()
            
            # Combine metrics
            combined_metrics = {
                'system': system_metrics,
                'response_times': response_times,
                'database': db_performance
            }
            
            self.metrics.append(combined_metrics)
            
            # Display current metrics
            print(f"⏱️  {datetime.now().strftime('%H:%M:%S')} | "
                  f"CPU: {system_metrics['cpu_percent']:.1f}% | "
                  f"Memory: {system_metrics['memory_percent']:.1f}% | "
                  f"Dashboard: {response_times.get('/dashboard', {}).get('response_time', 'N/A')}ms")
            
            time.sleep(30)  # Check every 30 seconds
        
        self.analyze_performance()
    
    def analyze_performance(self):
        """Analyze collected performance data"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE ANALYSIS REPORT")
        print("=" * 60)
        
        if not self.metrics:
            print("No metrics collected")
            return
        
        # System metrics analysis
        cpu_values = [m['system']['cpu_percent'] for m in self.metrics]
        memory_values = [m['system']['memory_percent'] for m in self.metrics]
        
        print(f"🖥️  System Performance:")
        print(f"  CPU Usage - Avg: {sum(cpu_values)/len(cpu_values):.1f}% | Max: {max(cpu_values):.1f}% | Min: {min(cpu_values):.1f}%")
        print(f"  Memory Usage - Avg: {sum(memory_values)/len(memory_values):.1f}% | Max: {max(memory_values):.1f}% | Min: {min(memory_values):.1f}%")
        
        # Response time analysis
        print(f"\n🌐 Response Time Analysis:")
        endpoints = ['/dashboard', '/students', '/teachers', '/classes', '/fees']
        
        for endpoint in endpoints:
            response_times = [m['response_times'].get(endpoint, {}).get('response_time') 
                            for m in self.metrics if m['response_times'].get(endpoint, {}).get('response_time')]
            
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                min_time = min(response_times)
                print(f"  {endpoint}: Avg: {avg_time:.0f}ms | Max: {max_time:.0f}ms | Min: {min_time:.0f}ms")
        
        # Database performance
        db_times = [m['database']['query_time_ms'] for m in self.metrics if m['database']['query_time_ms']]
        if db_times:
            avg_db_time = sum(db_times) / len(db_times)
            print(f"\n💾 Database Performance:")
            print(f"  Avg Query Time: {avg_db_time:.1f}ms")
            print(f"  Total Records: {self.metrics[-1]['database']['total_records']}")
        
        # Performance recommendations
        print(f"\n💡 Performance Recommendations:")
        
        avg_cpu = sum(cpu_values) / len(cpu_values)
        if avg_cpu > 80:
            print("  🔴 High CPU usage detected - Consider optimizing database queries")
        elif avg_cpu > 60:
            print("  🟡 Moderate CPU usage - Monitor for performance bottlenecks")
        else:
            print("  ✅ CPU usage is normal")
        
        avg_memory = sum(memory_values) / len(memory_values)
        if avg_memory > 85:
            print("  🔴 High memory usage - Consider implementing data caching")
        elif avg_memory > 70:
            print("  🟡 Moderate memory usage - Monitor memory consumption")
        else:
            print("  ✅ Memory usage is normal")
        
        # Save detailed report
        report_filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump({
                'metrics': self.metrics,
                'analysis': {
                    'cpu': {'avg': sum(cpu_values)/len(cpu_values), 'max': max(cpu_values), 'min': min(cpu_values)},
                    'memory': {'avg': sum(memory_values)/len(memory_values), 'max': max(memory_values), 'min': min(memory_values)}
                },
                'generated_at': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📋 Detailed performance report saved: {report_filename}")
        print("=" * 60)

if __name__ == "__main__":
    import sys
    
    duration = 2  # Default 2 minutes
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except:
            pass
    
    monitor = PerformanceMonitor()
    monitor.run_performance_test(duration)

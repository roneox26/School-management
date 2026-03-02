
#!/usr/bin/env python3
"""
Comprehensive Test Runner
Runs all system tests, database validation, and performance monitoring
"""

import subprocess
import sys
import time
import os
from datetime import datetime

class TestRunner:
    def __init__(self):
        self.results = {}
        
    def run_script(self, script_name, description):
        """Run a test script and capture results"""
        print(f"\n🚀 Starting: {description}")
        print("=" * 60)
        
        try:
            start_time = time.time()
            
            # Run the script
            result = subprocess.run([sys.executable, script_name], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=300)  # 5 minute timeout
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Store results
            self.results[script_name] = {
                'description': description,
                'success': result.returncode == 0,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
            # Display results
            if result.returncode == 0:
                print(f"✅ {description} completed successfully in {duration:.1f}s")
                if result.stdout:
                    print("Output:")
                    print(result.stdout)
            else:
                print(f"❌ {description} failed after {duration:.1f}s")
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print("Error output:")
                    print(result.stderr)
                    
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} timed out after 5 minutes")
            self.results[script_name] = {
                'description': description,
                'success': False,
                'duration': 300,
                'error': 'Timeout after 5 minutes'
            }
        except Exception as e:
            print(f"💥 Error running {description}: {str(e)}")
            self.results[script_name] = {
                'description': description,
                'success': False,
                'duration': 0,
                'error': str(e)
            }
    
    def check_flask_app(self):
        """Check if Flask app is running"""
        import requests
        try:
            response = requests.get("http://0.0.0.0:5000/", timeout=5)
            return True
        except:
            return False
    
    def wait_for_flask_app(self, max_wait=30):
        """Wait for Flask app to be ready"""
        print("🔄 Checking if Flask app is running...")
        
        for i in range(max_wait):
            if self.check_flask_app():
                print("✅ Flask app is ready!")
                return True
            print(f"⏳ Waiting for Flask app... ({i+1}/{max_wait})")
            time.sleep(1)
        
        print("❌ Flask app is not responding")
        return False
    
    def run_all_tests(self):
        """Run all available tests"""
        print("🎯 School Management System - Comprehensive Testing Suite")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Check if Flask app is running
        if not self.wait_for_flask_app():
            print("⚠️  Flask app is not running. Some tests may fail.")
            print("💡 Make sure to run 'python main.py' in another terminal")
            
            response = input("\nDo you want to continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("Exiting...")
                return
        
        # Test suite configuration
        tests = [
            {
                'script': 'validate_database.py',
                'description': 'Database Validation & Integrity Check',
                'critical': True
            },
            {
                'script': 'test_system.py',
                'description': 'System Feature Testing',
                'critical': True
            },
            {
                'script': 'monitor_performance.py',
                'description': 'Performance Monitoring (2 min)',
                'critical': False
            }
        ]
        
        # Run tests
        for test in tests:
            try:
                self.run_script(test['script'], test['description'])
                
                # Short break between tests
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("\n⏹️  Testing interrupted by user")
                break
        
        # Generate summary report
        self.generate_summary()
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results.values() if r['success']])
        failed_tests = total_tests - successful_tests
        
        print(f"📈 Overall Results:")
        print(f"  Total Test Suites: {total_tests}")
        print(f"  ✅ Successful: {successful_tests}")
        print(f"  ❌ Failed: {failed_tests}")
        print(f"  📊 Success Rate: {(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "  📊 Success Rate: N/A")
        
        total_duration = sum(r.get('duration', 0) for r in self.results.values())
        print(f"  ⏱️  Total Duration: {total_duration:.1f} seconds")
        
        print(f"\n📝 Test Suite Details:")
        for script, result in self.results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            duration = result.get('duration', 0)
            print(f"  {status} | {result['description']} | {duration:.1f}s")
            
            if not result['success'] and 'error' in result:
                print(f"    └─ Error: {result['error']}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if failed_tests == 0:
            print("  🎉 All tests passed! Your system is working correctly.")
            print("  🔄 Consider running these tests regularly to monitor system health.")
        else:
            print("  🔧 Some tests failed. Please review the detailed output above.")
            print("  📋 Check log files generated by individual test scripts for more details.")
            if not self.check_flask_app():
                print("  🚨 Make sure the Flask application is running before running tests.")
        
        print(f"\n📅 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Save summary report
        import json
        summary_report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': (successful_tests/total_tests)*100 if total_tests > 0 else 0,
            'total_duration': total_duration,
            'results': self.results
        }
        
        report_filename = f"comprehensive_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(summary_report, f, indent=2)
        
        print(f"📋 Comprehensive summary saved: {report_filename}")

if __name__ == "__main__":
    print("🔧 Installing required packages...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'psutil', 'requests'], 
                      capture_output=True, check=True)
        print("✅ Packages installed successfully")
    except:
        print("⚠️  Could not install packages. Some tests may not work.")
    
    runner = TestRunner()
    runner.run_all_tests()

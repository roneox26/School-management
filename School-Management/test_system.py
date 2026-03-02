
#!/usr/bin/env python3
"""
School Management System - Comprehensive Testing Module
This module tests all features of the system
"""

import json
import requests
from datetime import datetime, date
import time

class SchoolSystemTester:
    def __init__(self, base_url="http://0.0.0.0:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, status, message=""):
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {message}")
        
    def login_admin(self):
        """Test admin login functionality"""
        try:
            # Get login page
            response = self.session.get(f"{self.base_url}/login")
            if response.status_code != 200:
                self.log_test("Login Page Access", "FAIL", f"Status: {response.status_code}")
                return False
                
            # Login with default credentials
            login_data = {
                'username': 'admin',
                'password': 'admin123'
            }
            response = self.session.post(f"{self.base_url}/login", data=login_data)
            
            if response.status_code == 200 and 'dashboard' in response.url:
                self.log_test("Admin Login", "PASS", "Successfully logged in")
                return True
            else:
                self.log_test("Admin Login", "FAIL", f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_dashboard(self):
        """Test dashboard functionality"""
        try:
            response = self.session.get(f"{self.base_url}/dashboard")
            if response.status_code == 200:
                if 'Dashboard' in response.text:
                    self.log_test("Dashboard Access", "PASS", "Dashboard loaded successfully")
                else:
                    self.log_test("Dashboard Access", "FAIL", "Dashboard content missing")
            else:
                self.log_test("Dashboard Access", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard Access", "FAIL", f"Exception: {str(e)}")
    
    def test_student_management(self):
        """Test student management features"""
        try:
            # Test students list page
            response = self.session.get(f"{self.base_url}/students")
            if response.status_code == 200:
                self.log_test("Students List", "PASS", "Students page accessible")
            else:
                self.log_test("Students List", "FAIL", f"Status: {response.status_code}")
                
            # Test add student page
            response = self.session.get(f"{self.base_url}/add_student")
            if response.status_code == 200:
                self.log_test("Add Student Page", "PASS", "Add student page accessible")
            else:
                self.log_test("Add Student Page", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Student Management", "FAIL", f"Exception: {str(e)}")
    
    def test_teacher_management(self):
        """Test teacher management features"""
        try:
            # Test teachers list page
            response = self.session.get(f"{self.base_url}/teachers")
            if response.status_code == 200:
                self.log_test("Teachers List", "PASS", "Teachers page accessible")
            else:
                self.log_test("Teachers List", "FAIL", f"Status: {response.status_code}")
                
            # Test add teacher page
            response = self.session.get(f"{self.base_url}/add_teacher")
            if response.status_code == 200:
                self.log_test("Add Teacher Page", "PASS", "Add teacher page accessible")
            else:
                self.log_test("Add Teacher Page", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Teacher Management", "FAIL", f"Exception: {str(e)}")
    
    def test_class_management(self):
        """Test class management features"""
        try:
            # Test classes list page
            response = self.session.get(f"{self.base_url}/classes")
            if response.status_code == 200:
                self.log_test("Classes List", "PASS", "Classes page accessible")
            else:
                self.log_test("Classes List", "FAIL", f"Status: {response.status_code}")
                
            # Test add class page
            response = self.session.get(f"{self.base_url}/add_class")
            if response.status_code == 200:
                self.log_test("Add Class Page", "PASS", "Add class page accessible")
            else:
                self.log_test("Add Class Page", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Class Management", "FAIL", f"Exception: {str(e)}")
    
    def test_attendance_system(self):
        """Test attendance management"""
        try:
            # Test student attendance page
            response = self.session.get(f"{self.base_url}/attendance")
            if response.status_code == 200:
                self.log_test("Student Attendance", "PASS", "Student attendance page accessible")
            else:
                self.log_test("Student Attendance", "FAIL", f"Status: {response.status_code}")
                
            # Test teacher attendance page
            response = self.session.get(f"{self.base_url}/teacher_attendance")
            if response.status_code == 200:
                self.log_test("Teacher Attendance", "PASS", "Teacher attendance page accessible")
            else:
                self.log_test("Teacher Attendance", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Attendance System", "FAIL", f"Exception: {str(e)}")
    
    def test_fee_management(self):
        """Test fee management features"""
        try:
            # Test fees list page
            response = self.session.get(f"{self.base_url}/fees")
            if response.status_code == 200:
                self.log_test("Fees List", "PASS", "Fees page accessible")
            else:
                self.log_test("Fees List", "FAIL", f"Status: {response.status_code}")
                
            # Test add fee page
            response = self.session.get(f"{self.base_url}/add_fee")
            if response.status_code == 200:
                self.log_test("Add Fee Page", "PASS", "Add fee page accessible")
            else:
                self.log_test("Add Fee Page", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Fee Management", "FAIL", f"Exception: {str(e)}")
    
    def test_exam_system(self):
        """Test exam management"""
        try:
            # Test exams list page
            response = self.session.get(f"{self.base_url}/exams")
            if response.status_code == 200:
                self.log_test("Exams List", "PASS", "Exams page accessible")
            else:
                self.log_test("Exams List", "FAIL", f"Status: {response.status_code}")
                
            # Test add exam page
            response = self.session.get(f"{self.base_url}/add_exam")
            if response.status_code == 200:
                self.log_test("Add Exam Page", "PASS", "Add exam page accessible")
            else:
                self.log_test("Add Exam Page", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Exam System", "FAIL", f"Exception: {str(e)}")
    
    def test_sms_system(self):
        """Test SMS management features"""
        try:
            # Test SMS management page
            response = self.session.get(f"{self.base_url}/sms_management")
            if response.status_code == 200:
                self.log_test("SMS Management", "PASS", "SMS management page accessible")
            else:
                self.log_test("SMS Management", "FAIL", f"Status: {response.status_code}")
                
            # Test add SMS template page
            response = self.session.get(f"{self.base_url}/add_sms_template")
            if response.status_code == 200:
                self.log_test("Add SMS Template", "PASS", "Add SMS template page accessible")
            else:
                self.log_test("Add SMS Template", "FAIL", f"Status: {response.status_code}")
                
            # Test SMS configuration validation
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/validate_sms_config", headers=headers)
            if response.status_code == 200:
                self.log_test("SMS Config Validation", "PASS", "SMS validation endpoint working")
            else:
                self.log_test("SMS Config Validation", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("SMS System", "FAIL", f"Exception: {str(e)}")
    
    def test_reports_system(self):
        """Test reports functionality"""
        try:
            # Test main reports page
            response = self.session.get(f"{self.base_url}/reports")
            if response.status_code == 200:
                self.log_test("Reports Page", "PASS", "Reports page accessible")
            else:
                self.log_test("Reports Page", "FAIL", f"Status: {response.status_code}")
                
            # Test individual report pages
            report_pages = ['fee_report', 'sms_report', 'attendance_report', 'results_report']
            for report in report_pages:
                try:
                    response = self.session.get(f"{self.base_url}/{report}")
                    if response.status_code == 200:
                        self.log_test(f"{report.title()}", "PASS", f"{report} accessible")
                    else:
                        self.log_test(f"{report.title()}", "FAIL", f"Status: {response.status_code}")
                except:
                    self.log_test(f"{report.title()}", "FAIL", "Report not accessible")
                
        except Exception as e:
            self.log_test("Reports System", "FAIL", f"Exception: {str(e)}")
    
    def test_settings(self):
        """Test settings functionality"""
        try:
            response = self.session.get(f"{self.base_url}/settings")
            if response.status_code == 200:
                self.log_test("Settings Page", "PASS", "Settings page accessible")
            else:
                self.log_test("Settings Page", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Settings", "FAIL", f"Exception: {str(e)}")
    
    def test_data_export(self):
        """Test data export functionality"""
        try:
            # Test students CSV export
            response = self.session.get(f"{self.base_url}/export_data/students/csv")
            if response.status_code == 200 or response.status_code == 302:
                self.log_test("Students CSV Export", "PASS", "Students CSV export working")
            else:
                self.log_test("Students CSV Export", "FAIL", f"Status: {response.status_code}")
                
            # Test students PDF export
            response = self.session.get(f"{self.base_url}/export_data/students/pdf")
            if response.status_code == 200 or response.status_code == 302:
                self.log_test("Students PDF Export", "PASS", "Students PDF export working")
            else:
                self.log_test("Students PDF Export", "FAIL", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Data Export", "FAIL", f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all system tests"""
        print("🚀 Starting School Management System Comprehensive Testing...")
        print("=" * 60)
        
        # Login first
        if not self.login_admin():
            print("❌ Cannot proceed with tests - Login failed")
            return
            
        # Run all tests
        test_methods = [
            self.test_dashboard,
            self.test_student_management,
            self.test_teacher_management,
            self.test_class_management,
            self.test_attendance_system,
            self.test_fee_management,
            self.test_exam_system,
            self.test_sms_system,
            self.test_reports_system,
            self.test_settings,
            self.test_data_export
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_test(f"Test Method {test_method.__name__}", "FAIL", f"Exception: {str(e)}")
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate test summary report"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 60)
        
        passed = len([t for t in self.test_results if t['status'] == 'PASS'])
        failed = len([t for t in self.test_results if t['status'] == 'FAIL'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.test_results:
                if test['status'] == 'FAIL':
                    print(f"  - {test['test']}: {test['message']}")
        
        # Save detailed report
        report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump({
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'success_rate': (passed/total)*100
                },
                'tests': self.test_results,
                'generated_at': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📋 Detailed report saved: {report_filename}")
        print("=" * 60)

if __name__ == "__main__":
    print("🎯 School Management System - Feature Testing")
    print("Make sure the Flask app is running on port 5000")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    tester = SchoolSystemTester()
    tester.run_all_tests()

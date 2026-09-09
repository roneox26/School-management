
#!/usr/bin/env python3
"""
Database Validation and Integrity Checker
"""

import json
from datetime import datetime
from replit import db as repldb

class DatabaseValidator:
    def __init__(self):
        self.issues = []
        self.stats = {}
    
    def log_issue(self, category, message, severity="WARNING"):
        issue = {
            'category': category,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        self.issues.append(issue)
        
        severity_icon = "🔴" if severity == "ERROR" else "🟡" if severity == "WARNING" else "🔵"
        print(f"{severity_icon} [{category}] {message}")
    
    def validate_admin_users(self):
        """Validate admin users"""
        print("🔍 Validating Admin Users...")
        admins = []
        
        for key in repldb.prefix("admin:"):
            try:
                admin = repldb[key]
                admins.append(admin)
                
                # Check required fields
                if not admin.get('username'):
                    self.log_issue("Admin", f"Admin {admin.get('id')} missing username", "ERROR")
                if not admin.get('password_hash'):
                    self.log_issue("Admin", f"Admin {admin.get('id')} missing password hash", "ERROR")
                    
            except Exception as e:
                self.log_issue("Admin", f"Error reading admin data: {str(e)}", "ERROR")
        
        self.stats['admins'] = len(admins)
        print(f"✅ Found {len(admins)} admin users")
    
    def validate_students(self):
        """Validate student records"""
        print("🔍 Validating Students...")
        students = []
        roll_numbers = set()
        
        for key in repldb.prefix("student:"):
            try:
                student = repldb[key]
                students.append(student)
                
                # Check required fields
                required_fields = ['name', 'roll_number', 'class_id', 'guardian_phone']
                for field in required_fields:
                    if not student.get(field):
                        self.log_issue("Student", f"Student {student.get('name', 'Unknown')} missing {field}", "ERROR")
                
                # Check duplicate roll numbers
                roll_num = student.get('roll_number')
                if roll_num:
                    if roll_num in roll_numbers:
                        self.log_issue("Student", f"Duplicate roll number: {roll_num}", "ERROR")
                    roll_numbers.add(roll_num)
                
                # Validate phone numbers
                phone = student.get('guardian_phone', '')
                if phone and (len(phone) < 10 or not phone.replace('+', '').replace('-', '').isdigit()):
                    self.log_issue("Student", f"Invalid guardian phone for {student.get('name')}: {phone}", "WARNING")
                
            except Exception as e:
                self.log_issue("Student", f"Error reading student data: {str(e)}", "ERROR")
        
        self.stats['students'] = len(students)
        self.stats['active_students'] = len([s for s in students if s.get('is_active', True)])
        print(f"✅ Found {len(students)} students ({self.stats['active_students']} active)")
    
    def validate_teachers(self):
        """Validate teacher records"""
        print("🔍 Validating Teachers...")
        teachers = []
        employee_ids = set()
        
        for key in repldb.prefix("teacher:"):
            try:
                teacher = repldb[key]
                teachers.append(teacher)
                
                # Check required fields
                required_fields = ['name', 'employee_id', 'phone']
                for field in required_fields:
                    if not teacher.get(field):
                        self.log_issue("Teacher", f"Teacher {teacher.get('name', 'Unknown')} missing {field}", "ERROR")
                
                # Check duplicate employee IDs
                emp_id = teacher.get('employee_id')
                if emp_id:
                    if emp_id in employee_ids:
                        self.log_issue("Teacher", f"Duplicate employee ID: {emp_id}", "ERROR")
                    employee_ids.add(emp_id)
                
            except Exception as e:
                self.log_issue("Teacher", f"Error reading teacher data: {str(e)}", "ERROR")
        
        self.stats['teachers'] = len(teachers)
        self.stats['active_teachers'] = len([t for t in teachers if t.get('is_active', True)])
        print(f"✅ Found {len(teachers)} teachers ({self.stats['active_teachers']} active)")
    
    def validate_classes(self):
        """Validate class records"""
        print("🔍 Validating Classes...")
        classes = []
        
        for key in repldb.prefix("class:"):
            try:
                class_data = repldb[key]
                classes.append(class_data)
                
                # Check required fields
                if not class_data.get('name') or not class_data.get('section'):
                    self.log_issue("Class", f"Class {class_data.get('id')} missing name or section", "ERROR")
                
                # Validate teacher assignment
                teacher_id = class_data.get('teacher_id')
                if teacher_id:
                    teacher_key = f"teacher:{teacher_id}"
                    if teacher_key not in repldb:
                        self.log_issue("Class", f"Class {class_data.get('name')}-{class_data.get('section')} assigned to non-existent teacher", "WARNING")
                
            except Exception as e:
                self.log_issue("Class", f"Error reading class data: {str(e)}", "ERROR")
        
        self.stats['classes'] = len(classes)
        print(f"✅ Found {len(classes)} classes")
    
    def validate_attendance(self):
        """Validate attendance records"""
        print("🔍 Validating Attendance...")
        student_attendance = []
        teacher_attendance = []
        
        for key in repldb.prefix("attendance:"):
            try:
                attendance = repldb[key]
                student_attendance.append(attendance)
                
                # Validate student exists
                student_id = attendance.get('student_id')
                if student_id:
                    student_key = f"student:{student_id}"
                    if student_key not in repldb:
                        self.log_issue("Attendance", f"Attendance record for non-existent student: {student_id}", "WARNING")
                
                # Validate status
                status = attendance.get('status')
                if status not in ['Present', 'Absent', 'Late']:
                    self.log_issue("Attendance", f"Invalid attendance status: {status}", "WARNING")
                
            except Exception as e:
                self.log_issue("Attendance", f"Error reading attendance data: {str(e)}", "ERROR")
        
        for key in repldb.prefix("teacher_attendance:"):
            try:
                attendance = repldb[key]
                teacher_attendance.append(attendance)
                
                # Validate teacher exists
                teacher_id = attendance.get('teacher_id')
                if teacher_id:
                    teacher_key = f"teacher:{teacher_id}"
                    if teacher_key not in repldb:
                        self.log_issue("Teacher Attendance", f"Attendance record for non-existent teacher: {teacher_id}", "WARNING")
                
            except Exception as e:
                self.log_issue("Teacher Attendance", f"Error reading teacher attendance data: {str(e)}", "ERROR")
        
        self.stats['student_attendance_records'] = len(student_attendance)
        self.stats['teacher_attendance_records'] = len(teacher_attendance)
        print(f"✅ Found {len(student_attendance)} student attendance records")
        print(f"✅ Found {len(teacher_attendance)} teacher attendance records")
    
    def validate_fees(self):
        """Validate fee records"""
        print("🔍 Validating Fees...")
        fees = []
        
        for key in repldb.prefix("fee:"):
            try:
                fee = repldb[key]
                fees.append(fee)
                
                # Validate student exists
                student_id = fee.get('student_id')
                if student_id:
                    student_key = f"student:{student_id}"
                    if student_key not in repldb:
                        self.log_issue("Fee", f"Fee record for non-existent student: {student_id}", "WARNING")
                
                # Validate amount
                amount = fee.get('amount')
                if not isinstance(amount, (int, float)) or amount <= 0:
                    self.log_issue("Fee", f"Invalid fee amount: {amount}", "ERROR")
                
            except Exception as e:
                self.log_issue("Fee", f"Error reading fee data: {str(e)}", "ERROR")
        
        paid_fees = len([f for f in fees if f.get('is_paid', False)])
        self.stats['total_fees'] = len(fees)
        self.stats['paid_fees'] = paid_fees
        self.stats['unpaid_fees'] = len(fees) - paid_fees
        print(f"✅ Found {len(fees)} fee records ({paid_fees} paid, {len(fees) - paid_fees} unpaid)")
    
    def validate_sms_system(self):
        """Validate SMS templates and logs"""
        print("🔍 Validating SMS System...")
        templates = []
        logs = []
        
        for key in repldb.prefix("sms_template:"):
            try:
                template = repldb[key]
                templates.append(template)
                
                # Check required fields
                if not template.get('name') or not template.get('message'):
                    self.log_issue("SMS Template", f"Template {template.get('id')} missing name or message", "ERROR")
                
            except Exception as e:
                self.log_issue("SMS Template", f"Error reading SMS template: {str(e)}", "ERROR")
        
        for key in repldb.prefix("sms_log:"):
            try:
                log = repldb[key]
                logs.append(log)
                
            except Exception as e:
                self.log_issue("SMS Log", f"Error reading SMS log: {str(e)}", "ERROR")
        
        sent_sms = len([l for l in logs if l.get('status') == 'sent'])
        self.stats['sms_templates'] = len(templates)
        self.stats['sms_logs'] = len(logs)
        self.stats['sent_sms'] = sent_sms
        print(f"✅ Found {len(templates)} SMS templates")
        print(f"✅ Found {len(logs)} SMS logs ({sent_sms} sent)")
    
    def check_data_relationships(self):
        """Check data relationship integrity"""
        print("🔍 Checking Data Relationships...")
        
        # Students without valid classes
        student_class_issues = 0
        for key in repldb.prefix("student:"):
            try:
                student = repldb[key]
                class_id = student.get('class_id')
                if class_id:
                    class_key = f"class:{class_id}"
                    if class_key not in repldb:
                        self.log_issue("Relationship", f"Student {student.get('name')} assigned to non-existent class", "ERROR")
                        student_class_issues += 1
            except:
                pass
        
        if student_class_issues == 0:
            print("✅ All students have valid class assignments")
        else:
            print(f"❌ Found {student_class_issues} student-class relationship issues")
    
    def run_validation(self):
        """Run complete database validation"""
        print("🎯 School Management System - Database Validation")
        print("=" * 60)
        
        validation_methods = [
            self.validate_admin_users,
            self.validate_students,
            self.validate_teachers,
            self.validate_classes,
            self.validate_attendance,
            self.validate_fees,
            self.validate_sms_system,
            self.check_data_relationships
        ]
        
        for method in validation_methods:
            try:
                method()
                print()
            except Exception as e:
                self.log_issue("Validation", f"Error in {method.__name__}: {str(e)}", "ERROR")
        
        self.generate_validation_report()
    
    def generate_validation_report(self):
        """Generate validation report"""
        print("=" * 60)
        print("📊 DATABASE VALIDATION REPORT")
        print("=" * 60)
        
        # Statistics
        print("📈 Database Statistics:")
        for key, value in self.stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Issues summary
        errors = len([i for i in self.issues if i['severity'] == 'ERROR'])
        warnings = len([i for i in self.issues if i['severity'] == 'WARNING'])
        
        print(f"\n🚨 Issues Found:")
        print(f"  🔴 Errors: {errors}")
        print(f"  🟡 Warnings: {warnings}")
        print(f"  Total Issues: {len(self.issues)}")
        
        if len(self.issues) == 0:
            print("✅ Database validation passed - No issues found!")
        else:
            print("\n📝 Issue Details:")
            for issue in self.issues[:10]:  # Show first 10 issues
                print(f"  [{issue['severity']}] {issue['category']}: {issue['message']}")
            
            if len(self.issues) > 10:
                print(f"  ... and {len(self.issues) - 10} more issues")
        
        # Save detailed report
        report_filename = f"db_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump({
                'statistics': self.stats,
                'issues': self.issues,
                'summary': {
                    'total_issues': len(self.issues),
                    'errors': errors,
                    'warnings': warnings
                },
                'generated_at': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📋 Detailed validation report saved: {report_filename}")
        print("=" * 60)

if __name__ == "__main__":
    validator = DatabaseValidator()
    validator.run_validation()

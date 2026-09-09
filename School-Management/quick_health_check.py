
#!/usr/bin/env python3
"""
Quick Health Check - Fast system status verification
"""

import requests
import json
import time
from datetime import datetime
from replit import db as repldb

def quick_health_check():
    print("🏥 School Management System - Quick Health Check")
    print("=" * 50)
    
    health_status = []
    
    # 1. Check Flask App Status
    try:
        start_time = time.time()
        response = requests.get("http://0.0.0.0:5000/", timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code in [200, 302]:  # 302 for redirect to login
            health_status.append(("Flask App", "🟢 HEALTHY", f"{response_time:.0f}ms"))
        else:
            health_status.append(("Flask App", "🟡 WARNING", f"Status: {response.status_code}"))
    except Exception as e:
        health_status.append(("Flask App", "🔴 CRITICAL", f"Not responding: {str(e)[:30]}"))
    
    # 2. Check Database Connectivity
    try:
        # Simple database operation
        test_key = f"health_check_{int(time.time())}"
        repldb[test_key] = {"test": True, "timestamp": datetime.now().isoformat()}
        del repldb[test_key]
        health_status.append(("Database", "🟢 HEALTHY", "Read/Write OK"))
    except Exception as e:
        health_status.append(("Database", "🔴 CRITICAL", f"Error: {str(e)[:30]}"))
    
    # 3. Check Data Integrity (Quick)
    try:
        # Count basic collections
        student_count = len(list(repldb.prefix("student:")))
        teacher_count = len(list(repldb.prefix("teacher:")))
        class_count = len(list(repldb.prefix("class:")))
        
        if student_count > 0 or teacher_count > 0 or class_count > 0:
            health_status.append(("Data Integrity", "🟢 HEALTHY", f"S:{student_count} T:{teacher_count} C:{class_count}"))
        else:
            health_status.append(("Data Integrity", "🟡 WARNING", "No data found"))
    except Exception as e:
        health_status.append(("Data Integrity", "🔴 CRITICAL", f"Error: {str(e)[:30]}"))
    
    # 4. Check Authentication System
    try:
        admin_count = len(list(repldb.prefix("admin:")))
        if admin_count > 0:
            health_status.append(("Authentication", "🟢 HEALTHY", f"{admin_count} admin(s)"))
        else:
            health_status.append(("Authentication", "🔴 CRITICAL", "No admin users"))
    except Exception as e:
        health_status.append(("Authentication", "🔴 CRITICAL", f"Error: {str(e)[:30]}"))
    
    # 5. Check SMS Configuration
    try:
        import main
        if hasattr(main, 'INFOBIP_API_KEY') and main.INFOBIP_API_KEY:
            health_status.append(("SMS System", "🟢 HEALTHY", "API Key configured"))
        else:
            health_status.append(("SMS System", "🟡 WARNING", "No API Key"))
    except Exception as e:
        health_status.append(("SMS System", "🟡 WARNING", "Config check failed"))
    
    # 6. Check Critical Pages
    critical_pages = ['/login', '/dashboard', '/students', '/teachers']
    page_status = []
    
    try:
        session = requests.Session()
        # Login first
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post("http://0.0.0.0:5000/login", data=login_data, timeout=5)
        
        for page in critical_pages:
            try:
                response = session.get(f"http://0.0.0.0:5000{page}", timeout=3)
                if response.status_code == 200:
                    page_status.append("✅")
                else:
                    page_status.append("❌")
            except:
                page_status.append("❌")
        
        success_rate = (page_status.count("✅") / len(page_status)) * 100
        if success_rate == 100:
            health_status.append(("Page Accessibility", "🟢 HEALTHY", f"All pages OK"))
        elif success_rate >= 75:
            health_status.append(("Page Accessibility", "🟡 WARNING", f"{success_rate:.0f}% accessible"))
        else:
            health_status.append(("Page Accessibility", "🔴 CRITICAL", f"Only {success_rate:.0f}% accessible"))
    except:
        health_status.append(("Page Accessibility", "🔴 CRITICAL", "Cannot test pages"))
    
    # Display Results
    print("\n📊 Health Check Results:")
    print("-" * 50)
    
    healthy_count = 0
    warning_count = 0
    critical_count = 0
    
    for component, status, details in health_status:
        print(f"{status} {component:<20} | {details}")
        
        if "🟢" in status:
            healthy_count += 1
        elif "🟡" in status:
            warning_count += 1
        elif "🔴" in status:
            critical_count += 1
    
    print("-" * 50)
    print(f"📈 Summary: {healthy_count} Healthy | {warning_count} Warnings | {critical_count} Critical")
    
    # Overall Status
    if critical_count > 0:
        overall_status = "🔴 SYSTEM NEEDS ATTENTION"
    elif warning_count > 0:
        overall_status = "🟡 SYSTEM NEEDS MONITORING"
    else:
        overall_status = "🟢 SYSTEM HEALTHY"
    
    print(f"\n🎯 Overall Status: {overall_status}")
    
    # Quick recommendations
    print(f"\n💡 Quick Actions:")
    if critical_count > 0:
        print("  • Run full system diagnostics: python run_all_tests.py")
        print("  • Check application logs for errors")
        print("  • Verify database connectivity")
    elif warning_count > 0:
        print("  • Monitor system performance")
        print("  • Consider running detailed tests")
    else:
        print("  • System is operating normally")
        print("  • Schedule regular health checks")
    
    print(f"\n⏰ Check completed at: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)

if __name__ == "__main__":
    quick_health_check()

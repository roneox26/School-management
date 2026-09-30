import sys
import traceback
sys.stdout.reconfigure(encoding='utf-8')

from main import app, get_from_db, query_db
from datetime import datetime, timezone

with app.app_context():
    try:
        classes = get_from_db('class') or []
        teachers = query_db('teacher', is_active=True) or []
        schedules = get_from_db('schedule') or []
        subjects = get_from_db('subject') or []
        print(f"classes: {len(classes)}")
        print(f"teachers: {len(teachers)}")
        print(f"schedules: {len(schedules)}")
        print(f"subjects: {len(subjects)}")

        # Simulate what the route does
        selected_class = ''
        selected_day = ''
        selected_subject = ''

        if not subjects:
            default_subjects = [
                {'name': 'Bengali', 'code': 'BAN', 'color': '#4CAF50', 'is_active': True},
            ]
            print("No subjects found, would create defaults")

        filtered_schedules = []
        for schedule in schedules:
            if schedule:
                if selected_class and schedule.get('class_id') != selected_class:
                    continue
                if selected_day and schedule.get('day_of_week') != selected_day:
                    continue
                if selected_subject and schedule.get('subject') != selected_subject:
                    continue
                teacher_data = get_from_db('teacher', schedule.get('teacher_id'))
                if teacher_data:
                    schedule['teacher_name'] = teacher_data.get('name')
                subject_data = next((s for s in subjects if s.get('name') == schedule.get('subject')), None)
                schedule['subject_color'] = subject_data.get('color', '#e3f2fd') if subject_data else '#e3f2fd'
                filtered_schedules.append(schedule)

        default_time_slots = [
            "09:00-09:45", "09:45-10:30", "10:30-11:15", "11:15-12:00",
            "12:00-12:45", "02:00-02:45", "02:45-03:30", "03:30-04:15"
        ]
        saved_periods = get_from_db('period') or []
        saved_slots = [p.get('time') for p in saved_periods if p.get('time')]
        all_slots = list(dict.fromkeys(default_time_slots + saved_slots))
        time_slots = sorted(all_slots)

        schedule_subjects = list(set([s.get('subject') for s in schedules if s and s.get('subject')]))

        print(f"filtered_schedules: {len(filtered_schedules)}")
        print(f"time_slots: {time_slots}")
        print(f"schedule_subjects: {schedule_subjects}")

        # Now try rendering the template
        with app.test_request_context('/class_schedule'):
            from flask import render_template
            html = render_template('class_schedule.html',
                classes=classes,
                teachers=teachers,
                schedules=filtered_schedules,
                subjects=subjects,
                schedule_subjects=schedule_subjects,
                time_slots=time_slots,
                selected_class=selected_class,
                selected_day=selected_day,
                selected_subject=selected_subject)
            print(f"Template rendered OK, length: {len(html)}")

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()

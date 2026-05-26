"""
Management command to seed AttendWise with demo data.
Usage: python manage.py create_demo_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from attendance.models import UserProfile, Department, ClassRoom, Subject, Teacher, Student, Attendance
import random
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Create demo data for AttendWise'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating demo data...')

        # Superuser / Admin
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@attendwise.com', 'admin123')
            admin.first_name = 'System'
            admin.last_name = 'Admin'
            admin.save()
            UserProfile.objects.create(user=admin, role='admin')
            self.stdout.write(self.style.SUCCESS('  Created admin user (admin / admin123)'))

        # Departments
        dept_cs, _ = Department.objects.get_or_create(name='Computer Science', defaults={'code': 'CS', 'description': 'CS Dept'})
        dept_ec, _ = Department.objects.get_or_create(name='Electronics', defaults={'code': 'EC', 'description': 'EC Dept'})

        # Classes
        cs3a, _ = ClassRoom.objects.get_or_create(name='CS-3', section='A', year=3, department=dept_cs)
        cs2b, _ = ClassRoom.objects.get_or_create(name='CS-2', section='B', year=2, department=dept_cs)
        ec2a, _ = ClassRoom.objects.get_or_create(name='EC-2', section='A', year=2, department=dept_ec)

        # Subjects
        sub_ds,  _ = Subject.objects.get_or_create(code='CS301', defaults={'name': 'Data Structures', 'classroom': cs3a, 'credits': 4})
        sub_db,  _ = Subject.objects.get_or_create(code='CS302', defaults={'name': 'Database Systems', 'classroom': cs3a, 'credits': 3})
        sub_ml,  _ = Subject.objects.get_or_create(code='CS303', defaults={'name': 'Machine Learning', 'classroom': cs3a, 'credits': 4})
        sub_cn,  _ = Subject.objects.get_or_create(code='CS201', defaults={'name': 'Computer Networks', 'classroom': cs2b, 'credits': 3})
        sub_ec1, _ = Subject.objects.get_or_create(code='EC201', defaults={'name': 'Circuit Theory', 'classroom': ec2a, 'credits': 4})

        # Teachers
        teachers_data = [
            ('teacher1', 'Alice', 'Johnson', 'T001', dept_cs, [sub_ds, sub_db]),
            ('teacher2', 'Bob', 'Smith', 'T002', dept_cs, [sub_ml, sub_cn]),
            ('teacher3', 'Carol', 'Davis', 'T003', dept_ec, [sub_ec1]),
        ]
        teacher_objects = []
        for uname, first, last, eid, dept, subjects in teachers_data:
            if not User.objects.filter(username=uname).exists():
                u = User.objects.create_user(uname, f'{uname}@school.edu', 'Teacher@123')
                u.first_name = first; u.last_name = last; u.save()
                UserProfile.objects.create(user=u, role='teacher')
                t, _ = Teacher.objects.get_or_create(user=u, defaults={'employee_id': eid, 'department': dept})
                t.subjects.set(subjects)
                teacher_objects.append(t)
                self.stdout.write(f'  Created teacher: {uname} / Teacher@123')
            else:
                teacher_objects.append(Teacher.objects.get(user__username=uname))

        # Students
        students_data = [
            ('student1', 'Arjun', 'Sharma', 'CS21001', 'ENR21001', cs3a),
            ('student2', 'Priya', 'Patel', 'CS21002', 'ENR21002', cs3a),
            ('student3', 'Rahul', 'Verma', 'CS21003', 'ENR21003', cs3a),
            ('student4', 'Sneha', 'Gupta', 'CS21004', 'ENR21004', cs3a),
            ('student5', 'Akash', 'Singh', 'CS21005', 'ENR21005', cs3a),
            ('student6', 'Nisha', 'Kumar', 'CS22001', 'ENR22001', cs2b),
            ('student7', 'Deepak', 'Rao',   'CS22002', 'ENR22002', cs2b),
            ('student8', 'Pooja', 'Mehta',  'EC21001', 'ENR23001', ec2a),
        ]
        student_objects = []
        for uname, first, last, roll, enr, cls in students_data:
            if not User.objects.filter(username=uname).exists():
                u = User.objects.create_user(uname, f'{uname}@school.edu', 'Student@123')
                u.first_name = first; u.last_name = last; u.save()
                UserProfile.objects.create(user=u, role='student')
                s, _ = Student.objects.get_or_create(user=u, defaults={'roll_number': roll, 'enrollment_number': enr, 'classroom': cls})
                student_objects.append(s)
                self.stdout.write(f'  Created student: {uname} / Student@123')
            else:
                try:
                    student_objects.append(Student.objects.get(user__username=uname))
                except Student.DoesNotExist:
                    pass

        # Generate attendance for last 30 days
        self.stdout.write('  Generating attendance records...')
        all_subjects = [sub_ds, sub_db, sub_ml, sub_cn, sub_ec1]
        teacher_map = {sub_ds: teacher_objects[0], sub_db: teacher_objects[0],
                       sub_ml: teacher_objects[1], sub_cn: teacher_objects[1],
                       sub_ec1: teacher_objects[2]}

        records_created = 0
        for i in range(30, 0, -1):
            d = date.today() - timedelta(days=i)
            if d.weekday() >= 5:  # skip weekends
                continue
            for student in student_objects:
                if student.classroom is None:
                    continue
                for subject in student.classroom.subjects.all():
                    if not Attendance.objects.filter(student=student, subject=subject, date=d).exists():
                        # Give student1/student3 low attendance
                        if student.roll_number in ('CS21001', 'CS21003'):
                            status = random.choices(['present', 'absent'], weights=[50, 50])[0]
                        else:
                            status = random.choices(['present', 'absent', 'late'], weights=[80, 15, 5])[0]
                        Attendance.objects.create(
                            student=student, subject=subject, date=d, status=status,
                            teacher=teacher_map.get(subject)
                        )
                        records_created += 1

        self.stdout.write(self.style.SUCCESS(f'  Created {records_created} attendance records'))
        self.stdout.write(self.style.SUCCESS('\nDemo data created successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin:   admin / admin123')
        self.stdout.write('  Teacher: teacher1 / Teacher@123')
        self.stdout.write('  Student: student1 / Student@123')

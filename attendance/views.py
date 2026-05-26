import csv
import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.utils import timezone

from .models import UserProfile, Department, ClassRoom, Subject, Teacher, Student, Attendance
from .forms import (
    LoginForm, RegisterForm, StudentForm, TeacherForm,
    SubjectForm, ClassRoomForm, DepartmentForm,
    AttendanceMarkForm, AttendanceFilterForm
)
from .decorators import admin_required, teacher_required, student_required


# ─────────────────────────────────────────────
# Public Pages
# ─────────────────────────────────────────────

def home(request):
    stats = {
        'students': Student.objects.count(),
        'teachers': Teacher.objects.count(),
        'subjects': Subject.objects.count(),
        'classes': ClassRoom.objects.count(),
    }
    return render(request, 'home.html', {'stats': stats})


def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        messages.success(request, 'Your message has been sent! We will get back to you soon.')
        return redirect('contact')
    return render(request, 'contact.html')


# ─────────────────────────────────────────────
# Authentication
# ─────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.email = form.cleaned_data['email']
        user.save()
        role = form.cleaned_data.get('role', 'student')
        UserProfile.objects.create(user=user, role=role, phone=form.cleaned_data.get('phone', ''))
        messages.success(request, 'Account created! Please log in.')
        return redirect('login')
    return render(request, 'auth/register.html', {'form': form})


def forgot_password(request):
    if request.method == 'POST':
        messages.info(request, 'If that email is registered, a reset link has been sent.')
    return render(request, 'auth/forgot_password.html')


@login_required
def dashboard_redirect(request):
    try:
        role = request.user.profile.role
    except UserProfile.DoesNotExist:
        role = 'student'
    if role == 'admin' or request.user.is_superuser:
        return redirect('admin_dashboard')
    elif role == 'teacher':
        return redirect('teacher_dashboard')
    else:
        return redirect('student_dashboard')


# ─────────────────────────────────────────────
# Admin Views
# ─────────────────────────────────────────────

@login_required
@admin_required
def admin_dashboard(request):
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_subjects = Subject.objects.count()
    total_classes = ClassRoom.objects.count()

    # Today's attendance stats
    today = date.today()
    today_attendance = Attendance.objects.filter(date=today)
    today_present = today_attendance.filter(status='present').count()
    today_absent = today_attendance.filter(status='absent').count()

    # Last 7 days attendance for chart
    chart_labels = []
    chart_present = []
    chart_absent = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        chart_labels.append(d.strftime('%b %d'))
        day_att = Attendance.objects.filter(date=d)
        chart_present.append(day_att.filter(status='present').count())
        chart_absent.append(day_att.filter(status='absent').count())

    # Low attendance students (< 75%)
    low_attendance = []
    for student in Student.objects.select_related('user', 'classroom'):
        pct = student.attendance_percentage()
        if pct < 75:
            low_attendance.append({'student': student, 'percentage': pct})
    low_attendance = sorted(low_attendance, key=lambda x: x['percentage'])[:10]

    # Subject-wise attendance for doughnut chart
    subjects = Subject.objects.all()[:6]
    subject_labels = []
    subject_present_pct = []
    for sub in subjects:
        total = Attendance.objects.filter(subject=sub).count()
        present = Attendance.objects.filter(subject=sub, status='present').count()
        pct = round((present / total * 100), 1) if total else 0
        subject_labels.append(sub.name)
        subject_present_pct.append(pct)

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_subjects': total_subjects,
        'total_classes': total_classes,
        'today_present': today_present,
        'today_absent': today_absent,
        'chart_labels': json.dumps(chart_labels),
        'chart_present': json.dumps(chart_present),
        'chart_absent': json.dumps(chart_absent),
        'subject_labels': json.dumps(subject_labels),
        'subject_present_pct': json.dumps(subject_present_pct),
        'low_attendance': low_attendance,
        'recent_attendance': Attendance.objects.select_related('student__user', 'subject').order_by('-created_at')[:10],
    }
    return render(request, 'admin_panel/dashboard.html', context)


# Students CRUD
@login_required
@admin_required
def manage_students(request):
    q = request.GET.get('q', '')
    students = Student.objects.select_related('user', 'classroom')
    if q:
        students = students.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(roll_number__icontains=q) |
            Q(enrollment_number__icontains=q)
        )
    return render(request, 'admin_panel/students.html', {'students': students, 'q': q})


@login_required
@admin_required
def add_student(request):
    form = StudentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(
                username=username,
                password=form.cleaned_data['password'] or 'Student@123',
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
            )
            UserProfile.objects.create(user=user, role='student')
            student = form.save(commit=False)
            student.user = user
            student.save()
            messages.success(request, f'Student {user.get_full_name()} added successfully.')
            return redirect('manage_students')
    return render(request, 'admin_panel/student_form.html', {'form': form, 'title': 'Add Student'})


@login_required
@admin_required
def edit_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, instance=student)
    if request.method == 'POST' and form.is_valid():
        user = student.user
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.email = form.cleaned_data['email']
        if form.cleaned_data.get('password'):
            user.set_password(form.cleaned_data['password'])
        user.save()
        form.save()
        messages.success(request, 'Student updated.')
        return redirect('manage_students')
    # Pre-populate user fields
    form.fields['first_name'].initial = student.user.first_name
    form.fields['last_name'].initial = student.user.last_name
    form.fields['email'].initial = student.user.email
    form.fields['username'].initial = student.user.username
    return render(request, 'admin_panel/student_form.html', {'form': form, 'title': 'Edit Student', 'student': student})


@login_required
@admin_required
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.user.delete()
        messages.success(request, 'Student deleted.')
        return redirect('manage_students')
    return render(request, 'admin_panel/confirm_delete.html', {'object': student, 'back_url': 'manage_students'})


# Teachers CRUD
@login_required
@admin_required
def manage_teachers(request):
    q = request.GET.get('q', '')
    teachers = Teacher.objects.select_related('user', 'department')
    if q:
        teachers = teachers.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(employee_id__icontains=q)
        )
    return render(request, 'admin_panel/teachers.html', {'teachers': teachers, 'q': q})


@login_required
@admin_required
def add_teacher(request):
    form = TeacherForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(
                username=username,
                password=form.cleaned_data['password'] or 'Teacher@123',
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
            )
            UserProfile.objects.create(user=user, role='teacher')
            teacher = form.save(commit=False)
            teacher.user = user
            teacher.save()
            form.save_m2m()
            messages.success(request, f'Teacher {user.get_full_name()} added.')
            return redirect('manage_teachers')
    return render(request, 'admin_panel/teacher_form.html', {'form': form, 'title': 'Add Teacher'})


@login_required
@admin_required
def edit_teacher(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    form = TeacherForm(request.POST or None, instance=teacher)
    if request.method == 'POST' and form.is_valid():
        user = teacher.user
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.email = form.cleaned_data['email']
        if form.cleaned_data.get('password'):
            user.set_password(form.cleaned_data['password'])
        user.save()
        form.save()
        messages.success(request, 'Teacher updated.')
        return redirect('manage_teachers')
    form.fields['first_name'].initial = teacher.user.first_name
    form.fields['last_name'].initial = teacher.user.last_name
    form.fields['email'].initial = teacher.user.email
    form.fields['username'].initial = teacher.user.username
    return render(request, 'admin_panel/teacher_form.html', {'form': form, 'title': 'Edit Teacher', 'teacher': teacher})


@login_required
@admin_required
def delete_teacher(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        teacher.user.delete()
        messages.success(request, 'Teacher deleted.')
        return redirect('manage_teachers')
    return render(request, 'admin_panel/confirm_delete.html', {'object': teacher, 'back_url': 'manage_teachers'})


# Subjects CRUD
@login_required
@admin_required
def manage_subjects(request):
    subjects = Subject.objects.select_related('classroom')
    return render(request, 'admin_panel/subjects.html', {'subjects': subjects})


@login_required
@admin_required
def add_subject(request):
    form = SubjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Subject added.')
        return redirect('manage_subjects')
    return render(request, 'admin_panel/subject_form.html', {'form': form, 'title': 'Add Subject'})


@login_required
@admin_required
def edit_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, instance=subject)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Subject updated.')
        return redirect('manage_subjects')
    return render(request, 'admin_panel/subject_form.html', {'form': form, 'title': 'Edit Subject'})


@login_required
@admin_required
def delete_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted.')
        return redirect('manage_subjects')
    return render(request, 'admin_panel/confirm_delete.html', {'object': subject, 'back_url': 'manage_subjects'})


# ClassRoom CRUD
@login_required
@admin_required
def manage_classes(request):
    classes = ClassRoom.objects.select_related('department').annotate(student_count=Count('students'))
    return render(request, 'admin_panel/classes.html', {'classes': classes})


@login_required
@admin_required
def add_class(request):
    form = ClassRoomForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Class added.')
        return redirect('manage_classes')
    return render(request, 'admin_panel/class_form.html', {'form': form, 'title': 'Add Class'})


@login_required
@admin_required
def edit_class(request, pk):
    classroom = get_object_or_404(ClassRoom, pk=pk)
    form = ClassRoomForm(request.POST or None, instance=classroom)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Class updated.')
        return redirect('manage_classes')
    return render(request, 'admin_panel/class_form.html', {'form': form, 'title': 'Edit Class'})


@login_required
@admin_required
def delete_class(request, pk):
    classroom = get_object_or_404(ClassRoom, pk=pk)
    if request.method == 'POST':
        classroom.delete()
        messages.success(request, 'Class deleted.')
        return redirect('manage_classes')
    return render(request, 'admin_panel/confirm_delete.html', {'object': classroom, 'back_url': 'manage_classes'})


# Departments CRUD
@login_required
@admin_required
def manage_departments(request):
    departments = Department.objects.all()
    return render(request, 'admin_panel/departments.html', {'departments': departments})


@login_required
@admin_required
def add_department(request):
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Department added.')
        return redirect('manage_departments')
    return render(request, 'admin_panel/department_form.html', {'form': form, 'title': 'Add Department'})


@login_required
@admin_required
def edit_department(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=dept)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Department updated.')
        return redirect('manage_departments')
    return render(request, 'admin_panel/department_form.html', {'form': form, 'title': 'Edit Department'})


@login_required
@admin_required
def delete_department(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        dept.delete()
        messages.success(request, 'Department deleted.')
        return redirect('manage_departments')
    return render(request, 'admin_panel/confirm_delete.html', {'object': dept, 'back_url': 'manage_departments'})


# Reports
@login_required
@admin_required
def admin_reports(request):
    form = AttendanceFilterForm(request.GET or None)
    attendance_qs = Attendance.objects.select_related('student__user', 'subject', 'teacher__user')
    if form.is_valid():
        if form.cleaned_data.get('classroom'):
            attendance_qs = attendance_qs.filter(student__classroom=form.cleaned_data['classroom'])
        if form.cleaned_data.get('subject'):
            attendance_qs = attendance_qs.filter(subject=form.cleaned_data['subject'])
        if form.cleaned_data.get('start_date'):
            attendance_qs = attendance_qs.filter(date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            attendance_qs = attendance_qs.filter(date__lte=form.cleaned_data['end_date'])
        if form.cleaned_data.get('student_name'):
            name = form.cleaned_data['student_name']
            attendance_qs = attendance_qs.filter(
                Q(student__user__first_name__icontains=name) |
                Q(student__user__last_name__icontains=name)
            )
    return render(request, 'admin_panel/reports.html', {'form': form, 'attendance': attendance_qs[:200]})


@login_required
@admin_required
def export_csv(request):
    form = AttendanceFilterForm(request.GET or None)
    attendance_qs = Attendance.objects.select_related('student__user', 'subject', 'teacher__user')
    if form.is_valid():
        if form.cleaned_data.get('subject'):
            attendance_qs = attendance_qs.filter(subject=form.cleaned_data['subject'])
        if form.cleaned_data.get('start_date'):
            attendance_qs = attendance_qs.filter(date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            attendance_qs = attendance_qs.filter(date__lte=form.cleaned_data['end_date'])

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Student Name', 'Roll No', 'Subject', 'Status', 'Teacher'])
    for a in attendance_qs:
        writer.writerow([
            a.date, a.student.user.get_full_name(), a.student.roll_number,
            a.subject.name, a.status.capitalize(),
            a.teacher.user.get_full_name() if a.teacher else '-'
        ])
    return response


@login_required
@admin_required
def export_pdf(request):
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import io

        attendance_qs = Attendance.objects.select_related('student__user', 'subject').order_by('-date')[:200]
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = []
        elements.append(Paragraph('AttendWise – Attendance Report', styles['Title']))
        elements.append(Spacer(1, 12))
        data = [['Date', 'Student Name', 'Roll No', 'Subject', 'Status']]
        for a in attendance_qs:
            data.append([str(a.date), a.student.user.get_full_name(), a.student.roll_number, a.subject.name, a.status.capitalize()])
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t)
        doc.build(elements)
        buf.seek(0)
        response = HttpResponse(buf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'
        return response
    except ImportError:
        messages.error(request, 'reportlab is required for PDF export. Install it with: pip install reportlab')
        return redirect('admin_reports')


# ─────────────────────────────────────────────
# Teacher Views
# ─────────────────────────────────────────────

@login_required
@teacher_required
def teacher_dashboard(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    subjects = teacher.subjects.all()
    today = date.today()
    today_records = Attendance.objects.filter(teacher=teacher, date=today)
    today_present = today_records.filter(status='present').count()
    today_absent = today_records.filter(status='absent').count()

    # Monthly data for chart
    chart_labels = []
    chart_present = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        chart_labels.append(d.strftime('%b %d'))
        chart_present.append(
            Attendance.objects.filter(teacher=teacher, date=d, status='present').count()
        )

    # Subject-wise stats
    subject_stats = []
    for sub in subjects:
        total = Attendance.objects.filter(teacher=teacher, subject=sub).count()
        present = Attendance.objects.filter(teacher=teacher, subject=sub, status='present').count()
        subject_stats.append({
            'subject': sub,
            'total': total,
            'present': present,
            'pct': round((present / total * 100), 1) if total else 0,
        })

    context = {
        'teacher': teacher,
        'subjects': subjects,
        'today_present': today_present,
        'today_absent': today_absent,
        'chart_labels': json.dumps(chart_labels),
        'chart_present': json.dumps(chart_present),
        'subject_stats': subject_stats,
        'recent': Attendance.objects.filter(teacher=teacher).select_related('student__user', 'subject').order_by('-date')[:10],
    }
    return render(request, 'teacher/dashboard.html', context)


@login_required
@teacher_required
def mark_attendance(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    form = AttendanceMarkForm(request.GET or None, teacher=teacher)
    students = []
    selected_subject = None
    selected_date = None
    selected_classroom = None

    if form.is_valid():
        selected_classroom = form.cleaned_data['classroom']
        selected_subject = form.cleaned_data['subject']
        selected_date = form.cleaned_data['date']
        students_qs = Student.objects.filter(classroom=selected_classroom).select_related('user')
        for student in students_qs:
            existing = Attendance.objects.filter(
                student=student, subject=selected_subject, date=selected_date
            ).first()
            students.append({
                'student': student,
                'status': existing.status if existing else 'present',
            })

    context = {
        'form': form,
        'students': students,
        'selected_subject': selected_subject,
        'selected_date': selected_date,
        'selected_classroom': selected_classroom,
    }
    return render(request, 'teacher/mark_attendance.html', context)


@login_required
@teacher_required
def save_attendance(request):
    if request.method != 'POST':
        return redirect('mark_attendance')
    teacher = get_object_or_404(Teacher, user=request.user)
    subject_id = request.POST.get('subject_id')
    att_date = request.POST.get('date')
    subject = get_object_or_404(Subject, pk=subject_id)
    student_ids = request.POST.getlist('student_ids')

    saved = 0
    for sid in student_ids:
        student = get_object_or_404(Student, pk=sid)
        status = request.POST.get(f'status_{sid}', 'absent')
        remarks = request.POST.get(f'remarks_{sid}', '')
        obj, created = Attendance.objects.update_or_create(
            student=student, subject=subject, date=att_date,
            defaults={'status': status, 'teacher': teacher, 'remarks': remarks}
        )
        saved += 1

    messages.success(request, f'Attendance saved for {saved} student(s).')
    return redirect('teacher_dashboard')


@login_required
@teacher_required
def teacher_attendance_records(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    form = AttendanceFilterForm(request.GET or None)
    qs = Attendance.objects.filter(teacher=teacher).select_related('student__user', 'subject')
    if form.is_valid():
        if form.cleaned_data.get('subject'):
            qs = qs.filter(subject=form.cleaned_data['subject'])
        if form.cleaned_data.get('start_date'):
            qs = qs.filter(date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            qs = qs.filter(date__lte=form.cleaned_data['end_date'])
    return render(request, 'teacher/attendance_records.html', {'form': form, 'records': qs[:200]})


# ─────────────────────────────────────────────
# Student Views
# ─────────────────────────────────────────────

@login_required
@student_required
def student_dashboard(request):
    student = get_object_or_404(Student, user=request.user)
    subjects = []
    overall_total = 0
    overall_present = 0

    if student.classroom:
        for sub in student.classroom.subjects.all():
            total = Attendance.objects.filter(student=student, subject=sub).count()
            present = Attendance.objects.filter(student=student, subject=sub, status='present').count()
            pct = round((present / total * 100), 1) if total else 0
            overall_total += total
            overall_present += present
            subjects.append({'subject': sub, 'total': total, 'present': present, 'pct': pct})

    overall_pct = round((overall_present / overall_total * 100), 1) if overall_total else 0

    # Monthly chart
    today = date.today()
    chart_labels = []
    chart_pct = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        chart_labels.append(d.strftime('%b %d'))
        total_d = Attendance.objects.filter(student=student, date=d).count()
        present_d = Attendance.objects.filter(student=student, date=d, status='present').count()
        chart_pct.append(round((present_d / total_d * 100), 1) if total_d else 0)

    context = {
        'student': student,
        'subjects': subjects,
        'overall_pct': overall_pct,
        'chart_labels': json.dumps(chart_labels),
        'chart_pct': json.dumps(chart_pct),
        'recent': Attendance.objects.filter(student=student).select_related('subject').order_by('-date')[:10],
    }
    return render(request, 'student/dashboard.html', context)


@login_required
@student_required
def student_attendance(request):
    student = get_object_or_404(Student, user=request.user)
    form = AttendanceFilterForm(request.GET or None)
    qs = Attendance.objects.filter(student=student).select_related('subject', 'teacher__user')
    if form.is_valid():
        if form.cleaned_data.get('subject'):
            qs = qs.filter(subject=form.cleaned_data['subject'])
        if form.cleaned_data.get('start_date'):
            qs = qs.filter(date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            qs = qs.filter(date__lte=form.cleaned_data['end_date'])
    return render(request, 'student/attendance.html', {'form': form, 'records': qs[:200], 'student': student})


@login_required
@student_required
def student_download_report(request):
    student = get_object_or_404(Student, user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{student.roll_number}_attendance.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Subject', 'Status', 'Remarks'])
    for a in Attendance.objects.filter(student=student).select_related('subject').order_by('-date'):
        writer.writerow([a.date, a.subject.name, a.status.capitalize(), a.remarks])
    return response


# ─────────────────────────────────────────────
# AJAX Helpers
# ─────────────────────────────────────────────

def ajax_subjects_by_class(request):
    classroom_id = request.GET.get('classroom_id')
    subjects = Subject.objects.filter(classroom_id=classroom_id).values('id', 'name')
    return JsonResponse({'subjects': list(subjects)})


def ajax_students_by_class(request):
    classroom_id = request.GET.get('classroom_id')
    students = Student.objects.filter(classroom_id=classroom_id).select_related('user')
    data = [{'id': s.id, 'name': s.user.get_full_name(), 'roll': s.roll_number} for s in students]
    return JsonResponse({'students': data})

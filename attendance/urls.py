from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),

    # Dashboard router
    path('dashboard/', views.dashboard_redirect, name='dashboard'),

    # Admin views
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage/students/', views.manage_students, name='manage_students'),
    path('manage/students/add/', views.add_student, name='add_student'),
    path('manage/students/<int:pk>/edit/', views.edit_student, name='edit_student'),
    path('manage/students/<int:pk>/delete/', views.delete_student, name='delete_student'),
    path('manage/teachers/', views.manage_teachers, name='manage_teachers'),
    path('manage/teachers/add/', views.add_teacher, name='add_teacher'),
    path('manage/teachers/<int:pk>/edit/', views.edit_teacher, name='edit_teacher'),
    path('manage/teachers/<int:pk>/delete/', views.delete_teacher, name='delete_teacher'),
    path('manage/subjects/', views.manage_subjects, name='manage_subjects'),
    path('manage/subjects/add/', views.add_subject, name='add_subject'),
    path('manage/subjects/<int:pk>/edit/', views.edit_subject, name='edit_subject'),
    path('manage/subjects/<int:pk>/delete/', views.delete_subject, name='delete_subject'),
    path('manage/classes/', views.manage_classes, name='manage_classes'),
    path('manage/classes/add/', views.add_class, name='add_class'),
    path('manage/classes/<int:pk>/edit/', views.edit_class, name='edit_class'),
    path('manage/classes/<int:pk>/delete/', views.delete_class, name='delete_class'),
    path('manage/departments/', views.manage_departments, name='manage_departments'),
    path('manage/departments/add/', views.add_department, name='add_department'),
    path('manage/departments/<int:pk>/edit/', views.edit_department, name='edit_department'),
    path('manage/departments/<int:pk>/delete/', views.delete_department, name='delete_department'),
    path('manage/reports/', views.admin_reports, name='admin_reports'),
    path('manage/reports/export/csv/', views.export_csv, name='export_csv'),
    path('manage/reports/export/pdf/', views.export_pdf, name='export_pdf'),
    
    # Teacher views
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('teacher/mark-attendance/save/', views.save_attendance, name='save_attendance'),
    path('teacher/attendance-records/', views.teacher_attendance_records, name='teacher_attendance_records'),

    # Student views
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/my-attendance/', views.student_attendance, name='student_attendance'),
    path('student/download-report/', views.student_download_report, name='student_download_report'),

    # AJAX
    path('ajax/subjects-by-class/', views.ajax_subjects_by_class, name='ajax_subjects_by_class'),
    path('ajax/students-by-class/', views.ajax_students_by_class, name='ajax_students_by_class'),
]

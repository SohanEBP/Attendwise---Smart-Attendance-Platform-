from django.contrib import admin
from .models import UserProfile, Department, ClassRoom, Subject, Teacher, Student, Attendance

admin.site.register(UserProfile)
admin.site.register(Department)
admin.site.register(ClassRoom)
admin.site.register(Subject)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(Attendance)

admin.site.site_header = "AttendWise Admin"
admin.site.site_title = "AttendWise"
admin.site.index_title = "Welcome to AttendWise Admin Panel"

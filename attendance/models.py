from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with role information."""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role})"


class Department(models.Model):
    """Academic department / branch."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class ClassRoom(models.Model):
    """A class section, e.g. CS-3A."""
    name = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    year = models.PositiveSmallIntegerField(default=1)
    section = models.CharField(max_length=5, default='A')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'section', 'year', 'department')

    def __str__(self):
        return f"{self.name} - {self.section}"


class Subject(models.Model):
    """A subject taught in one or more classrooms."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='subjects')
    credits = models.PositiveSmallIntegerField(default=3)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Teacher(models.Model):
    """Teacher profile linked to a User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    subjects = models.ManyToManyField(Subject, blank=True, related_name='teachers')
    designation = models.CharField(max_length=100, blank=True)
    joining_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class Student(models.Model):
    """Student profile linked to a User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    enrollment_number = models.CharField(max_length=30, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    admission_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.roll_number})"

    def attendance_percentage(self, subject=None):
        """Calculate overall or subject-wise attendance percentage."""
        qs = Attendance.objects.filter(student=self)
        if subject:
            qs = qs.filter(subject=subject)
        total = qs.count()
        if total == 0:
            return 0
        present = qs.filter(status='present').count()
        return round((present / total) * 100, 2)


class Attendance(models.Model):
    """Individual attendance record per student per subject per date."""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendances')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')
    remarks = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} | {self.subject} | {self.date} | {self.status}"

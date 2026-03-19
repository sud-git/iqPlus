from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# ================= SCHOOL =================

class School(models.Model):
    name = models.CharField(max_length=200, null=False, default="Default School")
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Admin(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=200)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.full_name

# ================= CLASS =================
class ClassModel(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('school', 'name')

    def __str__(self):
        return f"{self.school} - {self.name}"


# ================= SUBJECT =================
class Subject(models.Model):
    class_name = models.ForeignKey(ClassModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('class_name', 'name')

    def __str__(self):
        return f"{self.class_name} - {self.name}"


# ================= CHAPTER =================
class Chapter(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('subject', 'name')

    def __str__(self):
        return f"{self.subject} - {self.name}"


# ================= QUESTION =================

class Question(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    question = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=1)  # A/B/C/D
    marks = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.chapter} - {self.question[:50]}"


# ================= TEST =================
class Test(models.Model):
    class_name = models.ForeignKey(ClassModel, on_delete=models.CASCADE)
    test_name = models.CharField(max_length=200)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    questions = models.ManyToManyField(Question)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ( 'class_name', 'test_name')

    def __str__(self):
        return f"{self.test_name} ({self.class_name.school} - {self.class_name})"



# ================= STUDENT =================
class Student(models.Model):
    full_name = models.CharField(max_length=200)  # Removed unique=True
    father_name = models.CharField(max_length=200, blank=True)  # Removed unique=True
    mobile = models.CharField(max_length=10)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    class_name = models.ForeignKey(ClassModel, on_delete=models.CASCADE)
    pin_code = models.CharField(max_length=10)
    district = models.CharField(max_length=100)
    address = models.TextField()
    username = models.CharField(max_length=100, unique=True)  # Only username should be unique
    password = models.CharField(max_length=255)


    def __str__(self):
        return self.full_name


# ================= STUDENT QUESTION =================
class StudentQuestion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'question', 'test')

    def __str__(self):
        return f"{self.student} - {self.question[:30]}"


# ================= STUDENT TEST (Optional) =================
class StudentTest(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'test')

    def __str__(self):
        return f"{self.student} - {self.test}"


# ================= STUDENT ANSWER (Optional) =================
class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'question', 'test')

    def __str__(self):
        return f"{self.student} - {self.question[:30]}"

class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    marks_obtained = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField()

    @property
    def percentage(self):
        return round((self.marks_obtained / self.total_marks) * 100, 2)

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name}"

class Attempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.IntegerField()
    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.test.test_name}"
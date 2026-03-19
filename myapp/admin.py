from django.contrib import admin

from myapp.models import School, Admin, ClassModel, Question, Chapter, Subject, Test, Student, StudentQuestion, \
    StudentTest, StudentAnswer, Result, Attempt

# Register your models here.

admin.site.register(Admin)
admin.site.register(School)
admin.site.register(ClassModel)
admin.site.register(Subject)
admin.site.register(Chapter)
admin.site.register(Question)
admin.site.register(Test)
admin.site.register(Student)
admin.site.register(StudentQuestion)
admin.site.register(StudentTest)
admin.site.register(StudentAnswer)
admin.site.register(Result)
admin.site.register(Attempt)

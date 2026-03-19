"""
URL configuration for my_iq_test project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("admin_login/", views.admin_login, name="admin_login"),
    path('admin_login_code/', views.admin_login_code, name='admin_login_code'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path("add_question/", views.add_question, name="add_question"),
    path("add_question_code/", views.add_question_code, name="add_question_code"),
    path("bulk-text-upload/", views.bulk_text_upload_questions, name="bulk_text_upload_questions"),
    path('ajax/load-subjects/', views.load_subjects, name='load_subjects'),
    path('ajax/load-chapters/', views.load_chapters, name='load_chapters'),
    path('ajax/load-questions/', views.load_questions, name='load_questions'),
    path('question_bank/', views.question_bank, name='question_bank'),
    path('forward_questions/', views.forward_questions, name='forward_questions'),
    path('log_out/', views.log_out, name='log_out'),
    path('result/', views.result, name='result'),
    path('start_test/<int:test_id>/', views.start_test, name='start_test'),
    path('attempted/', views.attempted, name='attempted'),
    path('pending/', views.pending, name='pending'),
    # path('results/download_pdf/', views.download_results_pdf, name='download_results_pdf'),
    path('student_register/', views.student_register, name='student_register'),
    path('student_register_code/', views.student_register_code, name='student_register_code'),
    path("", views.student_login, name="student_login"),
    path("student_login-code/", views.student_login_code, name="student_login_code"),
    path("student_dashboard/", views.student_dashboard, name="student_dashboard"),
    path('total_test/', views.total_test, name='total_test'),
    path('results/', views.results, name='results'),
    path('result-detail/<int:student_test_id>/', views.result_detail, name='result_detail'),


]

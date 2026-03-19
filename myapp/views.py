import csv
from datetime import timedelta
from functools import wraps
from django.utils import timezone

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.db import transaction

from myapp.models import (
    Admin, ClassModel, Subject, Chapter, Question,
    School, Student, StudentQuestion, Test, StudentTest, Result, Attempt, StudentAnswer
)

# ====================== DECORATORS ======================
def admin_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_id'):
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('student_id'):
            return redirect('student_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ====================== ADMIN AUTH ======================

def admin_login(request):
    if request.session.get('admin_id'):
        return redirect('admin_dashboard')
    return render(request, "admin/admin_login.html")


def admin_login_code(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            admin = Admin.objects.get(username=username)

            if password == admin.password:
                request.session['admin_id'] = admin.id
                request.session['admin_name'] = admin.full_name
                request.session['admin_school_id'] = admin.school.id
                return redirect('../admin_dashboard')
            else:
                messages.error(request, "Invalid password")

        except Admin.DoesNotExist:
            messages.error(request, "Admin not found")

        return redirect('../admin_login')

    return redirect('../admin_login')


@admin_login_required
def admin_dashboard(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('admin_login')  # session missing, redirect to login

    try:
        admin = Admin.objects.get(id=admin_id)
    except Admin.DoesNotExist:
        # Admin deleted or invalid id
        request.session.flush()  # clear session
        return redirect('admin_login')

    school_id = admin.school.id
    stats = {
        'total_classes': ClassModel.objects.filter(school_id=school_id).count(),
        'total_subjects': Subject.objects.filter(class_name__school_id=school_id).count(),
        'total_tests': Test.objects.filter(class_name__school_id=school_id).count(),
    }

    return render(request, 'admin/admin_dashboard.html', {
        'admin': admin,
        'stats': stats
    })
# ====================== ADMIN QUESTION BANK ======================

@admin_login_required
def add_question(request):
    admin_school_id = request.session.get("admin_school_id")
    classes = ClassModel.objects.filter(school_id=admin_school_id)

    return render(request, "admin/add_question.html", {
        "classes": classes
    })


@admin_login_required
def add_question_code(request):
    if request.method == "POST":
        admin_school_id = request.session.get("admin_school_id")
        school = School.objects.get(id=admin_school_id)

        class_name = request.POST.get("class_name")
        subject_name = request.POST.get("subject_name")
        chapter_name = request.POST.get("chapter_name")

        # 1️⃣ Class get or create
        class_obj, created = ClassModel.objects.get_or_create(
            school=school,
            name=class_name
        )

        # 2️⃣ Subject get or create
        subject_obj, created = Subject.objects.get_or_create(
            class_name=class_obj,
            name=subject_name
        )

        # 3️⃣ Chapter get or create
        chapter_obj, created = Chapter.objects.get_or_create(
            subject=subject_obj,
            name=chapter_name
        )

        # 4️⃣ Question create
        Question.objects.create(
            chapter=chapter_obj,
            question=request.POST.get("question"),
            option_a=request.POST.get("option_a"),
            option_b=request.POST.get("option_b"),
            option_c=request.POST.get("option_c"),
            option_d=request.POST.get("option_d"),
            correct_answer=request.POST.get("correct_answer"),
            marks=request.POST.get("marks"),
        )

        return redirect("question_bank")

# BULK CSV UPLOAD
# ==============================
@admin_login_required
def bulk_text_upload_questions(request):

    if request.method == "POST":

        admin_school_id = request.session.get("admin_school_id")
        school = School.objects.get(id=admin_school_id)

        bulk_text = request.POST.get("bulk_text")

        if not bulk_text:
            messages.error(request, "No data provided!")
            return redirect("add_question")

        lines = bulk_text.strip().split("\n")
        count = 0

        for line in lines:
            parts = [p.strip() for p in line.split("|")]

            # Format:
            # Class | Subject | Chapter | Question | A | B | C | D | Correct | Marks
            if len(parts) != 10:
                continue

            class_name, subject_name, chapter_name, question_text, \
            option_a, option_b, option_c, option_d, correct_answer, marks = parts

            if correct_answer.upper() not in ['A', 'B', 'C', 'D']:
                continue

            class_obj, _ = ClassModel.objects.get_or_create(
                school=school,
                name=class_name
            )

            subject_obj, _ = Subject.objects.get_or_create(
                class_name=class_obj,
                name=subject_name
            )

            chapter_obj, _ = Chapter.objects.get_or_create(
                subject=subject_obj,
                name=chapter_name
            )

            Question.objects.create(
                chapter=chapter_obj,
                question=question_text,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_answer=correct_answer.upper(),
                marks=int(marks)
            )

            count += 1

        messages.success(request, f"{count} Questions Added Successfully!")
        return redirect("add_question")

    return redirect("add_question")

@admin_login_required
def question_bank(request):

    admin = Admin.objects.get(id=request.session['admin_id'])
    school = admin.school

    if request.method == "POST":

        class_id = request.POST.get('class_name')
        test_name = request.POST.get('test_name')
        duration = request.POST.get('duration')
        question_ids = request.POST.getlist('question_ids')

        if not class_id or not test_name or not duration:
            messages.error(request, "All fields are required.")
            return redirect('question_bank')

        if not question_ids:
            messages.error(request, "Select at least one question.")
            return redirect('question_bank')

        try:
            class_obj = ClassModel.objects.get(id=class_id, school=school)

            # Check for duplicate test name in same class
            if Test.objects.filter(
                class_name=class_obj,
                test_name=test_name
            ).exists():
                messages.error(request, "Test with this name already exists in this class.")
                return redirect('question_bank')

            with transaction.atomic():
                # Create test
                test = Test.objects.create(
                    class_name=class_obj,
                    test_name=test_name,
                    duration=duration
                )

                # Attach questions
                test.questions.set(question_ids)

                # ✅ IMPORTANT: Assign test to all students in this class
                students = Student.objects.filter(
                    school=school,
                    class_name=class_obj
                )
                
                print(f"[QUESTION_BANK] Test created: {test.test_name}")
                print(f"[QUESTION_BANK] School: {school.name} (ID: {school.id})")
                print(f"[QUESTION_BANK] Class: {class_obj.name} (ID: {class_obj.id})")
                print(f"[QUESTION_BANK] Students found: {students.count()}")
                
                if students.count() == 0:
                    print("⚠️  [QUESTION_BANK] WARNING: No students found!")
                
                # Use get_or_create to prevent duplicates
                assigned_count = 0
                for student in students:
                    st, created = StudentTest.objects.get_or_create(
                        student=student,
                        test=test
                    )
                    if created:
                        assigned_count += 1
                        print(f"  ✓ Assigned: {student.full_name}")
                
                print(f"[QUESTION_BANK] Total assigned: {assigned_count}")

            messages.success(request, f"Test Created & Assigned to {assigned_count} students!")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect('question_bank')


    classes = ClassModel.objects.filter(school=school)
    subjects = Subject.objects.filter(class_name__school=school)
    questions = Question.objects.filter(
        chapter__subject__class_name__school=school
    )

    return render(request, 'admin/question_bank.html', {
        'classes': classes,
        'subjects': subjects,
        'questions': questions
    })

# ====================== AJAX ======================

def load_subjects(request):
    class_id = request.GET.get('class_id')
    subjects = Subject.objects.filter(class_name_id=class_id).values('id','name')
    return JsonResponse(list(subjects), safe=False)

def load_chapters(request):
    subject_id = request.GET.get('subject_id')
    chapters = Chapter.objects.filter(subject_id=subject_id).values('id','name')
    return JsonResponse(list(chapters), safe=False)


def load_questions(request):
    chapter_id = request.GET.get('chapter_id')
    questions = Question.objects.filter(chapter_id=chapter_id).values('id','question','marks')
    return JsonResponse(list(questions), safe=False)

# ====================== FORWARD QUESTIONS ======================


@admin_login_required
# def forward_questions(request):
#     admin_id = request.session.get('admin_id')
#     admin = get_object_or_404(Admin, id=admin_id)
#     school = admin.school

#     if request.method == "POST":
#         # ✅ POST data
#         class_id = request.POST.get('class_name')      # name="class_name" in HTML
#         test_name = request.POST.get('test_name')
#         duration = request.POST.get('duration')
#         question_ids = request.POST.getlist('question_ids')

#         # ===== VALIDATION =====
#         if not class_id or not test_name or not duration:
#             messages.error(request, "All fields are required.")
#             return redirect('forward_questions')

#         if not question_ids:
#             messages.error(request, "Select at least one question.")
#             return redirect('forward_questions')

#         try:
#             class_obj = ClassModel.objects.get(id=int(class_id))
#             duration = int(duration)

#             # ===== CHECK DUPLICATE TEST =====
#             if Test.objects.filter(school=school, class_name=class_obj, test_name=test_name).exists():
#                 messages.error(request, "Test with this name already exists.")
#                 return redirect('forward_questions')

#             with transaction.atomic():
#                 # ===== CREATE TEST =====
#                 test = Test.objects.create(
#                     school=school,
#                     class_name=class_obj,
#                     test_name=test_name,
#                     duration=duration
#                 )

#                 # ===== ATTACH QUESTIONS =====
#                 test.questions.set([int(q) for q in question_ids])


#                 # ===== ASSIGN TO STUDENTS =====
#                 students = Student.objects.filter(
#                             school=school,
#                             class_name=class_obj
#                             )
#                 # student_tests = [
#                 #     StudentTest(student=student, test=test) for student in students
#                 # ]
#                 # StudentTest.objects.bulk_create(student_tests)
#                 StudentTest.objects.bulk_create([
#         StudentTest(student=student, test=test)
#         for student in students
#     ])


#             messages.success(request, "Test Created & Forwarded Successfully!")
#             return redirect('forward_questions')

#         except Exception as e:
#             import traceback
#             print(traceback.format_exc())
#             messages.error(request, f"Error: {str(e)}")
#             return redirect('forward_questions')

#     # ===== GET REQUEST =====
#     classes = ClassModel.objects.filter(school=school)
#     subjects = Subject.objects.filter(class_name__school=school)
#     questions = Question.objects.filter(chapter__subject__class_name__school=school)

#     return render(request, 'admin/question_bank.html', {
#         'classes': classes,
#         'subjects': subjects,
#         'questions': questions
#     })

@admin_login_required
def forward_questions(request):
    admin_id = request.session.get('admin_id')
    admin = get_object_or_404(Admin, id=admin_id)
    school = admin.school

    if request.method == "POST":
        
        print("=" * 50)
        print("FORWARD QUESTIONS - POST REQUEST")
        print("=" * 50)

        class_id = request.POST.get('class_name')
        test_name = request.POST.get('test_name')
        duration = request.POST.get('duration')
        question_ids = request.POST.getlist('question_ids')
        
        print(f"Class ID: {class_id}")
        print(f"Test Name: {test_name}")
        print(f"Duration: {duration}")
        print(f"Question IDs: {question_ids}")
        print(f"Total Questions Selected: {len(question_ids)}")

        if not class_id or not test_name or not duration:
            print("ERROR: Missing required fields")
            messages.error(request, "All fields are required.")
            return redirect('forward_questions')

        if not question_ids:
            print("ERROR: No questions selected")
            messages.error(request, "Select at least one question.")
            return redirect('forward_questions')

        try:
            class_obj = ClassModel.objects.get(
                id=int(class_id),
                school=school
            )

            duration = int(duration)

            # ✅ Correct Duplicate Check
            if Test.objects.filter(
                class_name=class_obj,
                test_name=test_name
            ).exists():
                messages.error(request, "Test with this name already exists.")
                return redirect('forward_questions')

            with transaction.atomic():

                # ✅ Correct Test Create
                test = Test.objects.create(
                    class_name=class_obj,
                    test_name=test_name,
                    duration=duration
                )
                print(f"✅ Test Created: {test.id} - {test.test_name}")

                # ✅ Attach Questions
                test.questions.set([int(q) for q in question_ids])
                print(f"✅ Questions Attached: {test.questions.count()}")

                # ✅ Assign To Students
                students = Student.objects.filter(
                    school=school,
                    class_name=class_obj
                )
                print(f"✅ School ID for filtering: {school.id}")
                print(f"✅ School Name: {school.name}")
                print(f"✅ Class ID: {class_obj.id}")
                print(f"✅ Class Name: {class_obj.name}")
                print(f"✅ Found {students.count()} students in {class_obj.name}")
                
                if students.count() == 0:
                    print("⚠️  WARNING: No students found in this class!")
                    print(f"   Checking all students in school {school.name}:")
                    all_students = Student.objects.filter(school=school)
                    print(f"   Total students in school: {all_students.count()}")
                    for s in all_students:
                        print(f"     - {s.full_name}: Class={s.class_name.name} (ID:{s.class_name.id})")

                # Use get_or_create to prevent duplicates
                assigned_count = 0
                for student in students:
                    st, created = StudentTest.objects.get_or_create(
                        student=student,
                        test=test
                    )
                    if created:
                        assigned_count += 1
                        print(f"  ✓ NEW: Assigned to {student.full_name}")
                    else:
                        print(f"  - EXISTS: {student.full_name} already had this test")
                
                print(f"✅ Total Assigned: {assigned_count} students")

            messages.success(request, f"Test Created & Forwarded to {assigned_count} students!")
            print("=" * 50)
            return redirect('forward_questions')

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f"Error: {str(e)}")
            return redirect('forward_questions')

    classes = ClassModel.objects.filter(school=school)
    subjects = Subject.objects.filter(class_name__school=school)
    questions = Question.objects.filter(
        chapter__subject__class_name__school=school
    )

    return render(request, 'admin/farword_question.html', {
        'classes': classes,
        'subjects': subjects,
        'questions': questions
    })

# ====================== RESULTS ======================

@admin_login_required
def result(request):

    admin_school_id = request.session.get('admin_school_id')

    students = Student.objects.filter(
        school_id=admin_school_id
    ).select_related('class_name')

    results = []

    for student in students:

        total_attempt = StudentTest.objects.filter(
            student=student,
            completed=True
        ).count()

        total_pending = StudentTest.objects.filter(
            student=student,
            completed=False
        ).count()

        subject = None
        if StudentTest.objects.filter(student=student).exists():
            subject = StudentTest.objects.filter(student=student).first().test.questions.first().chapter.subject

        results.append({
            "student": student,
            "subject": subject,
            "total_attempt": total_attempt,
            "total_pending": total_pending
        })

    classes = ClassModel.objects.filter(school_id=admin_school_id)
    subjects = Subject.objects.filter(class_name__school_id=admin_school_id)

    return render(request, "admin/result.html", {
        "results": results,
        "classes": classes,
        "subjects": subjects
    })

# ====================== ADMIN LOGOUT ======================

@never_cache
def log_out(request):
    request.session.flush()
    return redirect('admin_login')

# ====================== STUDENT AUTH ======================

def student_register(request):
    return render(request, "student/student_register.html")

def student_register_code(request):
    if request.method == "POST":
        full_name = request.POST.get("student_name")
        mobile = request.POST.get("mobile")
        school_name = request.POST.get("s_name")
        student_class = request.POST.get("student_class")
        father_name = request.POST.get("father_name")
        pin_code = request.POST.get("pin_code")
        district = request.POST.get("district")
        address = request.POST.get("address")
        username = request.POST.get("username")
        password = request.POST.get("password")

        if Student.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('student_register')

        school_obj, _ = School.objects.get_or_create(name=school_name)
        class_obj, _ = ClassModel.objects.get_or_create(name=student_class, school=school_obj)

        Student.objects.create(
            full_name=full_name,
            father_name=father_name,
            mobile=mobile,
            school=school_obj,
            class_name=class_obj,
            pin_code=pin_code,
            district=district,
            address=address,
            username=username,
            password=password  # simple password
        )
        messages.success(request, "Student registered successfully")
        return redirect('student_login')
    return redirect('student_register')

def student_login(request):
    return render(request, "student/student_login.html")


def student_login_code(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            student = Student.objects.get(username=username)

            if password == student.password:
                request.session['student_id'] = student.id
                request.session['student_name'] = student.full_name
                return redirect('student_dashboard')  # ✅ Correct

            else:
                messages.error(request, "Invalid password")

        except Student.DoesNotExist:
            messages.error(request, "Student not found")

        return redirect('student_login')  # ✅ Correct

    return redirect('student_login')

@student_login_required
def student_dashboard(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('student_login')

    student = Student.objects.get(id=student_id)
    student_tests = StudentTest.objects.filter(student=student)

    total_tests = student_tests.count()
    attempted_tests = student_tests.filter(completed=True).count()
    pending_tests = student_tests.filter(completed=False).count()
    progress_percent = int((attempted_tests / total_tests * 100) if total_tests else 0)

    return render(request, 'student/student_dashboard.html', {
        'student_tests': student_tests,       # <--- Add this
        'total_tests': total_tests,
        'attempted_tests': attempted_tests,
        'pending_tests': pending_tests,
        'progress_percent': progress_percent
    })

@student_login_required
def total_test(request):
    student_id = request.session.get('student_id')
    student = get_object_or_404(Student, id=student_id)

    # All tests assigned to this student via StudentTest
    student_tests = StudentTest.objects.filter(student=student).select_related('test')
    tests = [st.test for st in student_tests]

    # Attempted test IDs
    attempted_test_ids = [st.test.id for st in student_tests if st.completed]

    return render(request, "student/total_test.html", {
        "tests": tests,
        "attempted_test_ids": attempted_test_ids
    })

@student_login_required
def start_test(request, test_id):

    student_id = request.session.get('student_id')
    student = get_object_or_404(Student, id=student_id)

    student_test = get_object_or_404(
        StudentTest,
        student=student,
        test_id=test_id
    )

    test = student_test.test
    questions = test.questions.all()

    # Reset if previously completed
    if student_test.completed:
        student_test.completed = False
        student_test.start_time = None
        student_test.end_time = None
        student_test.score = 0
        student_test.save()

    # ⏳ Start timer if first time
    if not student_test.start_time:
        student_test.start_time = timezone.now()
        student_test.end_time = timezone.now() + timedelta(minutes=int(test.duration))
        student_test.save()

    if timezone.now() > student_test.end_time:
        student_test.completed = True
        student_test.save()
        return redirect('result_detail', student_test_id=student_test.id)

    if request.method == "POST":
        score = 0

        for question in questions:
            selected = request.POST.get(str(question.id))

            if selected and selected.strip().upper() == question.correct_answer.strip().upper():
                score += int(question.marks)

        student_test.score = score
        student_test.completed = True
        student_test.save()

        return redirect('result_detail', student_test_id=student_test.id)

    remaining_time = int(
        (student_test.end_time - timezone.now()).total_seconds()
    )

    return render(request, "student/start_test.html", {
        "test": test,
        "questions": questions,
        "remaining_time": remaining_time
    })

@student_login_required  # use your session-based decorator
def attempted(request):

    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('student_login')

    student = get_object_or_404(Student, id=student_id)

    attempted_tests = StudentTest.objects.filter(
        student=student,
        completed=True
    ).select_related('test')

    return render(request, "student/attempted.html", {
        "attempted_tests": attempted_tests
    })
@student_login_required  # your session-based decorator
def pending(request):

    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('student_login')

    student = get_object_or_404(Student, id=student_id)

    pending_tests = StudentTest.objects.filter(
        student=student,
        completed=False
    ).select_related('test')

    return render(request, "student/pending.html", {
        "pending_tests": pending_tests
    })

@student_login_required
def results(request):

    student_id = request.session.get('student_id')

    if not student_id:
        return redirect('student_login')

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return redirect('student_login')

    results = StudentTest.objects.filter(
        student=student,
        completed=True
    ).select_related('test')

    return render(request, "student/results.html", {
        "results": results
    })


@student_login_required
def result_detail(request, student_test_id):

    student_id = request.session.get('student_id')
    student = get_object_or_404(Student, id=student_id)

    student_test = get_object_or_404(
        StudentTest,
        id=student_test_id,
        student=student
    )

    test = student_test.test
    questions = test.questions.all()

    total_questions = questions.count()

    total_marks = 0
    for q in questions:
        total_marks += int(q.marks)

    score = student_test.score

    # simple calculation
    correct = int(score / questions.first().marks) if questions.exists() else 0
    wrong = total_questions - correct
    attempted = correct + wrong

    context = {
        "student_test": student_test,
        "questions": questions,
        "total_questions": total_questions,
        "attempted": attempted,
        "correct": correct,
        "wrong": wrong,
        "total_marks": total_marks,
        "score": score
    }

    return render(request, "student/result_detail.html", context)

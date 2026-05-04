from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpRequest
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from .models import Assessment, Question, Choice, Submission, Answer
from .forms import AssessmentForm, QuestionForm, ChoiceForm
from nests.models import Nest, NestMembership
from django.db.models import Sum

# Create your views here.


def _require_auth(request: HttpRequest, message: str):
    messages.warning(request, message, 'alert-warning')
    return redirect_to_login(request.get_full_path())


def _deny_access(request: HttpRequest, message: str, redirect_to: str, **kwargs):
    messages.warning(request, message, 'alert-warning')
    return redirect(redirect_to, **kwargs)


def _nest_context(nest: Nest, user):
    membership = nest.membership_for(user)
    pending_membership = nest.memberships.filter(
        user=user,
        status=NestMembership.Status.PENDING,
    ).first()
    return {
        'membership': membership,
        'pending_membership': pending_membership,
        'can_manage': nest.is_nest_staff(user) or nest.is_site_staff(user),
        'is_nest_staff': nest.is_nest_staff(user) or nest.is_site_staff(user),
    }


def _has_manage_access(nest: Nest, user) -> bool:
    return nest.is_nest_staff(user) or nest.is_site_staff(user)

def assessment_page_view(request: HttpRequest, nest_id):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to access assessments.')

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    context = _nest_context(nest, request.user)

    has_access = context['is_nest_staff'] or (context['membership'] is not None)
    if not has_access:
        return _deny_access(request, 'You must be an active nest member to access assessments.', 'nests:nest_detail', nest_id=nest.pk)

    assessments = Assessment.objects.filter(nest=nest)

    if request.user.is_authenticated and not context['is_nest_staff']:
        submissions = Submission.objects.filter(student=request.user, assessment__nest=nest)
        submissions_map = {s.assessment_id: s.score for s in submissions}

        for assessment in assessments:
            assessment.student_score = submissions_map.get(assessment.id)
    else:
        for assessment in assessments:
            assessment.student_score = None

    total_score = (
        Submission.objects
        .filter(student=request.user, assessment__nest=nest)
        .aggregate(total=Sum('score'))['total'] or 0
    )

    context.update({
        'assessments': assessments,
        'nest': nest,
        'total_score': total_score,
    })

    return render(request, 'assessments/assessment_page.html', context)

def assessment_create_view(request: HttpRequest, nest_id):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to create assessments.')
    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not _has_manage_access(nest, request.user):
        return _deny_access(request, 'You do not have permission to create assessments.', 'assessments:assessment_page_view', nest_id=nest.pk)

    if request.method == 'POST':
        form = AssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.nest = nest
            assessment.created_by = request.user
            assessment.save()
            return redirect('assessments:assessment_page_view', nest_id=nest.id)
    else:
        form = AssessmentForm()
    return render(request, 'assessments/assessments_create.html', {'form': form, 'nest': nest})

def assessment_update_view(request: HttpRequest, nest_id, pk):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to update assessments.')
    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not _has_manage_access(nest, request.user):
        return _deny_access(request, 'You do not have permission to update assessments.', 'assessments:assessment_page_view', nest_id=nest.pk)
    assessment = get_object_or_404(Assessment, pk=pk, nest=nest)

    if request.method == 'POST':
        form = AssessmentForm(request.POST, instance=assessment)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.created_by = request.user
            assessment.nest = nest
            form.save()
            return redirect('assessments:assessment_page_view', nest_id=nest.id)
    else:
        form = AssessmentForm(instance=assessment)
    return render(request, 'assessments/assessments_update.html', {'form': form, 'assessment': assessment, 'nest': nest})

def assessment_delete_view(request: HttpRequest, nest_id, pk):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to delete assessments.')
    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not _has_manage_access(nest, request.user):
        return _deny_access(request, 'You do not have permission to delete assessments.', 'assessments:assessment_page_view', nest_id=nest.pk)
    assessment = get_object_or_404(Assessment, pk=pk, nest=nest)

    if request.method == 'POST':
        assessment.delete()
        return redirect('assessments:assessment_page_view', nest_id=nest.id)
    return render(request, 'assessments/assessments_delete.html', {'assessment': assessment, 'nest': nest})

def question_create_view(request: HttpRequest, nest_id, pk):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to create questions.')
    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not _has_manage_access(nest, request.user):
        return _deny_access(request, 'You do not have permission to create questions.', 'assessments:assessment_page_view', nest_id=nest.pk)
    assessment = get_object_or_404(Assessment, pk=pk, nest=nest, created_by=request.user)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.assessment = assessment
            question.save()
            return redirect('assessments:assessment_detail_view', nest_id=nest.id, pk=assessment.pk)
    else:
        form = QuestionForm()
    return render(request, 'assessments/questions_create.html', {'form': form, 'assessment': assessment, 'nest': nest})

def question_update_view(request: HttpRequest, nest_id, pk):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to update questions.')
    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not _has_manage_access(nest, request.user):
        return _deny_access(request, 'You do not have permission to update questions.', 'assessments:assessment_page_view', nest_id=nest.pk)
    question = get_object_or_404(Question, pk=pk, assessment__nest=nest, assessment__created_by=request.user)

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save(commit=False)
            question.save()
            return redirect('assessments:assessment_detail_view', nest_id=nest.id, pk=question.assessment.pk)
    else:
        form = QuestionForm(instance=question)
    return render(request, 'assessments/questions_update.html', {'form': form, 'question': question, 'nest': nest})

def question_delete_view(request: HttpRequest, nest_id, pk):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to delete questions.')
    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not _has_manage_access(nest, request.user):
        return _deny_access(request, 'You do not have permission to delete questions.', 'assessments:assessment_page_view', nest_id=nest.pk)
    question = get_object_or_404(Question, pk=pk, assessment__nest=nest, assessment__created_by=request.user)

    if request.method == 'POST':
        question.delete()
        return redirect('assessments:assessment_detail_view', nest_id=nest.id, pk=question.assessment.pk)
    return render(request, 'assessments/questions_delete.html', {'question': question, 'nest': nest})

def assessment_detail_view(request: HttpRequest, nest_id, pk):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to view assessments.')

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    context = _nest_context(nest, request.user)

    has_access = context['is_nest_staff'] or (context['membership'] is not None)
    if not has_access:
        return _deny_access(request, 'You must be an active nest member to access assessments.', 'nests:nest_detail', nest_id=nest.pk)

    assessment = get_object_or_404(Assessment, pk=pk, nest=nest)

    # إذا الطالب سبق وسلّم، امنعه من دخول الاختبار مرة ثانية
    if request.user.is_authenticated and not context['is_nest_staff']:
        already_submitted = Submission.objects.filter(
            student=request.user,
            assessment=assessment
        ).exists()
        if already_submitted:
            return redirect("assessments:assessment_page_view", nest_id=nest.id)

    questions = assessment.questions.all()
    context.update({
        'assessment': assessment,
        'questions': questions,
        'nest': nest,
    })
    return render(request, 'assessments/assessment_detail.html', context)

def choice_create_view(request, nest_id, question_id):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to create choices.')
    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not _has_manage_access(nest, request.user):
        return _deny_access(request, 'You do not have permission to create choices.', 'assessments:assessment_page_view', nest_id=nest.pk)
    question = get_object_or_404(Question, pk=question_id, assessment__nest=nest, assessment__created_by=request.user)

    if request.method == "POST":
        form = ChoiceForm(request.POST)
        if form.is_valid():
            choice = form.save(commit=False)
            choice.question = question
            if choice.is_correct:
                question.choices.update(is_correct=False)
            choice.save()
            return redirect("assessments:assessment_detail_view", nest_id=nest.id, pk=question.assessment.id)
    else:
        form = ChoiceForm()
    return render(request, "assessments/choice_create.html", {"form": form, "question": question, "nest": nest})

def choice_update_view(request, nest_id, choice_id):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to update choices.')
    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not _has_manage_access(nest, request.user):
        return _deny_access(request, 'You do not have permission to update choices.', 'assessments:assessment_page_view', nest_id=nest.pk)
    choice = get_object_or_404(Choice, pk=choice_id, question__assessment__nest=nest, question__assessment__created_by=request.user)

    if request.method == "POST":
        form = ChoiceForm(request.POST, instance=choice)
        if form.is_valid():
            updated_choice = form.save(commit=False)
            if updated_choice.is_correct:
                choice.question.choices.update(is_correct=False)
            updated_choice.save()
            return redirect("assessments:assessment_detail_view", nest_id=nest.id, pk=choice.question.assessment.id)
    else:
        form = ChoiceForm(instance=choice)
    return render(request, "assessments/choice_update.html", {"form": form, "choice": choice, "nest": nest})

def choice_delete_view(request, nest_id, choice_id):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to delete choices.')
    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not _has_manage_access(nest, request.user):
        return _deny_access(request, 'You do not have permission to delete choices.', 'assessments:assessment_page_view', nest_id=nest.pk)
    choice = get_object_or_404(Choice, pk=choice_id, question__assessment__nest=nest, question__assessment__created_by=request.user)

    if request.method == "POST":
        choice.delete()
        return redirect("assessments:assessment_detail_view", nest_id=nest.id, pk=choice.question.assessment.id)
    return render(request, "assessments/choice_delete.html", {"choice": choice, "nest": nest})

def take_assessment_view(request: HttpRequest, nest_id, pk):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to take assessments.')

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    context = _nest_context(nest, request.user)

    has_access = context['is_nest_staff'] or (context['membership'] is not None)
    if not has_access:
        return _deny_access(request, 'You must be an active nest member to access assessments.', 'nests:nest_detail', nest_id=nest.pk)

    assessment = get_object_or_404(Assessment, pk=pk, nest=nest)

    if request.user.is_authenticated and not context['is_nest_staff']:
        if Submission.objects.filter(student=request.user, assessment=assessment).exists():
            submission = Submission.objects.filter(
                student=request.user,
                assessment=assessment
            ).latest("id")
            return redirect(
                "assessments:submission_result_view",
                nest_id=nest.id,
                submission_id=submission.id
            )

    if request.method == "POST":
        submission = Submission.objects.create(
            assessment=assessment,
            student=request.user
        )

        score = 0
        for question in assessment.questions.all():
            if question.question_type == "mcq":
                choice_id = request.POST.get(f"question_{question.id}")
                if choice_id:
                    choice = Choice.objects.get(id=choice_id)
                    is_correct = choice.is_correct
                    if is_correct:
                        score += question.points

                    Answer.objects.create(
                        submission=submission,
                        question=question,
                        selected_choice=choice,
                        is_correct=is_correct
                    )

            elif question.question_type == "text":
                text_answer = request.POST.get(f"question_{question.id}", "")
                Answer.objects.create(
                    submission=submission,
                    question=question,
                    text_answer=text_answer
                )

        submission.score = score
        submission.save()

        if request.POST.get("auto_submit") == "1":
            return redirect(
                "assessments:assessment_page_view",
                nest_id=nest.id,
            )

        return redirect(
            "assessments:submission_result_view",
            nest_id=nest.id,
            submission_id=submission.id
        )

    context.update({
        "assessment": assessment,
        "nest": nest,
    })
    return render(request, "assessments/take_assessment.html", context)
def submission_result_view(request, nest_id, submission_id):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to view results.')

    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    context = _nest_context(nest, request.user)

    has_access = context['is_nest_staff'] or (context['membership'] is not None)
    if not has_access:
        return _deny_access(request, 'You must be an active nest member to access assessments.', 'nests:nest_detail', nest_id=nest.pk)

    # الطالب يشوف نتيجته، المعلم يشوف أي Submission داخل Nest
    if context['is_nest_staff']:
        submission = get_object_or_404(Submission, id=submission_id, assessment__nest=nest)
    else:
        submission = get_object_or_404(Submission, id=submission_id, student=request.user, assessment__nest=nest)

    if request.method == "POST" and context['is_nest_staff']:
        for answer in submission.answers.all():
            value = request.POST.get(f"answer_{answer.id}")
            if value == "correct":
                answer.is_correct = True
            elif value == "wrong":
                answer.is_correct = False
            answer.save()

        total_score = 0
        for answer in submission.answers.all():
            if answer.is_correct:
                total_score += answer.question.points

        submission.score = total_score
        submission.save()
        return redirect(
            "assessments:assessment_submissions_view",
            nest_id=nest_id,
            pk=submission.assessment.id,
        )

    context.update({
        "submission": submission,
        "nest": nest,
    })
    return render(request, "assessments/submission_result.html", context)

def assessment_submissions_view(request, nest_id, pk):
    if not request.user.is_authenticated:
        return _require_auth(request, 'You must be signed in to view submissions.')
    nest = get_object_or_404(Nest, pk=nest_id, status=Nest.Status.APPROVED)
    if not _has_manage_access(nest, request.user):
        return _deny_access(request, 'You do not have permission to view submissions.', 'assessments:assessment_page_view', nest_id=nest.pk)
    assessment = get_object_or_404(Assessment, pk=pk, nest=nest)
    submissions = assessment.submissions.all()
    return render(request, 'assessments/assessment_submissions.html', {
        'assessment': assessment,
        'submissions': submissions,
        'nest': nest
    })


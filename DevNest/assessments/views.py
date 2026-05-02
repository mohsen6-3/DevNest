from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpRequest
from .models import Assessment, Question, Choice, Submission, Answer
from .forms import AssessmentForm, QuestionForm, ChoiceForm
from nests.models import Nest
from django.db.models import Sum

# Create your views here.

def assessment_page_view(request: HttpRequest, nest_id):
    nest = get_object_or_404(Nest, id=nest_id)
    assessments = Assessment.objects.filter(nest=nest)
    total_score = (
        Submission.objects
        .filter(student=request.user, assessment__nest=nest)
        .aggregate(total=Sum('score'))['total'] or 0
    )
    user = request.user
    return render(request, 'assessments/assessment_page.html', {
        'assessments': assessments,
        'user': user,
        'nest': nest,
        'total_score': total_score
    })

def assessment_create_view(request: HttpRequest, nest_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    nest = get_object_or_404(Nest, id=nest_id)

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
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    nest = get_object_or_404(Nest, id=nest_id)
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
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    nest = get_object_or_404(Nest, id=nest_id)
    assessment = get_object_or_404(Assessment, pk=pk, nest=nest)

    if request.method == 'POST':
        assessment.delete()
        return redirect('assessments:assessment_page_view', nest_id=nest.id)
    return render(request, 'assessments/assessments_delete.html', {'assessment': assessment, 'nest': nest})

def question_create_view(request: HttpRequest, nest_id, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    nest = get_object_or_404(Nest, id=nest_id)
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
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    nest = get_object_or_404(Nest, id=nest_id)
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
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    nest = get_object_or_404(Nest, id=nest_id)
    question = get_object_or_404(Question, pk=pk, assessment__nest=nest, assessment__created_by=request.user)

    if request.method == 'POST':
        question.delete()
        return redirect('assessments:assessment_detail_view', nest_id=nest.id, pk=question.assessment.pk)
    return render(request, 'assessments/questions_delete.html', {'question': question, 'nest': nest})

def assessment_detail_view(request: HttpRequest, nest_id, pk):
    nest = get_object_or_404(Nest, id=nest_id)
    assessment = get_object_or_404(Assessment, pk=pk, nest=nest)
    questions = assessment.questions.all()
    return render(request, 'assessments/assessment_detail.html', {
        'assessment': assessment,
        'questions': questions,
        'nest': nest
    })

def choice_create_view(request, nest_id, question_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    nest = get_object_or_404(Nest, id=nest_id)
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
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    nest = get_object_or_404(Nest, id=nest_id)
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
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    nest = get_object_or_404(Nest, id=nest_id)
    choice = get_object_or_404(Choice, pk=choice_id, question__assessment__nest=nest, question__assessment__created_by=request.user)

    if request.method == "POST":
        choice.delete()
        return redirect("assessments:assessment_detail_view", nest_id=nest.id, pk=choice.question.assessment.id)
    return render(request, "assessments/choice_delete.html", {"choice": choice, "nest": nest})

def take_assessment_view(request, nest_id, pk):
    nest = get_object_or_404(Nest, id=nest_id)
    assessment = get_object_or_404(Assessment, pk=pk, nest=nest)

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
        return redirect("assessments:submission_result_view", nest_id=nest.id, submission_id=submission.id)

    return render(request, "assessments/take_assessment.html", {"assessment": assessment, "nest": nest})

def submission_result_view(request, nest_id, submission_id):
    nest = get_object_or_404(Nest, id=nest_id)
    submission = get_object_or_404(Submission, id=submission_id, student=request.user, assessment__nest=nest)
    return render(request, "assessments/submission_result.html", {"submission": submission, "nest": nest})


from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse,HttpRequest
from .models import Assessment, Question, Choice, Submission, Answer
from .forms import AssessmentForm ,QuestionForm, ChoiceForm

# Create your views here.

def assessment_page_view(request:HttpRequest):
    assessments = Assessment.objects.all()
    user = request.user

    return render(request, 'assessments/assessment_page.html', {'assessments': assessments  , 'user': user})

def assessment_create_view(request:HttpRequest):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    if request.method == 'POST':
        form = AssessmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('assessments:assessment_page_view')  # Replace with the actual URL name
    else:
        form = AssessmentForm()
    return render(request, 'assessments/assessments_create.html', {'form': form})

def assessment_update_view(request:HttpRequest, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    assessment = Assessment.objects.get(pk=pk)
    if request.method == 'POST':
        form = AssessmentForm(request.POST, instance=assessment)
        if form.is_valid():
            form.save()
            return redirect('assessments:assessment_page_view')  # Replace with the actual URL name
    else:
        form = AssessmentForm(instance=assessment)
    return render(request, 'assessments/assessments_update.html', {'form': form, 'assessment': assessment})

def assessment_delete_view(request:HttpRequest, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    assessment = Assessment.objects.get(pk=pk)
    if request.method == 'POST':
        assessment.delete()
        return redirect('assessments:assessment_page_view')  # Replace with the actual URL name
    return render(request, 'assessments/assessments_delete.html', {'assessment': assessment})

def question_create_view(request:HttpRequest, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    assessment = Assessment.objects.get(pk=pk ,created_by=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.assessment = assessment
            question.save()
            return redirect('assessments:assessment_detail_view', pk=assessment.pk)
    else:
        form = QuestionForm()
    return render(request, 'assessments/questions_create.html', {'form': form, 'assessment': assessment})
def question_update_view(request:HttpRequest, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    question = Question.objects.get(pk=pk, assessment__created_by=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('assessments:assessment_detail_view', pk=question.assessment.pk)
    else:
        form = QuestionForm(instance=question)
    return render(request, 'assessments/questions_update.html', {'form': form, 'question': question})

def assessment_detail_view(request:HttpRequest, pk):
    assessment = Assessment.objects.get(pk=pk)
    questions = assessment.questions.all()
    return render(request, 'assessments/assessment_detail.html', {'assessment': assessment, 'questions': questions})

def choice_create_view(request, question_id):
    question = get_object_or_404(Question, pk=question_id, assessment__created_by=request.user)
    if request.method == "POST":
        form = ChoiceForm(request.POST)
        if form.is_valid():
            choice = form.save(commit=False)
            choice.question = question
            if choice.is_correct:
                question.choices.update(is_correct=False)  
            choice.save()
            return redirect("assessments:assessment_detail_view", pk=question.assessment.id)
    else:
        form = ChoiceForm()
    return render(request, "assessments/choice_create.html", {"form": form, "question": question})

def choice_update_view(request, choice_id):
    choice = get_object_or_404(Choice, pk=choice_id, question__assessment__created_by=request.user)
    if request.method == "POST":
        form = ChoiceForm(request.POST, instance=choice)
        if form.is_valid():
            updated_choice = form.save(commit=False)
            if updated_choice.is_correct:
                choice.question.choices.update(is_correct=False)  
            updated_choice.save()
            return redirect("assessments:assessment_detail_view", pk=choice.question.assessment.id)
    else:
        form = ChoiceForm(instance=choice)
    return render(request, "assessments/choice_update.html", {"form": form, "choice": choice})

def take_assessment_view(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)

    if request.method == "POST":
        submission = Submission.objects.create(
            assessment=assessment,
            student=request.user
        )

        score = 0
        for question in assessment.questions.all():
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

        submission.score = score
        submission.save()
        return redirect("assessments:submission_result_view", submission_id=submission.id)

    return render(request, "assessments/take_assessment.html", {"assessment": assessment})

def submission_result_view(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id, student=request.user)
    return render(request, "assessments/submission_result.html", {"submission": submission})
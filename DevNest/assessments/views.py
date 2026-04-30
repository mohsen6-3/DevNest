from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse,HttpRequest
from .models import Assessment, Question, Choice
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
            choice.save()
            return redirect("assessments:assessment_detail_view", pk=question.assessment.id)
    else:
        form = ChoiceForm()
    return render(request, "assessments/choice_create.html", {"form": form, "question": question})
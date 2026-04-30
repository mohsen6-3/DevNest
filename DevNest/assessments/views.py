from django.shortcuts import render, redirect
from django.http import HttpResponse,HttpRequest
from .models import Assessment, Question, Choice, Submission, Answer
from .forms import AssessmentForm
# Create your views here.

def assessment_page_view(request:HttpRequest):
    assessments = Assessment.objects.all()
    return render(request, 'assessments/assessment_page.html', {'assessments': assessments})

def assessment_create_view(request:HttpRequest):
    if request.method == 'POST':
        form = AssessmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('assessments:assessment_page_view')  # Replace with the actual URL name
    else:
        form = AssessmentForm()
    return render(request, 'assessments/assessments_create.html', {'form': form})

def assessment_update_view(request:HttpRequest, pk):
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
    assessment = Assessment.objects.get(pk=pk)
    if request.method == 'POST':
        assessment.delete()
        return redirect('assessments:assessment_page_view')  # Replace with the actual URL name
    return render(request, 'assessments/assessments_delete.html', {'assessment': assessment})
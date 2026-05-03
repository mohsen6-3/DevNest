from django.db import models
from django.contrib.auth.models import User

from nests.models import Nest



class Assessment(models.Model):
    TYPE_CHOICES = [
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        # ('coding', 'Coding'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assessment_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    points = models.PositiveIntegerField(default=0)
    due_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name='created_assessments')
    created_at = models.DateTimeField(auto_now_add=True)
    nest = models.ForeignKey(Nest, on_delete=models.CASCADE, related_name='assessments', null=True, blank=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('text', 'Text Answer'),
        # ('code', 'Coding'),
    ]

    assessment = models.ForeignKey(Assessment,on_delete=models.CASCADE,related_name='questions')

    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    points = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.assessment.title} - {self.text[:40]}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE,related_name='choices')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Submission(models.Model):
    assessment = models.ForeignKey(Assessment,on_delete=models.CASCADE,related_name='submissions')

    student = models.ForeignKey(User,on_delete=models.CASCADE,related_name='submissions')

    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0)

    def __str__(self):
        return f"{self.student.username} - {self.assessment.title}"


class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')

    question = models.ForeignKey(Question,on_delete=models.CASCADE,related_name='answers')

    # للـMCQ
    selected_choice = models.ForeignKey(Choice,on_delete=models.SET_NULL,null=True,blank=True,related_name='selected_answers')

    # للأسئلة النصية
    text_answer = models.TextField(blank=True)

    # للأسئلة البرمجية
    code_answer = models.TextField(blank=True)

    is_correct = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"{self.submission.student.username} - {self.question.id}"
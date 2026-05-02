from django import forms
from .models import Title, Unit, Topic, VideoContent, FileContent, ImageContent, TextContent, LinkContent


class TitleForm(forms.ModelForm):
    class Meta:
        model = Title
        fields = ['name', 'description', 'sort_order', 'is_published']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'description', 'sort_order', 'is_published']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name', 'sort_order', 'status', 'due_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class VideoContentForm(forms.ModelForm):
    class Meta:
        model = VideoContent
        fields = ['video_title', 'video_file', 'thumbnail', 'duration', 'sort_order']
        widgets = {
            'video_title': forms.TextInput(attrs={'class': 'form-control'}),
            'video_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'video/*'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duration in seconds'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class FileContentForm(forms.ModelForm):
    class Meta:
        model = FileContent
        fields = ['file_name', 'file', 'sort_order']
        widgets = {
            'file_name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ImageContentForm(forms.ModelForm):
    class Meta:
        model = ImageContent
        fields = ['image_title', 'image', 'alt_text', 'sort_order']
        widgets = {
            'image_title': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Describe the image'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TextContentForm(forms.ModelForm):
    class Meta:
        model = TextContent
        fields = ['text_title', 'body', 'format', 'sort_order']
        widgets = {
            'text_title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'format': forms.Select(attrs={'class': 'form-select'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class LinkContentForm(forms.ModelForm):
    class Meta:
        model = LinkContent
        fields = ['display_text', 'url', 'sort_order']
        widgets = {
            'display_text': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
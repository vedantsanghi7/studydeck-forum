from django import forms
from .models import Thread, Reply, Report, Category, Course, Resource


class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['title', 'content', 'category', 'course', 'resource']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter thread title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter your question or discussion...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'course': forms.Select(attrs={
                'class': 'form-control'
            }),
            'resource': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].required = False
        self.fields['course'].queryset = Course.objects.all()
        self.fields['course'].empty_label = 'Select a course (optional)'
        self.fields['resource'].required = False
        self.fields['resource'].queryset = Resource.objects.all()
        self.fields['resource'].empty_label = 'Select a resource (optional)'


class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter your reply...'
            }),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['thread', 'reply', 'reason']
        widgets = {
            'thread': forms.HiddenInput(),
            'reply': forms.HiddenInput(),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Please explain why you are reporting this content...'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        thread = cleaned_data.get('thread')
        reply = cleaned_data.get('reply')
        
        if not thread and not reply:
            raise forms.ValidationError("Either thread or reply must be specified.")
        if thread and reply:
            raise forms.ValidationError("Cannot report both thread and reply at the same time.")
        
        return cleaned_data

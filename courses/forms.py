from .models import Course
from django import forms
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm, UserChangeForm, UserCreationForm
from django.contrib.auth import get_user_model
User = get_user_model()
from .models import UserProfile
from .models import CustomUser, Lesson
from django.conf import settings

    
class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'birth_date']  # Добавьте ваши поля
        
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Имя пользователя или Email')

class UserUpdateForm(forms.ModelForm):

    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'avatar']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class CourseFilterForm(forms.Form):
    category = forms.ChoiceField(
        label='Категория',
        required=False,
        choices=Course.CATEGORY_CHOICES  # Теперь атрибут существует
    )
class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'lesson_type', 'content', 'video_url', 'duration']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }
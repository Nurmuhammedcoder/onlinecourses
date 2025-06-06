from django.db import models
from django.contrib.auth.models import  Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import os
import uuid

def custom_upload_to(instance, filename):
    # Генерируем уникальное имя файла
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('courses/images', new_filename)

class CustomUser(AbstractUser):
    avatar = models.ImageField(
        upload_to='avatars/', 
        blank=True,
        default='avatars/default.png',
        verbose_name='Аватар'
    )
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True)
    
    # Добавляем поле для хранения курсов, на которые записан пользователь
    courses_joined = models.ManyToManyField(
        'courses.Course',  # Убедитесь, что имя приложения указано верно
        blank=True,
        related_name='students',
    )

    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    groups = models.ManyToManyField(
        'auth.Group',
        related_name="customuser_set",
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="customuser_set",
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )
    
    # Исправленные отношения для групп и разрешений
    
class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        unique=True  # Важная строка
    )
    # Add your profile fields here
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    unique=True
    def __str__(self):
        return f'Профиль {self.user.username}'
    def get_interests_list(self):
        return [i.strip().lower() for i in self.interests.split(',')] if self.interests else []
    

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(
        upload_to=custom_upload_to,  # Используем кастомную функцию
        max_length=500,
        verbose_name='Изображение'
    )
    CATEGORY_CHOICES = [  # ← 4 пробела отступа
        ('programming', 'Programming'),  # ← 8 пробелов (двойной отступ)
        ('design', 'UI/UX Design'),
        ('business', 'Business'),
    ] 
    slug = models.SlugField(unique=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='programming'
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use string reference
        on_delete=models.CASCADE,
        related_name='courses_taught'
    )
    
    rating = models.FloatField(
        verbose_name='Рейтинг',
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text='Рейтинг от 0 до 5 звезд'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['rating']),  # Теперь это поле существует
            models.Index(fields=['created_at']),
        ]
    @property
    def progress(self):
        # Пример расчета прогресса
        total_lessons = self.lessons.count()
        completed = self.lessons.filter(is_completed=True).count()
        return int((completed / total_lessons) * 100) if total_lessons else 0
    

class VideoLesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='video_lessons'  # Используйте это имя для связи
    )
    title = models.CharField(max_length=200)
    video_url = models.URLField()
    
    def __str__(self):
        return self.title
    

class UserCourseProgress(models.Model):
    user = models.ForeignKey(
    CustomUser,
    on_delete=models.CASCADE
)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    progress = models.PositiveIntegerField(default=0) 
    completed_lessons = models.ManyToManyField(VideoLesson, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'course')
        verbose_name_plural = "User Progress"

    def progress_percentage(self):
        total_lessons = self.course.video_lessons.count()
        completed = self.completed_lessons.count()
        return round((completed / total_lessons) * 100) if total_lessons > 0 else 0

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    

class UserAchievement(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    title = models.CharField(max_length=100)
    date_achieved = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"
    

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save() 





class AboutPage(models.Model):
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "About Page"

    def __str__(self):
        return f"About Page ({self.updated_at})"

class Lesson(models.Model):
    LESSON_TYPES = [
        ('video', 'Видеоурок'),
        ('text', 'Текстовый урок'),
        ('quiz', 'Тест'),
    ]
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    title = models.CharField(max_length=200)
    lesson_type = models.CharField(
        max_length=10, 
        choices=LESSON_TYPES,
        default='video'
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Порядковый номер урока"
    )
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    duration = models.DurationField(
        blank=True,
        null=True,
        help_text="Длительность видео (HH:MM:SS)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return f"{self.order}. {self.title} ({self.get_lesson_type_display()})"

class YourModel(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    bio = models.TextField(verbose_name='Биография')
    experience = models.PositiveIntegerField(verbose_name='Опыт работы (лет)')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}"



from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Teacher, AboutPage, Course, VideoLesson, UserProfile,  UserCourseProgress, CustomUser, UserAchievement, Lesson
from django.conf import settings
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
User = settings.AUTH_USER_MODEL
User = get_user_model()

class UserProfileInline(admin.StackedInline):  # ← Измените имя класса
    model = UserProfile  # ← Исправлено на UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'is_teacher', 'is_student')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('email',)}),
        ('Права', {'fields': ('is_teacher', 'is_student', 'is_active', 'is_staff', 'is_superuser')}),
    )
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)  # Теперь ProfileInline определен
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio')  # Пример полей


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience')
    search_fields = ('user__username',)

@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not AboutPage.objects.exists()

@admin.register(UserCourseProgress)
class UserCourseProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'progress_percent')  # Используем существующее поле
    
    def progress_percent(self, obj):
        return f"{obj.progress}%"
    progress_percent.short_description = 'Прогресс'
@admin.register(UserAchievement)  # Регистрируем новую модель
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'date_achieved')
@admin.register(VideoLesson)
class VideoLessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course')

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1
    fields = ('title', 'lesson_type', 'order', 'content', 'video_url', 'duration')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ('title', 'instructor', 'category', 'created_at')
    search_fields = ('title', 'description')


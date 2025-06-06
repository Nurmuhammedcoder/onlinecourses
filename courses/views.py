from django.shortcuts import render, redirect, get_object_or_404 
from .models import Course, VideoLesson, Teacher, AboutPage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from .models import Course, Lesson
from .forms import LessonForm
from django.contrib.auth.decorators import login_required
from .forms import( 
    UserRegistrationForm, 
    UserLoginForm, 
    UserUpdateForm, 
    UserProfileUpdateForm,
    CourseFilterForm
)
from django.contrib import messages
from .forms import CourseFilterForm 
from .models import UserCourseProgress  # Добавьте эту строку
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from django.db.models import Count, Case, When, IntegerField, Q
from django.contrib.postgres.aggregates import ArrayAgg
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from django.contrib.auth import login


def home(request):
    featured_courses = Course.objects.all()[:3]
    context = {
        'featured_courses': Course.objects.order_by('-rating')[:3],
        'user_progress': None,
        'recommended_courses': []
    }

    if request.user.is_authenticated:
        # Прогресс пользователя с оптимизацией запроса
        context['user_progress'] = UserCourseProgress.objects.filter(
            user=request.user
        ).select_related('course__category').prefetch_related('course__tags')[:5]

        # Расширенная система рекомендаций
        try:
            profile = request.user.profile
            interests = profile.get_interests_list()  # Метод модели Profile
            
            # 1. Рекомендации на основе интересов
            interest_courses = Course.objects.annotate(
                match_score=Count(
                    Case(
                        When(category__in=interests, then=1),
                        output_field=IntegerField()
                    )
                )
            ).exclude(
                usercourseprogress__user=request.user
            ).order_by('-match_score', '-created_at')[:10]

            # 2. Рекомендации на основе похожих пользователей (коллаборативная фильтрация)
            user_vector = Course.objects.annotate(
                taken=Case(
                    When(usercourseprogress__user=request.user, then=1),
                    default=0,
                    output_field=IntegerField()
                )
            ).values_list('taken', flat=True)

            all_users = User.objects.exclude(id=request.user.id).annotate(
                course_vector=ArrayAgg(
                    Case(
                        When(usercourseprogress__course__isnull=False, then=1),
                        default=0,
                        output_field=IntegerField()
                    )
                )
            )[:100]  # Лимит для производительности

            # Вычисление косинусного сходства
            similarities = []
            for user in all_users:
                other_vector = user.course_vector
                if len(other_vector) == len(user_vector):
                    sim = cosine_similarity([user_vector], [other_vector])[0][0]
                    similarities.append((sim, user))

            # Сортировка по схожести
            similarities.sort(reverse=True, key=lambda x: x[0])
            top_users = [user for _, user in similarities[:5]]

            # Сбор курсов от похожих пользователей
            collaborative_courses = Course.objects.filter(
                usercourseprogress__user__in=top_users
            ).exclude(
                usercourseprogress__user=request.user
            ).annotate(
                popularity=Count('usercourseprogress')
            ).order_by('-popularity')[:10]

            # 3. Гибридная рекомендация (объединение подходов)
            all_recommendations = list(interest_courses) + list(collaborative_courses)
            np.random.shuffle(all_recommendations)  # Добавляем элемент случайности
            
            context['recommended_courses'] = all_recommendations[:3]

        except AttributeError:
            # Рекомендации по умолчанию если нет профиля
            context['recommended_courses'] = Course.objects.order_by(
                '-rating', '-created_at'
            )[:3]

    return render(request, 'courses/index.html', context)



def course_list(request):
    courses = Course.objects.all()
    form = CourseFilterForm(request.GET)

    if form.is_valid():
        category = form.cleaned_data.get('category')
        if category:
            courses = courses.filter(category=category)

    joined_course_ids = (
        request.user.courses_joined.values_list('id', flat=True)
        if request.user.is_authenticated else []
    )

    return render(request, 'courses/courses.html', {
        'courses': courses,
        'form': form,
        'joined_course_ids': joined_course_ids,
    })


@login_required
def join_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if course not in request.user.courses_joined.all():
        request.user.courses_joined.add(course)
        messages.success(request, f'Вы записались на курс: {course.title}')
    return redirect('course_list')



def video_lessons(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    video_lessons = course.video_lessons.all()
    return render(request, 'courses/video_lessons.html', {
        'course': course,
        'lessons': video_lessons
    })
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'courses/registration/register.html', {'form': form})

@login_required
def profile(request):
    # Инициализируем форму для GET и POST запросов
    if request.method == 'POST':
        u_form = UserUpdateForm(
            request.POST, 
            instance=request.user,
            files=request.FILES  # Для обработки загрузки файлов (если есть)
        )
        if u_form.is_valid():
            u_form.save()
    else:
        u_form = UserUpdateForm(instance=request.user)  # Создаем форму для GET-запроса

    context = {
        'u_form': u_form,
    }
    return render(request, 'courses/profile/profile.html', context)
@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        profile_form = UserProfileUpdateForm(request.POST, instance=request.user)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль был успешно обновлен!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileUpdateForm(instance=request.user)
    
    return render(request, 'courses/profile/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })
def teachers_list(request):
    teachers = Teacher.objects.all()
    return render(request, 'courses/teachers.html', {'teachers': teachers})

def about(request):
    about_content = AboutPage.objects.first()
    return render(request, 'courses/about.html', {'about': about_content})
@require_POST
def custom_logout(request):
    logout(request)
    return redirect('home')

@login_required
def my_courses_view(request):
    courses = request.user.courses_joined.all()
    return render(request, 'courses/my_courses.html', {'courses': courses})

def course_detail(request, slug):
    # Получаем курс по slug или возвращаем 404
    course = get_object_or_404(Course, slug=slug)
    
    # Пример контекста (добавьте нужные данные)
    context = {
        'course': course,
        'lessons': course.lessons.all(),
        'progress': course.progress  # Если есть свойство progress
    }
    return render(request, 'courses/course_detail.html', context)

class LessonCreateView(LoginRequiredMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/lesson_form.html'

    def form_valid(self, form):
        form.instance.course = Course.objects.get(pk=self.kwargs['course_id'])
        return super().form_valid(form)

class LessonUpdateView(LoginRequiredMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/lesson_form.html'
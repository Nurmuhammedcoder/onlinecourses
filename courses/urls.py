from django.urls import path
from . import views
from .views import home 
from django.contrib.auth import views as auth_views
from .forms import UserLoginForm  # Правильно
from .views import LessonCreateView, LessonUpdateView
urlpatterns = [
    path('course/<int:course_id>/add-lesson/', 
         LessonCreateView.as_view(), 
         name='add_lesson'),
    path('lesson/<int:pk>/edit/', 
         LessonUpdateView.as_view(), 
         name='edit_lesson'),
    path('', views.home, name='home'),
    path('', home, name='home'),
    path('courses/', views.course_list, name='course_list'),
    path('join_course/<int:course_id>/', views.join_course, name='join_course'),
    path('courses/<int:course_id>/', views.video_lessons, name='video_lessons'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='courses/registration/login.html', form_class=UserLoginForm), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='courses/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='courses/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='courses/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='courses/password_reset_complete.html'),
         name='password_reset_complete'),
     path('teachers/', views.teachers_list, name='teachers'),
    path('about/', views.about, name='about'),
path('my-courses/', views.my_courses_view, name='my_courses'),
]
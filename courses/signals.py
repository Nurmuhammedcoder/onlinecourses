from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserCourseProgress, UserAchievement
from .models import CustomUser, UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
    instance.profile.save()
@receiver(post_save, sender=UserCourseProgress)
def check_achievements(sender, instance, **kwargs):
    user = instance.user
    # Проверка достижения "Первый курс"
    if instance.progress_percent() >= 100:
        achievement, created = Achievement.objects.get_or_create(
            name='Первый курс',
            defaults={
                'description': 'Завершил первый курс',
                'icon': 'bi-trophy',
                'condition': 'complete_first_course'
            }
        )
        UserAchievement.objects.get_or_create(user=user, achievement=achievement)
    
    # Дополнительные проверки достижений...
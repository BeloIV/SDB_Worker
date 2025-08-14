from django.urls import path
from . import views

app_name = 'team_manager'

urlpatterns = [
    path('api/admin-login/', views.admin_login, name='admin_login'),
    path('api/create-team/', views.create_team, name='create_team'),
    path('api/add-member/', views.add_team_member, name='add_member'),
    path('api/import-members/', views.import_team_members, name='import_members'),
    path('api/update-member/', views.update_team_member, name='update_member'),
    path('api/delete-member/', views.delete_team_member, name='delete_member'),
    path('api/add-task/', views.add_task, name='add_task'),
    path('api/import-tasks/', views.import_tasks, name='import_tasks'),
    path('api/update-task/', views.update_task, name='update_task'),
    path('api/delete-task/', views.delete_task, name='delete_task'),
    path('api/restore-task/', views.restore_task, name='restore_task'),
    path('api/generate-schedule/', views.generate_schedule, name='generate_schedule'),
    path('api/get-schedule/', views.get_team_schedule, name='get_schedule'),
    path('api/get-schedule-for-date/', views.get_team_schedule_for_date, name='get_schedule_for_date'),
    path('api/get-task-details/', views.get_task_details, name='get_task_details'),
    path('api/team-info/<int:team_id>/', views.get_team_info, name='team_info'),
]

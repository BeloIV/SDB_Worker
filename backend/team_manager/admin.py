from django.contrib import admin
from .models import Team, TeamMember, Task, TaskSchedule

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'team_password', 'admin_password', 'created_at', 'member_count']
    search_fields = ['name']
    readonly_fields = ['team_password', 'admin_password', 'created_at', 'updated_at']
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = "Počet členov"

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'created_at']
    list_filter = ['team']
    search_fields = ['name', 'team__name']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'people_needed', 'created_at']
    list_filter = ['team', 'people_needed']
    search_fields = ['name', 'team__name', 'description']

@admin.register(TaskSchedule)
class TaskScheduleAdmin(admin.ModelAdmin):
    list_display = ['task', 'team', 'date', 'members_display', 'created_at']
    list_filter = ['team', 'date', 'task']
    search_fields = ['task__name', 'team__name']
    date_hierarchy = 'date'
    
    def members_display(self, obj):
        return ", ".join([member.name for member in obj.members.all()])
    members_display.short_description = "Členovia"

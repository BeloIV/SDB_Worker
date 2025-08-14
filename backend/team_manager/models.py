from django.db import models
import secrets
import string

def generate_team_password():
    """Generuje 8-miestne heslo pre tím"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def generate_admin_password():
    """Generuje 10-miestne heslo pre admina tímu"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))

class Team(models.Model):
    name = models.CharField(max_length=100, verbose_name="Názov tímu")
    team_password = models.CharField(max_length=8, default=generate_team_password, unique=True, verbose_name="Heslo pre tím")
    admin_password = models.CharField(max_length=10, default=generate_admin_password, verbose_name="Heslo pre admina")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tím"
        verbose_name_plural = "Tímy"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.team_password:
            self.team_password = generate_team_password()
        if not self.admin_password:
            self.admin_password = generate_admin_password()
        super().save(*args, **kwargs)

class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members', verbose_name="Tím")
    name = models.CharField(max_length=100, verbose_name="Meno")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Člen tímu"
        verbose_name_plural = "Členovia tímu"
        unique_together = ['team', 'name']

    def __str__(self):
        return f"{self.name} ({self.team.name})"

class Task(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='tasks', verbose_name="Tím")
    name = models.CharField(max_length=200, verbose_name="Názov úlohy")
    description = models.TextField(blank=True, verbose_name="Popis")
    people_needed = models.PositiveIntegerField(default=1, verbose_name="Počet potrebných ľudí")
    time_slot = models.PositiveIntegerField(default=1, verbose_name="Časový slot (1-5)")
    is_deleted = models.BooleanField(default=False, verbose_name="Úloha je vymazaná")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Úloha"
        verbose_name_plural = "Úlohy"
        unique_together = ['team', 'name']

    def __str__(self):
        status = " [VYMAZANÁ]" if self.is_deleted else ""
        return f"{self.name} ({self.team.name}) - {self.people_needed} ľudí{status}"

class TaskSchedule(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='schedules', verbose_name="Tím")
    date = models.DateField(verbose_name="Dátum")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='schedules', verbose_name="Úloha")
    members = models.ManyToManyField(TeamMember, related_name='schedules', verbose_name="Členovia")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rozvrh úlohy"
        verbose_name_plural = "Rozvrhy úloh"
        unique_together = ['team', 'date', 'task']

    def __str__(self):
        member_names = ", ".join([member.name for member in self.members.all()])
        return f"{self.task.name} - {self.date} ({member_names})"

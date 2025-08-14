from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import authenticate
from datetime import datetime, timedelta
import json
import os
import random
import itertools
from .models import Team, TeamMember, Task, TaskSchedule
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@csrf_exempt
@require_http_methods(["POST"])
def admin_login(request):
    """Admin prihlásenie cez .env heslo"""
    try:
        data = json.loads(request.body)
        admin_password = data.get('admin_password')
        
        if not admin_password:
            return JsonResponse({'error': 'Admin heslo je povinné'}, status=400)
        
        # Kontrola proti .env premennej
        env_admin_password = os.getenv('ADMIN_PASSWORD')
        if not env_admin_password:
            return JsonResponse({'error': 'Admin heslo nie je nastavené na serveri'}, status=500)
        
        if admin_password == env_admin_password:
            return JsonResponse({'success': True, 'message': 'Úspešné prihlásenie'})
        else:
            return JsonResponse({'error': 'Nesprávne admin heslo'}, status=401)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_team(request):
    """Vytvorí nový tím"""
    try:
        data = json.loads(request.body)
        team_name = data.get('name')
        
        if not team_name:
            return JsonResponse({'error': 'Názov tímu je povinný'}, status=400)
        
        team = Team.objects.create(name=team_name)
        
        return JsonResponse({
            'success': True,
            'team_id': team.id,
            'team_password': team.team_password,
            'admin_password': team.admin_password
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_team_member(request):
    """Pridá člena do tímu"""
    try:
        data = json.loads(request.body)
        team_id = data.get('team_id')
        admin_password = data.get('admin_password')
        member_name = data.get('name')
        
        if not all([team_id, admin_password, member_name]):
            return JsonResponse({'error': 'Všetky polia sú povinné'}, status=400)
        
        team = get_object_or_404(Team, id=team_id)
        
        if team.admin_password != admin_password:
            return JsonResponse({'error': 'Nesprávne admin heslo'}, status=401)
        
        member, created = TeamMember.objects.get_or_create(
            team=team,
            name=member_name
        )
        
        if not created:
            return JsonResponse({'error': 'Člen s týmto menom už existuje'}, status=400)
        
        return JsonResponse({'success': True, 'member_id': member.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def import_team_members(request):
    """Importuje členov tímu z textu (jeden člen na riadok)"""
    try:
        data = json.loads(request.body)
        team_id = data.get('team_id')
        members_text = data.get('members_text')
        admin_password = data.get('admin_password')
        
        if not all([team_id, admin_password, members_text]):
            return JsonResponse({'error': 'Všetky polia sú povinné'}, status=400)
        
        team = get_object_or_404(Team, id=team_id)
        
        if team.admin_password != admin_password:
            return JsonResponse({'error': 'Nesprávne admin heslo'}, status=401)
        
        # Rozdel text na riadky a vyčisti
        member_names = [name.strip() for name in members_text.split('\n') if name.strip()]
        
        if not member_names:
            return JsonResponse({'error': 'Text neobsahuje žiadne mená'}, status=400)
        
        # Skontroluj duplicity v texte
        if len(member_names) != len(set(member_names)):
            return JsonResponse({'error': 'Text obsahuje duplicitné mená'}, status=400)
        
        # Skontroluj či už existujú
        existing_names = set(TeamMember.objects.filter(team=team).values_list('name', flat=True))
        new_names = [name for name in member_names if name not in existing_names]
        
        if not new_names:
            return JsonResponse({'error': 'Všetci členovia už existujú'}, status=400)
        
        # Vytvor nových členov
        created_members = []
        for name in new_names:
            member = TeamMember.objects.create(team=team, name=name)
            created_members.append({
                'id': member.id,
                'name': member.name
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Úspešne pridaných {len(created_members)} nových členov',
            'members': created_members,
            'total_added': len(created_members),
            'skipped': len(member_names) - len(new_names)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_team_member(request):
    """Aktualizuje meno člena tímu"""
    try:
        data = json.loads(request.body)
        member_id = data.get('member_id')
        new_name = data.get('new_name')
        admin_password = data.get('admin_password')
        
        if not all([member_id, new_name, admin_password]):
            return JsonResponse({'error': 'Všetky polia sú povinné'}, status=400)
        
        member = get_object_or_404(TeamMember, id=member_id)
        team = member.team
        
        if team.admin_password != admin_password:
            return JsonResponse({'error': 'Nesprávne admin heslo'}, status=400)
        
        # Skontroluj či nové meno už existuje
        if TeamMember.objects.filter(team=team, name=new_name).exclude(id=member_id).exists():
            return JsonResponse({'error': 'Člen s týmto menom už existuje'}, status=400)
        
        # Aktualizuj meno
        old_name = member.name
        member.name = new_name
        member.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Člen {old_name} bol premenovaný na {new_name}',
            'member': {
                'id': member.id,
                'name': member.name
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_team_member(request):
    """Vymaže člena tímu"""
    try:
        data = json.loads(request.body)
        member_id = data.get('member_id')
        admin_password = data.get('admin_password')
        
        if not all([member_id, admin_password]):
            return JsonResponse({'error': 'Všetky polia sú povinné'}, status=400)
        
        member = get_object_or_404(TeamMember, id=member_id)
        team = member.team
        
        if team.admin_password != admin_password:
            return JsonResponse({'error': 'Nesprávne admin heslo'}, status=400)
        
        # Skontroluj či člen nemá priradené úlohy
        if member.schedules.exists():
            return JsonResponse({'error': 'Člena nie je možné vymazať, má priradené úlohy'}, status=400)
        
        member_name = member.name
        member.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Člen {member_name} bol úspešne vymazaný'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def import_tasks(request):
    """Importuje úlohy tímu z textu (formát: Názov úlohy (X) - Popis)"""
    try:
        data = json.loads(request.body)
        team_id = data.get('team_id')
        tasks_text = data.get('tasks_text')
        admin_password = data.get('admin_password')
        
        if not all([team_id, admin_password, tasks_text]):
            return JsonResponse({'error': 'Všetky polia sú povinné'}, status=400)
        
        team = get_object_or_404(Team, id=team_id)
        
        if team.admin_password != admin_password:
            return JsonResponse({'error': 'Nesprávne admin heslo'}, status=400)
        
        # Rozdel text na riadky a vyčisti
        task_lines = [line.strip() for line in tasks_text.split('\n') if line.strip()]
        
        if not task_lines:
            return JsonResponse({'error': 'Text neobsahuje žiadne úlohy'}, status=400)
        
        # Parsuj úlohy
        parsed_tasks = []
        for line in task_lines:
            # Formát: "Názov úlohy (X) - Popis - Časový slot" alebo "Názov úlohy (X) - Časový slot"
            if '(' in line and ')' in line:
                # Nájdi počet ľudí v zátvorke
                start = line.rfind('(')
                end = line.rfind(')')
                if start < end:
                    people_part = line[start+1:end]
                    try:
                        people_needed = int(people_part)
                        # Získaj názov, popis a časový slot
                        name_part = line[:start].strip()
                        remaining_part = line[end+1:].strip()
                        
                        # Rozdel na popis a časový slot
                        parts = remaining_part.split('-')
                        description_part = ''
                        time_slot = 1  # Default časový slot
                        
                        if len(parts) >= 2:
                            description_part = parts[0].strip()
                            if len(parts) >= 3:
                                try:
                                    time_slot = int(parts[2].strip())
                                    if time_slot < 1 or time_slot > 5:
                                        time_slot = 1
                                except ValueError:
                                    time_slot = 1
                        
                        parsed_tasks.append({
                            'name': name_part,
                            'people_needed': people_needed,
                            'description': description_part,
                            'time_slot': time_slot
                        })
                    except ValueError:
                        continue
            else:
                # Jednoduchý formát bez počtu ľudí - použije default 1
                parsed_tasks.append({
                    'name': line,
                    'people_needed': 1,
                    'description': '',
                    'time_slot': 1
                })
        
        if not parsed_tasks:
            return JsonResponse({'error': 'Nepodarilo sa parsovať žiadne úlohy'}, status=400)
        
        # Skontroluj duplicity v texte
        task_names = [task['name'] for task in parsed_tasks]
        if len(task_names) != len(set(task_names)):
            return JsonResponse({'error': 'Text obsahuje duplicitné názvy úloh'}, status=400)
        
        # Skontroluj či už existujú (aj vymazané)
        existing_tasks = Task.objects.filter(team=team)
        existing_names = set(existing_tasks.values_list('name', flat=True))
        
        # Rozdel úlohy na nové a existujúce vymazané
        new_tasks = []
        restored_tasks = []
        
        for task_data in parsed_tasks:
            if task_data['name'] not in existing_names:
                new_tasks.append(task_data)
            else:
                # Skontroluj či je úloha vymazaná
                existing_task = existing_tasks.filter(name=task_data['name']).first()
                if existing_task and existing_task.is_deleted:
                    restored_tasks.append((existing_task, task_data))
        
        if not new_tasks and not restored_tasks:
            return JsonResponse({'error': 'Všetky úlohy už existujú'}, status=400)
        
        # Obnov vymazané úlohy
        restored_tasks_data = []
        for existing_task, task_data in restored_tasks:
            existing_task.description = task_data['description']
            existing_task.people_needed = task_data['people_needed']
            existing_task.time_slot = task_data['time_slot']
            existing_task.is_deleted = False
            existing_task.save()
            
            restored_tasks_data.append({
                'id': existing_task.id,
                'name': existing_task.name,
                'description': existing_task.description,
                'people_needed': existing_task.people_needed,
                'time_slot': existing_task.time_slot
            })
        
        # Vytvor nové úlohy
        created_tasks = []
        for task_data in new_tasks:
            task = Task.objects.create(
                team=team,
                name=task_data['name'],
                description=task_data['description'],
                people_needed=task_data['people_needed'],
                time_slot=task_data['time_slot']
            )
            created_tasks.append({
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'people_needed': task.people_needed,
                'time_slot': task.time_slot
            })
        
        total_added = len(created_tasks) + len(restored_tasks_data)
        all_tasks = created_tasks + restored_tasks_data
        
        return JsonResponse({
            'success': True,
            'message': f'Úspešne pridaných {len(created_tasks)} nových úloh a obnovených {len(restored_tasks_data)} vymazaných úloh',
            'tasks': all_tasks,
            'total_added': total_added,
            'skipped': len(parsed_tasks) - total_added
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_task(request):
    """Aktualizuje úlohu tímu"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        new_name = data.get('new_name')
        new_description = data.get('new_description')
        new_people_needed = data.get('new_people_needed')
        new_time_slot = data.get('new_time_slot', 1)
        admin_password = data.get('admin_password')
        
        if not all([task_id, new_name, new_people_needed, admin_password]):
            return JsonResponse({'error': 'Všetky polia sú povinné'}, status=400)
        
        # Validácia časového slotu
        if new_time_slot < 1 or new_time_slot > 5:
            return JsonResponse({'error': 'Časový slot musí byť medzi 1 a 5'}, status=400)
        
        task = get_object_or_404(Task, id=task_id)
        team = task.team
        
        if team.admin_password != admin_password:
            return JsonResponse({'error': 'Nesprávne admin heslo'}, status=400)
        
        # Skontroluj či nový názov už existuje (ignoruj vymazané úlohy)
        if Task.objects.filter(team=team, name=new_name, is_deleted=False).exclude(id=task_id).exists():
            return JsonResponse({'error': 'Úloha s týmto názvom už existuje'}, status=400)
        
        # Aktualizuj úlohu
        old_name = task.name
        task.name = new_name
        task.description = new_description or ''
        task.people_needed = new_people_needed
        task.time_slot = new_time_slot
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Úloha {old_name} bola úspešne aktualizovaná',
            'task': {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'people_needed': task.people_needed,
                'time_slot': task.time_slot
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_task(request):
    """Vymaže úlohu tímu"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        admin_password = data.get('admin_password')
        
        if not all([task_id, admin_password]):
            return JsonResponse({'error': 'Všetky polia sú povinné'}, status=400)
        
        task = get_object_or_404(Task, id=task_id)
        team = task.team
        
        if team.admin_password != admin_password:
            return JsonResponse({'error': 'Nesprávne admin heslo'}, status=400)
        
        # Namiesto vymazania z databázy označ úlohu ako vymazanú
        # Toto zachová existujúce rozvrhy, ale úloha sa nebude pridávať do nových
        task_name = task.name
        task.is_deleted = True
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Úloha {task_name} bola úspešne vymazaná (zachované existujúce rozvrhy)'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def restore_task(request):
    """Obnoví vymazanú úlohu tímu"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        admin_password = data.get('admin_password')
        
        if not all([task_id, admin_password]):
            return JsonResponse({'error': 'Všetky polia sú povinné'}, status=400)
        
        task = get_object_or_404(Task, id=task_id)
        team = task.team
        
        if team.admin_password != admin_password:
            return JsonResponse({'error': 'Nesprávne admin heslo'}, status=401)
        
        if not task.is_deleted:
            return JsonResponse({'error': 'Úloha nie je vymazaná'}, status=400)
        
        task_name = task.name
        task.is_deleted = False
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Úloha {task_name} bola úspešne obnovená'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_task(request):
    """Pridá úlohu do tímu"""
    try:
        data = json.loads(request.body)
        team_id = data.get('team_id')
        admin_password = data.get('admin_password')
        task_name = data.get('name')
        task_description = data.get('description', '')
        people_needed = data.get('people_needed', 1)
        time_slot = data.get('time_slot', 1)
        
        if not all([team_id, admin_password, task_name]):
            return JsonResponse({'error': 'Tím ID, admin heslo a názov úlohy sú povinné'}, status=400)
        
        # Validácia počtu ľudí
        if people_needed < 1:
            return JsonResponse({'error': 'Počet ľudí musí byť aspoň 1'}, status=400)
        
        # Validácia časového slotu
        if time_slot < 1 or time_slot > 5:
            return JsonResponse({'error': 'Časový slot musí byť medzi 1 a 5'}, status=400)
        
        team = get_object_or_404(Team, id=team_id)
        
        if team.admin_password != admin_password:
            return JsonResponse({'error': 'Nesprávne admin heslo'}, status=401)
        
        # Skontroluj či úloha s týmto názvom už existuje (aj vymazané)
        existing_task = Task.objects.filter(team=team, name=task_name).first()
        
        if existing_task:
            if existing_task.is_deleted:
                # Ak je úloha vymazaná, obnov ju
                existing_task.description = task_description
                existing_task.people_needed = people_needed
                existing_task.time_slot = time_slot
                existing_task.is_deleted = False
                existing_task.save()
                
                return JsonResponse({
                    'success': True, 
                    'task_id': existing_task.id,
                    'task': {
                        'id': existing_task.id,
                        'name': existing_task.name,
                        'description': existing_task.description,
                        'people_needed': existing_task.people_needed,
                        'time_slot': existing_task.time_slot
                    },
                    'message': 'Vymazaná úloha bola obnovená'
                })
            else:
                return JsonResponse({'error': 'Úloha s týmto názvom už existuje'}, status=400)
        
        # Vytvor novú úlohu
        task = Task.objects.create(
            team=team,
            name=task_name,
            description=task_description,
            people_needed=people_needed,
            time_slot=time_slot
        )
        
        return JsonResponse({
            'success': True, 
            'task_id': task.id,
            'task': {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'people_needed': task.people_needed,
                'time_slot': task.time_slot
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def generate_schedule(request):
    """Vygeneruje rozvrh úloh na jeden deň"""
    try:
        data = json.loads(request.body)
        team_id = data.get('team_id')
        admin_password = data.get('admin_password')
        target_date = data.get('date')  # Dátum pre ktorý sa generuje rozvrh
        
        if not all([team_id, admin_password, target_date]):
            return JsonResponse({'error': 'Tím ID, admin heslo a dátum sú povinné'}, status=400)
        
        team = get_object_or_404(Team, id=team_id)
        
        if team.admin_password != admin_password:
            return JsonResponse({'error': 'Nesprávne admin heslo'}, status=401)
        
        # Získaj členov a úlohy (ignoruj vymazané úlohy)
        members = list(team.members.all())
        tasks = list(team.tasks.filter(is_deleted=False))
        
        if not members or not tasks:
            return JsonResponse({'error': 'Tím musí mať aspoň jedného člena a jednu úlohu'}, status=400)
        
        # Parse dátum
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Vymaž existujúce rozvrhy pre tento dátum a tím
        TaskSchedule.objects.filter(team=team, date=target_date).delete()
        
        # Funkcia na kontrolu či sa vyčerpali všetky unikátne kombinácie
        def should_reset_counters():
            # Ak je počet členov menší ako maximálny počet potrebných ľudí pre úlohu, nemôže sa vyčerpať
            max_people_needed = max(task.people_needed for task in tasks)
            if len(members) < max_people_needed:
                return False
            
            # Skontroluj či existujú úlohy ktoré sa nedajú priradiť bez opakovania
            for task in tasks:
                if task.people_needed == 1:
                    # Pre jednu osobu - ak všetci už robili túto úlohu
                    all_have_done = True
                    for member in members:
                        if not TaskSchedule.objects.filter(
                            team=team,
                            task=task,
                            members=member,
                            date__lt=target_date
                        ).exists():
                            all_have_done = False
                            break
                    if not all_have_done:
                        return False
                else:
                    # Pre viac ľudí - skontroluj či existuje aspoň jedna kombinácia bez opakovania
                    combinations = list(itertools.combinations(members, task.people_needed))
                    has_unused_combination = False
                    for combination in combinations:
                        member_ids = [m.id for m in combination]
                        # Hľadaj rozvrhy kde sú VŠETCI členovia tejto skupiny priradení k tejto úlohe
                        schedules_with_all_members = TaskSchedule.objects.filter(
                            team=team,
                            task=task,
                            date__lt=target_date
                        )
                        
                        combination_used = False
                        for schedule in schedules_with_all_members:
                            schedule_member_ids = set(schedule.members.values_list('id', flat=True))
                            if set(member_ids).issubset(schedule_member_ids):
                                combination_used = True
                                break
                        
                        if not combination_used:
                            has_unused_combination = True
                            break
                    
                    if has_unused_combination:
                        return False
            
            return True
        
        # Generuj rozvrh pre jeden deň
        schedules = []
        member_task_count = {member.id: 0 for member in members}
        member_pair_count = {}
        
        # Zoskup úlohy podľa časových slotov
        tasks_by_time_slot = {}
        for task in tasks:
            time_slot = task.time_slot
            if time_slot not in tasks_by_time_slot:
                tasks_by_time_slot[time_slot] = []
            tasks_by_time_slot[time_slot].append(task)
        
        # Rotuj poradie úloh a členov pre lepšiu distribúciu
        # Použi kombináciu dátumu a času pre lepšiu rotáciu
        seed_value = hash(target_date) % 1000000
        if should_reset_counters():
            # Ak sa vyčerpali kombinácie, použij iný seed pre leitmotiv
            seed_value = (seed_value + 1) % 1000000
        
        random.seed(seed_value)
        rotated_members = list(members)
        random.shuffle(rotated_members)
        
        # Získaj históriu pred aktuálnym dátumom pre lepšie počítadlá
        historical_schedules = TaskSchedule.objects.filter(
            team=team,
            date__lt=target_date
        ).select_related('task').prefetch_related('members')
        
        # Inicializuj počítadlá z histórie
        for schedule in historical_schedules:
            for member in schedule.members.all():
                member_task_count[member.id] += 1
            
            # Aktualizuj počítadlá párov z histórie
            members_list = list(schedule.members.all())
            if len(members_list) > 1:
                for i in range(len(members_list)):
                    for j in range(i+1, len(members_list)):
                        pair_key = tuple(sorted([members_list[i].id, members_list[j].id]))
                        member_pair_count[pair_key] = member_pair_count.get(pair_key, 0) + 1
        
        # Ak sa vyčerpali všetky unikátne kombinácie, resetuj počítadlá
        if should_reset_counters():
            member_task_count = {member.id: 0 for member in members}
            member_pair_count = {}
            print(f"Počítadlá pre tím {team.name} boli resetované - vyčerpali sa všetky unikátne kombinácie.")
        
        # Spracuj úlohy podľa časových slotov
        for time_slot in sorted(tasks_by_time_slot.keys()):
            tasks_in_slot = tasks_by_time_slot[time_slot]
            random.shuffle(tasks_in_slot)  # Náhodne poradie úloh v rámci slotu
            
            for task in tasks_in_slot:
                # Nájdi najlepšiu kombináciu členov pre úlohu
                best_members = find_best_member_combination(
                    rotated_members, task, member_task_count, member_pair_count, target_date, time_slot
                )
                
                if best_members:
                    # Vytvor rozvrh
                    schedule = TaskSchedule.objects.create(
                        team=team,
                        date=target_date,
                        task=task
                    )
                    
                    # Pridaj členov do rozvrhu
                    schedule.members.set(best_members)
                    
                    schedules.append({
                        'id': schedule.id,
                        'date': target_date.isoformat(),
                        'task': task.name,
                        'people_needed': task.people_needed,
                        'time_slot': task.time_slot,
                        'members': [member.name for member in best_members]
                    })
                    
                    # Aktualizuj počítadlá
                    for member in best_members:
                        member_task_count[member.id] += 1
                    
                    # Aktualizuj počítadlá párov
                    if len(best_members) > 1:
                        for i in range(len(best_members)):
                            for j in range(i+1, len(best_members)):
                                pair_key = tuple(sorted([best_members[i].id, best_members[j].id]))
                                member_pair_count[pair_key] = member_pair_count.get(pair_key, 0) + 1
        
        # Kontrola či sa vyčerpali všetky unikátne kombinácie počas generovania
        # Ak áno, resetuj počítadlá pre budúce generovania
        if should_reset_counters():
            # Resetuj počítadlá v databáze alebo cache pre budúce generovania
            # Toto by sa mohlo implementovať ako globálny cache alebo databázová tabuľka
            # Pre teraz len logujeme informáciu
            print(f"Všetky unikátne kombinácie pre tím {team.name} sa vyčerpali. Počítadlá boli resetované.")
        
        return JsonResponse({
            'success': True,
            'schedules': schedules,
            'message': f'Vygenerovaný rozvrh pre {target_date.strftime("%d.%m.%Y")}'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def find_best_member_combination(members, task, member_task_count, member_pair_count, date, current_time_slot=None):
    """Nájde najlepšiu kombináciu členov pre úlohu s úplnou kontrolou párov a úloh"""
    people_needed = task.people_needed
    
    # Získaj tím z prvej úlohy
    team = task.team
    
    # Funkcia na kontrolu spravodlivosti - prioritizuje spravodlivosť
    def is_fair_distribution(candidate_members, current_task_counts):
        if not candidate_members:
            return False
        
        # Vypočítaj nové počty úloh po pridaní tejto úlohy
        new_task_counts = current_task_counts.copy()
        for member in candidate_members:
            new_task_counts[member.id] = new_task_counts.get(member.id, 0) + 1
        
        # Nájdi minimálny a maximálny počet úloh
        min_tasks = min(new_task_counts.values())
        max_tasks = max(new_task_counts.values())
        
        # Ak je rozdiel väčší ako 2, nie je to spravodlivé
        if max_tasks - min_tasks > 2:
            return False
        
        # Ak niekto má 3+ úlohy, skontroluj či všetci ostatní majú aspoň 1
        if max_tasks >= 3:
            members_with_less_than_1 = sum(1 for count in new_task_counts.values() if count < 1)
            if members_with_less_than_1 > 0:
                return False
        
        return True
    
    # Funkcia na výpočet skóre spravodlivosti - nižšie skóre = lepšia spravodlivosť
    def calculate_fairness_score(candidate_members, current_task_counts):
        if not candidate_members:
            return float('inf')
        
        # Vypočítaj nové počty úloh po pridaní tejto úlohy
        new_task_counts = current_task_counts.copy()
        for member in candidate_members:
            new_task_counts[member.id] = new_task_counts.get(member.id, 0) + 1
        
        # Nájdi minimálny a maximálny počet úloh
        min_tasks = min(new_task_counts.values())
        max_tasks = max(new_task_counts.values())
        
        # Skóre spravodlivosti - čím menšie, tým lepšie
        fairness_score = max_tasks - min_tasks
        
        # Penalizuj situácie kde niekto má 3+ úlohy a niekto 0
        if max_tasks >= 3:
            members_with_less_than_1 = sum(1 for count in new_task_counts.values() if count < 1)
            fairness_score += members_with_less_than_1 * 10
        
        return fairness_score
    
    # Ak je zadaný časový slot, skontroluj či členovia už nemajú úlohy v tomto čase
    if current_time_slot is not None:
        # Filtruj členov ktorí už nemajú úlohy v aktuálnom časovom slote
        available_members = []
        for member in members:
            # Skontroluj či člen už nemá úlohu v aktuálnom časovom slote
            has_task_in_slot = TaskSchedule.objects.filter(
                team=team,
                date=date,
                task__time_slot=current_time_slot,
                members=member
            ).exists()
            
            if not has_task_in_slot:
                available_members.append(member)
        
        # Ak nie sú dostupní žiadni členovia pre tento časový slot, vráť None
        if len(available_members) < people_needed:
            return None
        
        # Použi len dostupných členov
        members = available_members
    
    # Kontrola histórie iba pred aktuálnym dátumom
    def has_done_task_before_date(member, task, team, date):
        return TaskSchedule.objects.filter(
            team=team,
            task=task,
            members=member,
            date__lt=date
        ).exists()
    
    def has_done_task_as_group_before_date(members_list, task, team, date):
        if len(members_list) == 1:
            return has_done_task_before_date(members_list[0], task, team, date)
        
        # Pre viac členov kontroluj či už existovala kombinácia tejto skupiny s touto úlohou
        member_ids = [m.id for m in members_list]
        # Hľadaj rozvrhy kde sú VŠETCI členovia tejto skupiny priradení k tejto úlohe
        schedules_with_all_members = TaskSchedule.objects.filter(
            team=team,
            task=task,
            date__lt=date
        )
        
        for schedule in schedules_with_all_members:
            schedule_member_ids = set(schedule.members.values_list('id', flat=True))
            if set(member_ids).issubset(schedule_member_ids):
                return True
        
        return False
    
    if people_needed == 1:
        # Pre jednu osobu - vyber člena ktorý túto úlohu ešte nerobil
        members_without_task = []
        for member in members:
            if not has_done_task_before_date(member, task, team, date):
                members_without_task.append(member)
        
        if members_without_task:
            # Najprv skús nájsť člena s najmenším počtom úloh ktorý spravodlivo rozdelí úlohy
            # Zoraď členov podľa skóre spravodlivosti (od najmenšieho)
            members_with_scores = []
            for member in members_without_task:
                fairness_score = calculate_fairness_score([member], member_task_count)
                members_with_scores.append((fairness_score, member_task_count[member.id], member))
            
            # Zoraď podľa skóre spravodlivosti, potom podľa počtu úloh
            members_with_scores.sort(key=lambda x: (x[0], x[1]))
            
            # Ak je prvá kombinácia spravodlivá, použij ju
            if is_fair_distribution([members_with_scores[0][2]], member_task_count):
                return [members_with_scores[0][2]]
            
            # Inak vyber člena s najmenším počtom úloh
            min_task_count = min(member_task_count[m.id] for m in members_without_task)
            candidates = [m for m in members_without_task if member_task_count[m.id] == min_task_count]
            random.shuffle(candidates)
            return [candidates[0]]
        else:
            # Ak všetci už túto úlohu robili, skús nájsť spravodlivú kombináciu
            members_with_scores = []
            for member in members:
                fairness_score = calculate_fairness_score([member], member_task_count)
                members_with_scores.append((fairness_score, member_task_count[member.id], member))
            
            # Zoraď podľa skóre spravodlivosti, potom podľa počtu úloh
            members_with_scores.sort(key=lambda x: (x[0], x[1]))
            
            # Ak je prvá kombinácia spravodlivá, použij ju
            if is_fair_distribution([members_with_scores[0][2]], member_task_count):
                return [members_with_scores[0][2]]
            
            # Inak vyber člena s najmenším počtom úloh
            min_task_count = min(member_task_count[m.id] for m in members)
            candidates = [m for m in members if member_task_count[m.id] == min_task_count]
            random.shuffle(candidates)
            return [candidates[0]]
    
    elif people_needed == 2:
        # Pre dve osoby - kontroluj kombináciu dvojica+úloha
        best_score = float('inf')
        best_combination = None
        
        # Generuj všetky možné dvojice
        all_combinations = []
        for i, member1 in enumerate(members):
            for j, member2 in enumerate(members[i+1:], i+1):
                # Skontroluj či niektorý z členov už túto úlohu robil
                if has_done_task_before_date(member1, task, team, date) or has_done_task_before_date(member2, task, team, date):
                    continue
                
                # Skontroluj či táto kombinácia dvojica+úloha už existovala
                if has_done_task_as_group_before_date([member1, member2], task, team, date):
                    continue
                
                # Skontroluj počet spoločných úloh tejto dvojice
                pair_key = tuple(sorted([member1.id, member2.id]))
                pair_count = member_pair_count.get(pair_key, 0)
                
                # Skóre = súčet úloh oboch členov + počet spoločných úloh (vyššia váha)
                score = member_task_count[member1.id] + member_task_count[member2.id] + pair_count * 10
                all_combinations.append((score, [member1, member2]))
        
        # Zoraď podľa skóre spravodlivosti, potom podľa skóre úloh
        all_combinations_with_fairness = []
        for score, combination in all_combinations:
            fairness_score = calculate_fairness_score(combination, member_task_count)
            all_combinations_with_fairness.append((fairness_score, score, combination))
        
        # Zoraď podľa skóre spravodlivosti (primárne), potom podľa skóre úloh (sekundárne)
        all_combinations_with_fairness.sort(key=lambda x: (x[0], x[1]))
        all_combinations = [(score, combination) for fairness_score, score, combination in all_combinations_with_fairness]
        
        # Najprv skús nájsť spravodlivú kombináciu bez opakovania
        for score, combination in all_combinations:
            if is_fair_distribution(combination, member_task_count):
                return combination
        
        # Ak sa nenašla žiadna spravodlivá kombinácia bez opakovania, 
        # vyber kombináciu s najlepším skóre spravodlivosti
        best_fairness_score = float('inf')
        best_combination = None
        
        for score, combination in all_combinations:
            fairness_score = calculate_fairness_score(combination, member_task_count)
            if fairness_score < best_fairness_score:
                best_fairness_score = fairness_score
                best_combination = combination
        
        if best_combination:
            return best_combination
        
        # Ak sa stále nenašla žiadna kombinácia, vyber dvojicu s najmenším počtom úloh
        min_task_count = min(member_task_count[m.id] for m in members)
        candidates = [m for m in members if member_task_count[m.id] == min_task_count]
        random.shuffle(candidates)
        return candidates[:2]
    
    else:
        # Pre viac ako 2 osoby - implementuj rotáciu s minimálnym opakovaním
        all_combinations = []
        
        # Generuj všetky možné kombinácie členov
        for combination in itertools.combinations(members, people_needed):
            # Skontroluj či niektorý z členov už túto úlohu robil
            if any(has_done_task_before_date(m, task, team, date) for m in combination):
                continue
            
            # Skontroluj či táto kombinácia skupina+úloha už existovala
            if has_done_task_as_group_before_date(combination, task, team, date):
                continue
            
            # Skontroluj počet spoločných úloh medzi členmi skupiny
            group_score = 0
            for i in range(len(combination)):
                for j in range(i+1, len(combination)):
                    pair_key = tuple(sorted([combination[i].id, combination[j].id]))
                    group_score += member_pair_count.get(pair_key, 0)
            
            # Skóre = súčet úloh všetkých členov + počet spoločných úloh (vyššia váha)
            total_task_count = sum(member_task_count[m.id] for m in combination)
            score = total_task_count + group_score * 10
            all_combinations.append((score, list(combination)))
        
        # Zoraď podľa skóre spravodlivosti, potom podľa skóre úloh
        all_combinations_with_fairness = []
        for score, combination in all_combinations:
            fairness_score = calculate_fairness_score(combination, member_task_count)
            all_combinations_with_fairness.append((fairness_score, score, combination))
        
        # Zoraď podľa skóre spravodlivosti (primárne), potom podľa skóre úloh (sekundárne)
        all_combinations_with_fairness.sort(key=lambda x: (x[0], x[1]))
        all_combinations = [(score, combination) for fairness_score, score, combination in all_combinations_with_fairness]
        
        # Najprv skús nájsť spravodlivú kombináciu bez opakovania
        for score, combination in all_combinations:
            if is_fair_distribution(combination, member_task_count):
                return combination
        
        # Ak sa nenašla žiadna spravodlivá kombinácia bez opakovania, 
        # vyber kombináciu s najlepším skóre spravodlivosti
        best_fairness_score = float('inf')
        best_combination = None
        
        for score, combination in all_combinations:
            fairness_score = calculate_fairness_score(combination, member_task_count)
            if fairness_score < best_fairness_score:
                best_fairness_score = fairness_score
                best_combination = combination
        
        if best_combination:
            return best_combination
        
        # Ak sa stále nenašla žiadna kombinácia, vyber skupinu s najmenším počtom úloh
        min_task_count = min(member_task_count[m.id] for m in members)
        candidates = [m for m in members if member_task_count[m.id] == min_task_count]
        random.shuffle(candidates)
        return candidates[:people_needed]

@csrf_exempt
@require_http_methods(["POST"])
def get_team_schedule(request):
    """Získa rozvrh tímu pomocou týmového hesla"""
    try:
        data = json.loads(request.body)
        team_password = data.get('team_password')
        
        if not team_password:
            return JsonResponse({'error': 'Heslo tímu je povinné'}, status=400)
        
        team = get_object_or_404(Team, team_password=team_password)
        
        # Získaj rozvrhy zoradené podľa dátumu a časových slotov
        schedules = TaskSchedule.objects.filter(team=team).order_by('date', 'task__time_slot')
        
        schedule_data = []
        for schedule in schedules:
            schedule_data.append({
                'id': schedule.id,
                'date': schedule.date.isoformat(),
                'task': schedule.task.name,
                'people_needed': schedule.task.people_needed,
                'time_slot': schedule.task.time_slot,
                'members': [member.name for member in schedule.members.all()]
            })
        
        return JsonResponse({
            'success': True,
            'team_name': team.name,
            'team_id': team.id,
            'schedules': schedule_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_team_schedule_for_date(request):
    """Získa rozvrh tímu pre konkrétny deň"""
    try:
        data = json.loads(request.body)
        team_password = data.get('team_password')
        target_date = data.get('date')
        
        if not team_password or not target_date:
            return JsonResponse({'error': 'Heslo tímu a dátum sú povinné'}, status=400)
        
        team = get_object_or_404(Team, team_password=team_password)
        
        # Parse dátum
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Získaj rozvrhy pre konkrétny deň zoradené podľa časových slotov
        schedules = TaskSchedule.objects.filter(team=team, date=target_date).order_by('task__time_slot')
        
        if not schedules.exists():
            return JsonResponse({
                'success': True,
                'team_name': team.name,
                'team_id': team.id,
                'date': target_date.isoformat(),
                'schedules': [],
                'message': f'Pre {target_date.strftime("%d.%m.%Y")} nie je vygenerovaný rozvrh'
            })
        
        schedule_data = []
        for schedule in schedules:
            schedule_data.append({
                'id': schedule.id,
                'task_id': schedule.task.id,
                'task': schedule.task.name,
                'task_description': schedule.task.description,
                'people_needed': schedule.task.people_needed,
                'time_slot': schedule.task.time_slot,
                'members': [member.name for member in schedule.members.all()]
            })
        
        return JsonResponse({
            'success': True,
            'team_name': team.name,
            'team_id': team.id,
            'date': target_date.isoformat(),
            'schedules': schedule_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_task_details(request):
    """Získa detailné informácie o úlohe"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        team_password = data.get('team_password')
        
        if not task_id or not team_password:
            return JsonResponse({'error': 'ID úlohy a heslo tímu sú povinné'}, status=400)
        
        team = get_object_or_404(Team, team_password=team_password)
        task = get_object_or_404(Task, id=task_id, team=team)
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'people_needed': task.people_needed,
                'time_slot': task.time_slot
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_team_info(request, team_id):
    """Získa informácie o tíme"""
    try:
        team = get_object_or_404(Team, id=team_id)
        
        members = [{'id': m.id, 'name': m.name} for m in team.members.all()]
        tasks = [{'id': t.id, 'name': t.name, 'description': t.description, 'people_needed': t.people_needed, 'time_slot': t.time_slot, 'is_deleted': t.is_deleted} for t in team.tasks.all()]
        
        return JsonResponse({
            'success': True,
            'team': {
                'id': team.id,
                'name': team.name,
                'created_at': team.created_at.isoformat()
            },
            'members': members,
            'tasks': tasks
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

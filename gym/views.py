from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from gym.models import MembershipPlan, Enrollment, Announcement, GalleryImage
from accounts.models import UserProfile
from scheduling.models import AvailableSlot, Booking
from nutrition.models import DietPlan, WorkoutPlan, ProgressLog, GlobalWorkout, DailyTaskCompletion, DailyMealCompletion, Meal, Exercise, WeeklyFeedback
from payments.models import Transaction
from staff_control.models import StaffPermission, FEATURE_CHOICES, ALL_FEATURE_KEYS
import json
import requests
from gym.utils import get_member_stats


# ─────────────────────────────── PUBLIC VIEWS ────────────────────────────── #

def overview(request):
    plans = MembershipPlan.objects.filter(is_active=True)
    announcements = Announcement.objects.filter(is_active=True)[:3]
    gallery = GalleryImage.objects.all()[:12]
    # Trainer cards: all staff users
    trainers = UserProfile.objects.filter(role='staff').select_related('user')

    # Dynamic calculation for "Sessions Completed"
    total_bookings = Booking.objects.filter(status='confirmed').count()
    total_tasks = DailyTaskCompletion.objects.filter(is_completed=True).count()
    total_sessions = total_bookings + total_tasks

    # Dynamic calculation for "Years of Excellence" (at least 1)
    first_user = User.objects.order_by('date_joined').first()
    if first_user:
        years = (timezone.now() - first_user.date_joined).days // 365
        years_of_excellence = max(1, years)
    else:
        years_of_excellence = 1

    context = {
        'plans': plans,
        'announcements': announcements,
        'gallery': gallery,
        'trainers': trainers,
        'total_members': UserProfile.objects.filter(role='member').count(),
        'total_trainers': trainers.count(),
        'total_sessions': total_sessions,
        'years_of_excellence': years_of_excellence,
    }
    return render(request, 'overview/index.html', context)


# ─────────────────────────────── MEMBER PORTAL ───────────────────────────── #

def _require_role(role):
    """Decorator factory for role-based access."""
    from functools import wraps
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            try:
                if request.user.profile.role != role:
                    return redirect('overview')
            except Exception:
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def get_allowed_tabs(user):
    """
    Central logic to determine which portal tabs a member can access.
    """
    # Superusers see everything

    if getattr(user, 'is_superuser', False):
         return MembershipPlan.DEFAULT_TABS

    active_enrollment = Enrollment.objects.filter(user=user, is_active=True).first()

    # Restricted tier for non-members or expired members
    if not active_enrollment or active_enrollment.is_expired:
        # Non-subscribed users get basic features only (no checklist / progress)
        return ['dashboard', 'bmi', 'nutrient', 'payments']

    # Plan-based tabs or default
    return active_enrollment.plan.allowed_tabs or MembershipPlan.DEFAULT_TABS


def require_tab(tab_key):
    """
    Decorator to protect views based on plan-based tab permissions.
    Usage: @require_tab('booking')
    """
    from functools import wraps
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'message': 'Login required'}, status=401)

            allowed = get_allowed_tabs(request.user)
            if tab_key not in allowed:
                return JsonResponse({
                    'message': f'Your current plan does not include access to the "{tab_key.replace("_", " ").title()}" feature.'
                }, status=403)

            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


@login_required
def member_portal(request):
    if getattr(request.user, 'is_superuser', False):
        return redirect('admin_portal')
    try:
        profile = request.user.profile
        if profile.role != 'member':
            return _redirect_portal(profile.role)
    except Exception:
        return redirect('login')

    today = timezone.localtime().date()
    active_enrollment = Enrollment.objects.filter(
        user=request.user, is_active=True
    ).first()

    upcoming_bookings = Booking.objects.filter(
        member=request.user,
        status='confirmed',
        slot__date__gte=today
    ).select_related('slot', 'slot__instructor').order_by('slot__date', 'slot__start_time')[:5]

    # Active plan logic: Date-bounded plan first, then fallback to most recent
    diet_plan = DietPlan.objects.filter(member=request.user).order_by('-updated_at').first()
    workout_plan = WorkoutPlan.objects.filter(member=request.user).order_by('-updated_at').first()
    progress_logs = ProgressLog.objects.filter(member=request.user)[:10]
    recent_transactions = Transaction.objects.filter(user=request.user)[:5]
    announcements = Announcement.objects.filter(is_active=True)[:3]
    plans = MembershipPlan.objects.filter(is_active=True)
    global_workouts = GlobalWorkout.objects.all()

    # Define allowed tabs logic (Using the centralized helper)
    allowed_tabs = get_allowed_tabs(request.user)

    today_name = today.strftime('%A').lower()
    
    # Filter meals/exercises for today
    today_meals = diet_plan.meals.filter(day=today_name) if diet_plan else []
    today_exercises = workout_plan.exercises.filter(day=today_name) if workout_plan else []
    
    meal_completion_ids = list(DailyMealCompletion.objects.filter(
        member=request.user, date=today, is_completed=True
    ).values_list('meal_id', flat=True))
    
    exercise_completion_ids = list(DailyTaskCompletion.objects.filter(
        member=request.user, date=today, is_completed=True
    ).values_list('exercise_id', flat=True))

    today_log = ProgressLog.objects.filter(member=request.user, date=today).first()


    # Dashboard prompt for trainer selection
    needs_trainer = (profile.instructor is None) and (active_enrollment is not None)

    # Advanced Analytics for Member Dashboard
    stats = get_member_stats(request.user)

    context = {
        'today_log': today_log,
        'profile': profile,
        'enrollment': active_enrollment,
        'upcoming_bookings': upcoming_bookings,
        'diet_plan': diet_plan,
        'workout_plan': workout_plan,
        'today_meals': today_meals,
        'today_exercises': today_exercises,
        'meal_completion_ids': meal_completion_ids,
        'exercise_completion_ids': exercise_completion_ids,
        'progress_logs': list(progress_logs.values('date', 'weight_kg', 'height_cm', 'body_fat_pct', 'waist_cm')),
        'recent_transactions': recent_transactions,
        'announcements': announcements,
        'plans': plans,
        'global_workouts': global_workouts,
        'allowed_tabs': allowed_tabs,
        'today': today,
        'today_name': today_name.title(),
        'needs_trainer': needs_trainer,
        'stats': stats, # Advanced analytics (consistency, BMI, trends, etc.)
    }
    return render(request, 'portals/member_portal.html', context)


@login_required
def select_trainer_view(request):
    """Page for member to choose an instructor."""
    try:
        profile = request.user.profile
        if profile.role != 'member':
            return _redirect_portal(profile.role)
        
        # Only allow if they have an active plan but no instructor
        active_enrollment = Enrollment.objects.filter(user=request.user, is_active=True).first()
        if not active_enrollment:
            return redirect('member_portal')

        instructors = UserProfile.objects.filter(role='staff').select_related('user').prefetch_related('assigned_members')
        specialities = instructors.values_list('speciality', flat=True).distinct()
        specialities = [s for s in specialities if s]

        context = {
            'instructors': instructors,
            'specialities': specialities,
        }
        return render(request, 'portals/select_trainer.html', context)
    except Exception:
        return redirect('member_portal')


@login_required
def process_trainer_selection(request):
    """AJAX endpoint to save chosen instructor."""
    if request.method == 'POST':
        try:
            profile = request.user.profile
            if profile.role != 'member':
                return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
            
            data = json.loads(request.body)
            instructor_id = data.get('instructor_id')
            if not instructor_id:
                return JsonResponse({'success': False, 'message': 'Instructor ID required'}, status=400)
            
            instructor_profile = get_object_or_404(UserProfile, id=instructor_id, role='staff')
            profile.instructor = instructor_profile
            profile.save()
            
            return JsonResponse({'success': True, 'message': f'Trainer {instructor_profile.user.get_full_name() or instructor_profile.user.email} assigned!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


@login_required
@require_tab('booking')
def get_instructor_slots(request):
    """Return all available slots as JSON for FullCalendar, including instructor name."""
    try:
        today = timezone.now().date()
        # Fetch slots for all instructors
        slots = AvailableSlot.objects.filter(
            date__gte=today
        ).select_related('instructor__profile')

        booked_slot_ids = set(
            Booking.objects.filter(
                member=request.user, status='confirmed'
            ).values_list('slot_id', flat=True)
        )

        events = []
        for s in slots:
            booking_count = Booking.objects.filter(slot_id=s.id, status='confirmed').count()
            is_full = booking_count >= s.capacity
            is_booked = s.id in booked_slot_ids
            
            # Include instructor name in title if it's not already descriptive
            instructor_name = s.instructor.get_full_name() or s.instructor.email
            display_title = f"{s.title} ({instructor_name})" if s.title else f"Session with {instructor_name}"

            events.append({
                'id': s.id,
                'title': display_title,
                'start': f"{s.date}T{s.start_time}",
                'end': f"{s.date}T{s.end_time}",
                'color': '#16a34a' if is_booked else ('#ef4444' if is_full else s.color),
                'extendedProps': {
                    'is_booked': is_booked,
                    'is_full': is_full,
                    'spots_left': s.capacity - booking_count,
                    'instructor': instructor_name,
                }
            })
        return JsonResponse(events, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_tab('booking')
def book_slot(request, slot_id):
    if request.method == 'POST':
        slot = get_object_or_404(AvailableSlot, id=slot_id)
        
        # Prevent booking past slots
        from django.utils import timezone
        import datetime
        now = timezone.now()
        slot_datetime = datetime.datetime.combine(slot.date, slot.start_time)
        slot_datetime = timezone.make_aware(slot_datetime) if timezone.is_naive(slot_datetime) else slot_datetime
        if slot_datetime < now:
            return JsonResponse({'message': 'Cannot book a slot in the past.'}, status=400)
            
        # General booking flow - check for past slots and capacity
        if slot.is_full:
            return JsonResponse({'message': 'This slot is already full.'}, status=400)
        if slot.is_full:
            return JsonResponse({'message': 'This slot is already full.'}, status=400)
        booking, created = Booking.objects.get_or_create(
            member=request.user, slot=slot,
            defaults={'status': 'confirmed'}
        )
        if not created:
            return JsonResponse({'message': 'You already booked this slot.'}, status=400)
        return JsonResponse({'message': 'Session booked successfully!'})
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
@require_tab('booking')
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, member=request.user)
        booking.status = 'cancelled'
        booking.save()
        return JsonResponse({'message': 'Booking cancelled.'})
    return JsonResponse({'message': 'Method not allowed'}, status=405)





    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def weekly_performance_analysis(request):
    """Basic analysis of task completion for the last 7 days."""
    try:
        today = timezone.now().date()

        start_date = today - timezone.timedelta(days=7)
        
        meals_count = DailyMealCompletion.objects.filter(
            member=request.user, date__gte=start_date, is_completed=True
        ).count()
        tasks_count = DailyTaskCompletion.objects.filter(
            member=request.user, date__gte=start_date, is_completed=True
        ).count()
        
        return JsonResponse({
            'summary': f"You've completed {meals_count} meals and {tasks_count} exercises in the past week. Keep it up!",
            'meals_completed': meals_count,
            'tasks_completed': tasks_count
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_tab('progress')
def log_progress(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            log_date_str = data.get('date')
            if log_date_str:
                log_date = timezone.datetime.strptime(log_date_str, '%Y-%m-%d').date()
            else:
                log_date = timezone.now().date()
            
            log, _ = ProgressLog.objects.update_or_create(
                member=request.user, date=log_date,
                defaults={
                    'weight_kg': data.get('weight_kg') or None,
                    'height_cm': data.get('height_cm') or None,
                    'body_fat_pct': data.get('body_fat_pct') or None,
                    'chest_cm': data.get('chest_cm') or None,
                    'waist_cm': data.get('waist_cm') or None,
                    'hip_cm': data.get('hip_cm') or None,
                    'notes': data.get('notes', ''),
                }
            )
            return JsonResponse({'message': 'Progress logged!'})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
@require_tab('nutrient')
def nutrient_proxy(request):
    """Server-side proxy to fetch nutrition data, avoiding browser/CORS/400 issues."""
    query = request.GET.get('query', '')
    if not query:
        return JsonResponse({'message': 'Query required'}, status=400)

    from django.conf import settings
    api_key = getattr(settings, 'CALORIE_NINJAS_API_KEY', '')
    api_url = getattr(settings, 'CALORIE_NINJAS_API_URL', 'https://api.api-ninjas.com/v1/nutrition')

    try:
        response = requests.get(
            api_url,
            params={'query': query},
            headers={'X-Api-Key': api_key},
            timeout=10
        )
        if response.status_code != 200:
            return JsonResponse({
                'message': f'Upstream Error {response.status_code}', 
                'detail': response.text
            }, status=response.status_code)
        
        return JsonResponse(response.json(), safe=False)
    except Exception as e:
        return JsonResponse({'message': 'Server Proxy Error', 'error': str(e)}, status=500)


@login_required
@require_tab('workout')
def toggle_exercise_completion(request, exercise_id):
    if request.method == 'POST':
        try:
            from nutrition.models import Exercise
            exercise = get_object_or_404(Exercise, id=exercise_id)
            data = json.loads(request.body)
            log_date = data.get('date', timezone.localtime().date())
            task, created = DailyTaskCompletion.objects.get_or_create(
                member=request.user, exercise=exercise, date=log_date
            )
            task.is_completed = data.get('is_completed', False)
            task.save()
            return JsonResponse({'message': 'Task updated.', 'is_completed': task.is_completed})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
@require_tab('diet')
def toggle_meal_completion(request, meal_id):
    if request.method == 'POST':
        try:
            from nutrition.models import Meal, DailyMealCompletion
            meal = get_object_or_404(Meal, id=meal_id)
            data = json.loads(request.body)
            log_date = data.get('date', timezone.localtime().date())
            task, created = DailyMealCompletion.objects.get_or_create(
                member=request.user, meal=meal, date=log_date
            )
            task.is_completed = data.get('is_completed', False)
            if task.is_completed:
                task.calories_snapshot = meal.calories
                task.protein_snapshot = meal.protein_g
                task.carbs_snapshot = meal.carbs_g
                task.fat_snapshot = meal.fat_g
            else:
                task.calories_snapshot = None
                task.protein_snapshot = None
                task.carbs_snapshot = None
                task.fat_snapshot = None
            task.save()
            return JsonResponse({'message': 'Meal updated.', 'is_completed': task.is_completed})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)

# ─────────────────────────────── STAFF PORTAL ────────────────────────────── #

@login_required
def staff_portal(request):
    if getattr(request.user, 'is_superuser', False):
        return redirect('admin_portal')
    try:
        profile = request.user.profile
        if profile.role != 'staff':
            return _redirect_portal(profile.role)
    except Exception:
        return redirect('login')

    today = timezone.now().date()
    my_members = UserProfile.objects.filter(
        instructor=profile, role='member'
    ).select_related('user').prefetch_related('user__diet_plans', 'user__workout_plans')

    upcoming_bookings = Booking.objects.filter(
        slot__instructor=request.user,
        status='confirmed',
        slot__date__gte=today
    ).select_related('member', 'slot').order_by('slot__date', 'slot__start_time')[:10]


    from nutrition.models import GlobalWorkout, DietPlan, WorkoutPlan, DAYS_CHOICES
    global_workouts = GlobalWorkout.objects.all().order_by('-created_at')
    diet_templates = DietPlan.objects.filter(instructor=request.user, is_template=True)
    workout_templates = WorkoutPlan.objects.filter(instructor=request.user, is_template=True)
    days_list = [d[0] for d in DAYS_CHOICES]

    from gym.models import Announcement
    announcements = Announcement.objects.filter(is_active=True)[:3]

    context = {
        'profile': profile,
        'my_members': my_members,
        'member_count': my_members.count(),
        'upcoming_bookings': upcoming_bookings,

        'global_workouts': global_workouts,
        'diet_templates': diet_templates,
        'workout_templates': workout_templates,
        'days_list': days_list,
        'announcements': announcements,
        'today': today,
        'feature_choices': FEATURE_CHOICES,
        'allowed_nav': StaffPermission.get_or_create_for_staff(request.user).get_allowed_features()
    }
    return render(request, 'portals/staff_portal.html', context)


@login_required
def get_staff_slots(request):
    """Return staff's own schedule slots for FullCalendar."""
    try:
        profile = request.user.profile
        if profile.role != 'staff':
            return JsonResponse({'events': []})
        slots = AvailableSlot.objects.filter(instructor=request.user)
        events = [{
            'id': s.id,
            'title': s.title or f"{s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')}",
            'start': f"{s.date}T{s.start_time}",
            'end': f"{s.date}T{s.end_time}",
            'color': s.color,
            'extendedProps': {'capacity': s.capacity, 'booked': s.bookings_count}
        } for s in slots]
        return JsonResponse(events, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def add_slot(request):
    if request.method == 'POST':
        try:
            profile = request.user.profile
            if profile.role != 'staff':
                return JsonResponse({'message': 'Unauthorized'}, status=403)
            data = json.loads(request.body)
            
            from django.utils import timezone
            import datetime
            now = timezone.now()
            slot_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
            slot_start_time = datetime.datetime.strptime(data['start_time'], '%H:%M').time()
            slot_datetime = datetime.datetime.combine(slot_date, slot_start_time)
            slot_datetime = timezone.make_aware(slot_datetime) if timezone.is_naive(slot_datetime) else slot_datetime
            
            if slot_datetime < now:
                return JsonResponse({'message': 'Cannot create slots in the past.'}, status=400)

            slot = AvailableSlot.objects.create(
                instructor=request.user,
                date=data['date'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                title=data.get('title', ''),
                capacity=data.get('capacity', 1),
                color=data.get('color', '#0d9488'),
            )
            return JsonResponse({'message': 'Slot added!', 'id': slot.id})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def delete_slot(request, slot_id):
    if request.method == 'POST':
        slot = get_object_or_404(AvailableSlot, id=slot_id, instructor=request.user)
        slot.delete()
        return JsonResponse({'message': 'Slot removed.'})
    return JsonResponse({'message': 'Method not allowed'}, status=405)



@login_required
def remove_member_plan(request, member_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            plan_type = data.get('plan_type') # 'diet' or 'workout'
            member = get_object_or_404(User, id=member_id)
            
            if plan_type == 'diet':
                DietPlan.objects.filter(member=member).delete()
            elif plan_type == 'workout':
                WorkoutPlan.objects.filter(member=member).delete()
            else:
                return JsonResponse({'message': 'Invalid plan type'}, status=400)
            
            return JsonResponse({'message': f'{plan_type.capitalize()} plan removed from member.'})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


# Diet & Workout Plan Views
@login_required
def save_diet_plan(request, member_id):
    """Saves a diet plan. If member_id is 0, it creates/updates a template."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                profile = request.user.profile
                if profile.role not in ('staff', 'admin'):
                    return JsonResponse({'message': 'Unauthorized'}, status=403)
                
                data = json.loads(request.body)
                is_template = data.get('is_template', False)
                member = None
                if not is_template:
                    member = get_object_or_404(User, id=member_id)

                plan_id = data.get('plan_id')
                if plan_id:
                    plan = get_object_or_404(DietPlan, id=plan_id)
                    plan.title = data.get('title', 'Diet Plan')
                    plan.notes = data.get('notes', '')
                    plan.category = data.get('category', '')
                    plan.save()
                else:
                    plan = DietPlan.objects.create(
                        member=member, instructor=request.user,
                        title=data.get('title', 'Diet Plan'),
                        notes=data.get('notes', ''),
                        is_template=is_template,
                        category=data.get('category', '')
                    )
                
                # Bulk items handle
                items = data.get('items')
                if items is not None:
                    plan.meals.all().delete()
                    for item in items:
                        Meal.objects.create(
                            diet_plan=plan,
                            meal_type=item.get('meal_type', 'breakfast'),
                            name=item.get('name', 'Meal'),
                            description=item.get('description', ''),
                            calories=item.get('calories'),
                            protein_g=item.get('protein_g'),
                            carbs_g=item.get('carbs_g'),
                            fat_g=item.get('fat_g'),
                            image_url=item.get('image_url', ''),
                            video_url=item.get('video_url', ''),
                            day=item.get('day', 'monday'),
                            order=item.get('order', 0)
                        )
                
                return JsonResponse({'message': 'Diet plan saved!', 'plan_id': plan.id})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def save_meal(request, plan_id):
    if request.user.profile.role not in ('staff', 'admin'):
        return JsonResponse({'message': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        try:
            from nutrition.models import Meal
            data = json.loads(request.body)
            plan = get_object_or_404(DietPlan, id=plan_id)
            meal = Meal.objects.create(
                diet_plan=plan,
                meal_type=data['meal_type'],
                name=data['name'],
                description=data.get('description', ''),
                calories=data.get('calories'),
                protein_g=data.get('protein_g'),
                carbs_g=data.get('carbs_g'),
                fat_g=data.get('fat_g'),
                image_url=data.get('image_url', ''),
                video_url=data.get('video_url', ''),
                day=data.get('day', 'monday')
            )

            return JsonResponse({'message': 'Meal added!', 'meal_id': meal.id})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def delete_meal(request, meal_id):
    if request.user.profile.role not in ('staff', 'admin'):
        return JsonResponse({'message': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        from nutrition.models import Meal
        meal = get_object_or_404(Meal, id=meal_id)
        meal.delete()
        return JsonResponse({'message': 'Meal deleted.'})
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def get_member_data(request, member_id):
    """Staff/Admin fetches a member's full profile including plans and progress."""
    try:
        from django.contrib.auth.models import User
        if request.user.profile.role not in ['staff', 'admin']:
            return JsonResponse({'message': 'Unauthorized'}, status=403)
        member_user = get_object_or_404(User, id=member_id)
        profile = member_user.profile
        if request.user.profile.role == 'staff' and profile.instructor and profile.instructor.user != request.user:
            return JsonResponse({'message': 'Unauthorized'}, status=403)
        
        today = timezone.localtime().date()
        # Active plan logic: Date-bounded plan first, then fallback to most recent
        diet = DietPlan.objects.filter(member=member_user).order_by('-updated_at').first()
        workout = WorkoutPlan.objects.filter(member=member_user).order_by('-updated_at').first()

        ex_completions = set(DailyTaskCompletion.objects.filter(member=member_user, date=today, is_completed=True).values_list('exercise_id', flat=True))
        meal_completions = set(DailyMealCompletion.objects.filter(member=member_user, date=today, is_completed=True).values_list('meal_id', flat=True))

        # Replaced manual logic with get_member_stats helper
        stats = get_member_stats(member_user)

        return JsonResponse({
            'member_name': member_user.get_full_name() or member_user.email,
            'member_email': member_user.email,
            'diet': {
                'id': diet.id if diet else None,
                'title': diet.title if diet else '',
                'notes': diet.notes if diet else '',
                'category': diet.category if diet else '',
                'meals': [{
                    'id': m.id, 'meal_type': m.meal_type, 'name': m.name, 'day': m.day,
                    'description': m.description,
                    'calories': m.calories, 'protein_g': m.protein_g, 'carbs_g': m.carbs_g, 'fat_g': m.fat_g,
                    'image_url': m.image_url,
                    'is_completed_today': m.id in meal_completions,
                    'video_url': m.video_url,
                    'youtube_embed_url': m.youtube_embed_url,
                    'is_youtube': m.is_youtube
                } for m in diet.meals.all()] if diet else []
            },
            'workout': {
                'id': workout.id if workout else None,
                'title': workout.title if workout else '',
                'notes': workout.notes if workout else '',
                'category': workout.category if workout else '',
                'exercises': [{
                    'id': ex.id, 'name': ex.name, 'day': ex.day, 'sets': ex.sets, 'reps': ex.reps, 
                    'rest_seconds': ex.rest_seconds, 'notes': ex.notes,
                    'is_completed_today': ex.id in ex_completions,
                    'video_url': ex.video_url,
                    'youtube_embed_url': ex.youtube_embed_url,
                    'is_youtube': ex.is_youtube
                } for ex in workout.exercises.all()] if workout else []
            },
            'progress': stats['raw_logs'],
            'advanced_metrics': stats['advanced_metrics'],
            'macro_history': stats['macro_history'],
            'target_weight_kg': stats['target_weight_kg'],
            'consistency': stats['consistency'],
            'insights': stats['insights'],
            'feedback': list(WeeklyFeedback.objects.filter(member=member_user).order_by('-date')[:3].values('date','analysis','rating','recommendations'))
        })
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@login_required
def save_workout_plan(request, member_id):
    if request.user.profile.role not in ('staff', 'admin'):
        return JsonResponse({'message': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                data = json.loads(request.body)
                is_template = data.get('is_template', False)
                member = None
                if not is_template:
                    member = get_object_or_404(User, id=member_id)

                plan_id = data.get('plan_id')
                if plan_id:
                    plan = get_object_or_404(WorkoutPlan, id=plan_id)
                    plan.title = data.get('title', 'Workout Plan')
                    plan.notes = data.get('notes', '')
                    plan.category = data.get('category', '')
                    plan.save()
                else:
                    plan = WorkoutPlan.objects.create(
                        member=member, instructor=request.user,
                        title=data.get('title', 'Workout Plan'),
                        notes=data.get('notes', ''),
                        is_template=is_template,
                        category=data.get('category', '')
                    )

                # Bulk items handle
                items = data.get('items')
                if items is not None:
                    plan.exercises.all().delete()
                    for item in items:
                        Exercise.objects.create(
                            workout_plan=plan,
                            name=item.get('name', 'Exercise'),
                            day=item.get('day', 'monday'),
                            sets=item.get('sets'),
                            reps=item.get('reps'),
                            rest_seconds=item.get('rest_seconds'),
                            notes=item.get('notes', ''),
                            video_url=item.get('video_url', ''),
                            order=item.get('order', 0)
                        )

                return JsonResponse({'message': 'Workout plan saved!', 'plan_id': plan.id})

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def assign_plan(request, plan_id):
    """Assigns (copies) a template plan to one or more members."""
    if request.user.profile.role not in ('staff', 'admin'):
        return JsonResponse({'message': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            template_id = data['template_id']
            member_ids = data['member_ids']
            plan_type = data['plan_type'] # 'diet' or 'workout'

            if plan_type == 'diet':
                template = get_object_or_404(DietPlan, id=template_id)
                meals = list(template.meals.all())
                for mid in member_ids:
                    member = get_object_or_404(User, id=mid)
                    # Remove existing diet plan if any
                    DietPlan.objects.filter(member=member).delete()
                    new_plan = DietPlan.objects.create(
                        member=member, instructor=request.user,
                        title=template.title, notes=template.notes,
                        category=template.category
                    )
                    for meal in meals:
                        # Copy meal
                        Meal.objects.create(
                            diet_plan=new_plan,
                            meal_type=meal.meal_type,
                            name=meal.name,
                            description=meal.description,
                            calories=meal.calories,
                            protein_g=meal.protein_g,
                            carbs_g=meal.carbs_g,
                            fat_g=meal.fat_g,
                            image_url=meal.image_url,
                            video_url=meal.video_url,
                            day=meal.day,
                            order=meal.order
                        )
            else:
                template = get_object_or_404(WorkoutPlan, id=template_id)
                exercises = list(template.exercises.all())
                for mid in member_ids:
                    member = get_object_or_404(User, id=mid)
                    
                    WorkoutPlan.objects.filter(member=member).delete()
                    new_plan = WorkoutPlan.objects.create(
                        member=member, instructor=request.user,
                        title=template.title, notes=template.notes,
                        category=template.category
                    )
                    for ex in exercises:
                        # Copy exercise
                        Exercise.objects.create(
                            workout_plan=new_plan,
                            name=ex.name,
                            day=ex.day,
                            sets=ex.sets,
                            reps=ex.reps,
                            rest_seconds=ex.rest_seconds,
                            notes=ex.notes,
                            video_url=ex.video_url,
                            order=ex.order
                        )

            
            return JsonResponse({'message': f'Plan assigned to {len(member_ids)} members.'})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def duplicate_plan(request, plan_id):
    """Duplicates an existing plan (template or member-specific)."""
    if request.user.profile.role not in ('staff', 'admin'):
        return JsonResponse({'message': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            plan_type = data['plan_type']
            if plan_type == 'diet':
                old_plan = get_object_or_404(DietPlan, id=plan_id)
                meals = list(old_plan.meals.all())
                new_plan = DietPlan.objects.create(
                    member=None, instructor=request.user,
                    title=f"Copy of {old_plan.title}", notes=old_plan.notes,
                    calories_target=old_plan.calories_target,
                    protein_target=old_plan.protein_target,
                    is_template=True, category=old_plan.category
                )
                for m in meals:
                    m.pk = None
                    m.diet_plan = new_plan
                    m.save()
            else:
                old_plan = get_object_or_404(WorkoutPlan, id=plan_id)
                exercises = list(old_plan.exercises.all())
                new_plan = WorkoutPlan.objects.create(
                    member=None, instructor=request.user,
                    title=f"Copy of {old_plan.title}", notes=old_plan.notes,
                    is_template=True, category=old_plan.category
                )
                for ex in exercises:
                    ex.pk = None
                    ex.workout_plan = new_plan
                    ex.save()
            return JsonResponse({'message': 'Plan duplicated successfully!', 'new_id': new_plan.id})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def save_feedback(request, member_id):
    if request.user.profile.role not in ('staff', 'admin'):
        return JsonResponse({'message': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        try:
            from nutrition.models import WeeklyFeedback
            data = json.loads(request.body)
            member = get_object_or_404(User, id=member_id)
            WeeklyFeedback.objects.create(
                member=member, instructor=request.user,
                analysis=data['analysis'],
                rating=data.get('rating', 5),
                recommendations=data.get('recommendations', '')
            )
            return JsonResponse({'message': 'Feedback saved!'})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def save_exercise(request, plan_id):
    if request.user.profile.role not in ('staff', 'admin'):
        return JsonResponse({'message': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        try:
            from nutrition.models import Exercise
            data = json.loads(request.body)
            plan = get_object_or_404(WorkoutPlan, id=plan_id)
            exercise = Exercise.objects.create(
                workout_plan=plan,
                name=data['name'],
                day=data.get('day', ''),
                sets=data.get('sets'),
                reps=data.get('reps', ''),
                rest_seconds=data.get('rest_seconds'),
                notes=data.get('notes', ''),
                video_url=data.get('video_url', ''),
            )
            return JsonResponse({'message': 'Exercise added!', 'exercise_id': exercise.id})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def delete_exercise(request, exercise_id):
    if request.user.profile.role not in ('staff', 'admin'):
        return JsonResponse({'message': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        from nutrition.models import Exercise
        ex = get_object_or_404(Exercise, id=exercise_id)
        ex.delete()
        return JsonResponse({'message': 'Exercise deleted.'})
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def save_global_workout(request):
    """Staff/Admin can upload general class workouts."""
    if request.user.profile.role not in ('staff', 'admin'):
        return JsonResponse({'message': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            workout_id = data.get('id')
            if workout_id:
                gw = get_object_or_404(GlobalWorkout, id=workout_id)
            else:
                gw = GlobalWorkout(created_by=request.user)
            gw.title = data['title']
            gw.category = data['category']
            gw.description = data.get('description', '')
            gw.video_url = data.get('video_url', '')
            gw.thumbnail_url = data.get('thumbnail_url', '')
            gw.save()
            return JsonResponse({'message': 'Global Workout saved!', 'id': gw.id})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def delete_global_workout(request, workout_id):
    if request.method == 'POST':
        gw = get_object_or_404(GlobalWorkout, id=workout_id)
        gw.delete()
        return JsonResponse({'message': 'Workout deleted.'})
    return JsonResponse({'message': 'Method not allowed'}, status=405)

# ─────────────────────────────── ADMIN PORTAL ────────────────────────────── #

@login_required
def admin_portal(request):
    if getattr(request.user, 'is_superuser', False):
        profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'admin'})
    else:
        try:
            profile = request.user.profile
            if profile.role != 'admin':
                return _redirect_portal(profile.role)
        except Exception:
            return redirect('login')

    today = timezone.now().date()
    total_members = UserProfile.objects.filter(role='member').count()
    total_staff = UserProfile.objects.filter(role='staff').count()
    active_enrollments = Enrollment.objects.filter(is_active=True).count()
    recent_transactions = Transaction.objects.filter(status='success')[:10]
    total_revenue = sum(t.amount for t in Transaction.objects.filter(status='success'))
    all_staff = UserProfile.objects.filter(role='staff').select_related('user')
    members = UserProfile.objects.filter(role='member').select_related('user', 'instructor')[:20]
    
    from django.contrib.sessions.models import Session
    from datetime import timedelta
    
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    logged_in_user_ids = []
    for session in active_sessions:
        data = session.get_decoded()
        uid = data.get('_auth_user_id')
        if uid:
            logged_in_user_ids.append(uid)
            
    # Consider "online" as having logged in within the last 12 hours AND hasn't logged out
    recently = timezone.now() - timedelta(hours=12)
    
    active_users = UserProfile.objects.filter(
        role__in=['member', 'staff'],
        user__id__in=logged_in_user_ids,
        user__last_login__gte=recently
    ).select_related('user').distinct().order_by('-user__last_login')[:8]

    plans = MembershipPlan.objects.filter(is_active=True)
    announcements = Announcement.objects.all()[:5]
    global_workouts = GlobalWorkout.objects.all()
    gallery = GalleryImage.objects.all()

    context = {
        'profile': profile,
        'total_members': total_members,
        'total_staff': total_staff,
        'active_enrollments': active_enrollments,
        'total_revenue': total_revenue,
        'recent_transactions': recent_transactions,
        'all_staff': all_staff,
        'members': members,
        'active_users': active_users,
        'plans': plans,
        'announcements': announcements,
        'global_workouts': global_workouts,
        'gallery': gallery,
        'feature_choices': FEATURE_CHOICES,
        'tab_choices': [
            ('dashboard', 'Dashboard'), ('checklist', 'Daily Checklist'), ('booking', 'Book Session'),
            ('diet', 'Diet Plan'), ('workout', 'Workout Plan'),
            ('global_workout', 'Workout Library'), ('progress', 'My Progress'),
            ('bmi', 'BMI Calculator'), ('nutrient', 'Nutrient Calculator'),
            ('payments', 'Payments'), ('profile', 'My Profile')
        ],
        'today': today,
    }
    return render(request, 'portals/admin_portal.html', context)


@login_required
def manage_access(request, staff_id):
    """Admin toggles staff feature permissions."""
    try:
        if request.user.profile.role != 'admin':
            return JsonResponse({'message': 'Unauthorized'}, status=403)
    except Exception:
        return JsonResponse({'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            staff_user = get_object_or_404(User, id=staff_id)
            perm = StaffPermission.get_or_create_for_staff(staff_user)
            perm.allowed_nav = data.get('allowed_nav', [])
            perm.save()
            return JsonResponse({'message': 'Permissions updated!'})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    elif request.method == 'GET':
        staff_user = get_object_or_404(User, id=staff_id)
        perm = StaffPermission.get_or_create_for_staff(staff_user)
        return JsonResponse({'allowed_nav': perm.allowed_nav, 'all_features': FEATURE_CHOICES})

    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def assign_instructor(request):
    """Admin assigns an instructor to a member."""
    if request.method == 'POST':
        try:
            if request.user.profile.role != 'admin':
                return JsonResponse({'message': 'Unauthorized'}, status=403)
            data = json.loads(request.body)
            member_profile = get_object_or_404(UserProfile, user_id=data['member_id'])
            
            instructor_id = data.get('instructor_id')
            if instructor_id:
                instructor_profile = get_object_or_404(UserProfile, user_id=instructor_id)
                member_profile.instructor = instructor_profile
            else:
                member_profile.instructor = None
            
            member_profile.save()
            return JsonResponse({'message': 'Instructor assigned!' if instructor_id else 'Instructor unassigned!'})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def save_announcement(request):
    if request.method == 'POST':
        try:
            if request.user.profile.role != 'admin':
                return JsonResponse({'message': 'Unauthorized'}, status=403)
            data = json.loads(request.body)
            ann = Announcement.objects.create(
                title=data['title'],
                body=data['body'],
                image_url=data.get('image_url', ''),
                created_by=request.user,
            )
            return JsonResponse({'message': 'Announcement posted!', 'id': ann.id})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def save_plan(request):
    """Admin CRUD for membership plans."""
    if request.method == 'POST':
        try:
            if request.user.profile.role != 'admin':
                return JsonResponse({'message': 'Unauthorized'}, status=403)
            data = json.loads(request.body)
            plan_id = data.get('id')
            if plan_id:
                plan = get_object_or_404(MembershipPlan, id=plan_id)
            else:
                plan = MembershipPlan()
            plan.name = data['name']
            plan.price = data['price']
            plan.duration_days = data['duration_days']
            plan.features = data.get('features', [])
            plan.image_url = data.get('image_url', '')
            plan.is_popular = data.get('is_popular', False)
            
            # Save allowed_tabs if provided, else use the class default for new plans
            if 'allowed_tabs' in data:
                plan.allowed_tabs = data['allowed_tabs']
            elif not plan_id:
                plan.allowed_tabs = MembershipPlan.DEFAULT_TABS
                
            plan.save()
            return JsonResponse({'message': 'Plan saved!', 'id': plan.id})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


def _redirect_portal(role):
    if role == 'admin':
        return redirect('admin_portal')
    elif role == 'staff':
        return redirect('staff_portal')
    return redirect('member_portal')
@login_required
def delete_member(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({"message": "Unauthorized"}, status=403)
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return JsonResponse({"message": "Member deleted successfully"})

@login_required
def delete_staff(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({"message": "Unauthorized"}, status=403)
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return JsonResponse({"message": "Staff account deleted successfully"})

@login_required
def delete_plan(request, plan_id):
    if not request.user.is_superuser:
        return JsonResponse({"message": "Unauthorized"}, status=403)
    plan = get_object_or_404(MembershipPlan, id=plan_id)
    plan.delete()
    return JsonResponse({"message": "Plan deleted successfully"})

@login_required
def delete_announcement(request, ann_id):
    if not request.user.is_superuser:
        return JsonResponse({"message": "Unauthorized"}, status=403)
    ann = get_object_or_404(Announcement, id=ann_id)
    ann.delete()
    return JsonResponse({"message": "Announcement deleted successfully"})


@login_required
def save_gallery_image(request):
    if request.method == 'POST':
        try:
            if request.user.profile.role != 'admin':
                return JsonResponse({'message': 'Unauthorized'}, status=403)
            data = json.loads(request.body)
            img = GalleryImage.objects.create(
                image_url=data['image_url'],
                caption=data.get('caption', ''),
                order=data.get('order', 0)
            )
            return JsonResponse({'message': 'Image added to gallery!', 'id': img.id})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def delete_gallery_image(request, img_id):
    if request.method == 'POST':
        try:
            if request.user.profile.role != 'admin':
                return JsonResponse({'message': 'Unauthorized'}, status=403)
            img = get_object_or_404(GalleryImage, id=img_id)
            img.delete()
            return JsonResponse({'message': 'Image removed from gallery.'})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def get_plan_detail(request, plan_id):
    """Returns full details of a plan including meals/exercises."""
    plan_type = request.GET.get('type')
    try:
        from nutrition.models import DietPlan, WorkoutPlan
        if plan_type == 'diet':
            plan = get_object_or_404(DietPlan, id=plan_id, instructor=request.user)
            data = {
                'id': plan.id,
                'title': plan.title,
                'category': plan.category,
                'notes': plan.notes,
                'meals': [{
                    'id': m.id,
                    'day': m.day,
                    'meal_type': m.meal_type,
                    'name': m.name,
                    'description': m.description,
                    'calories': m.calories,
                    'protein_g': m.protein_g,
                    'carbs_g': m.carbs_g,
                    'fat_g': m.fat_g,
                    'image_url': m.image_url,
                    'video_url': m.video_url

                } for m in plan.meals.all()]
            }
        else:
            plan = get_object_or_404(WorkoutPlan, id=plan_id, instructor=request.user)
            data = {
                'id': plan.id,
                'title': plan.title,
                'category': plan.category,
                'notes': plan.notes,
                'exercises': [{
                    'id': e.id,
                    'day': e.day,
                    'name': e.name,
                    'sets': e.sets,
                    'reps': e.reps,
                    'rest_seconds': e.rest_seconds,
                    'notes': e.notes,
                    'video_url': e.video_url

                } for e in plan.exercises.all()]
            }
        return JsonResponse({'plan': data})
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@login_required
def delete_template(request, plan_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            plan_type = data.get('type')
            from nutrition.models import DietPlan, WorkoutPlan
            if plan_type == 'diet':
                plan = get_object_or_404(DietPlan, id=plan_id, instructor=request.user, is_template=True)
            else:
                plan = get_object_or_404(WorkoutPlan, id=plan_id, instructor=request.user, is_template=True)
            plan.delete()
            return JsonResponse({'message': 'Template deleted.'})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)

@login_required
def copy_day(request, plan_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            from_day = data.get('from_day')
            to_day = data.get('to_day')
            plan_type = data.get('type')
            
            from nutrition.models import DietPlan, WorkoutPlan, Meal, Exercise, DAYS_CHOICES
            days = [d[0] for d in DAYS_CHOICES]
            targets = days if to_day == 'all' else [to_day]

            if plan_type == 'diet':
                plan = get_object_or_404(DietPlan, id=plan_id, instructor=request.user)
                source_items = plan.meals.filter(day=from_day)
                for day in targets:
                    if day == from_day: continue
                    plan.meals.filter(day=day).delete()
                    for item in source_items:
                        item.pk = None
                        item.day = day
                        item.save()
            else:
                plan = get_object_or_404(WorkoutPlan, id=plan_id, instructor=request.user)
                source_items = plan.exercises.filter(day=from_day)
                for day in targets:
                    if day == from_day: continue
                    plan.exercises.filter(day=day).delete()
                    for item in source_items:
                        item.pk = None
                        item.day = day
                        item.save()
            
            return JsonResponse({'message': f'Copied {from_day} to {to_day} successfully.'})
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    return JsonResponse({'message': 'Method not allowed'}, status=405)




@login_required
def save_feedback(request, member_id):
    if request.method == 'POST':
        from nutrition.models import WeeklyFeedback
        from django.contrib.auth.models import User
        member = get_object_or_404(User, id=member_id)
        data = json.loads(request.body)
        WeeklyFeedback.objects.create(
            member=member,
            instructor=request.user,
            content=data.get('content'),
            date=timezone.localtime().date()
        )
        return JsonResponse({'message': 'Feedback sent.'})
    return JsonResponse({'message': 'Error'}, status=405)

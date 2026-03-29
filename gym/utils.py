from django.utils import timezone
from django.db.models import Sum
from nutrition.models import ProgressLog, DailyTaskCompletion, DailyMealCompletion, DietPlan, WorkoutPlan
from accounts.models import UserProfile

def get_member_stats(member_user):
    """
    Calculates advanced health metrics, consistency, and insights for a member.
    Reused by both staff_portal and member_portal for data consistency.
    """
    profile = member_user.profile
    today = timezone.localtime().date()
    thirty_days_ago = today - timezone.timedelta(days=30)
    
    # Macro History (Last 30 days)
    macro_history_qs = DailyMealCompletion.objects.filter(
        member=member_user, date__gte=thirty_days_ago, is_completed=True
    )
    macro_history = list(macro_history_qs.values('date').annotate(
        total_cals=Sum('calories_snapshot'),
        total_protein=Sum('protein_snapshot'),
        total_carbs=Sum('carbs_snapshot'),
        total_fat=Sum('fat_snapshot')
    ).order_by('date'))

    # Consistency Math
    # Joined date fallback to 30 days if not set
    days_since_joined = (today - profile.joined_date).days if profile.joined_date else 30
    denominator = min(days_since_joined, 30) or 1
    
    diet_days = macro_history_qs.values('date').distinct().count()
    workout_days_qs = DailyTaskCompletion.objects.filter(
        member=member_user, date__gte=thirty_days_ago, is_completed=True
    ).values('date').distinct()
    workout_days_list = [v['date'] for v in workout_days_qs]
    workout_days = len(workout_days_list)
    
    diet_consistency = round((diet_days / denominator) * 100) if diet_days <= denominator else 100
    workout_consistency = round((workout_days / denominator) * 100) if workout_days <= denominator else 100

    # Smart Insights
    insights = []
    # Streak calculation
    streak = 0
    temp_date = today
    while temp_date in workout_days_list:
        streak += 1
        temp_date -= timezone.timedelta(days=1)
    if streak > 2:
        insights.append({"type": "streak", "text": f"Great Job: You have completed {streak} workouts in a row!"})
    
    # Weight Metrics & Deltas
    all_logs = list(ProgressLog.objects.filter(member=member_user).order_by('date'))
    metrics = {}
    if all_logs:
        first = all_logs[0]
        curr = all_logs[-1]
        
        # Plateau Check (last 14 days)
        fourteen_days_ago = today - timezone.timedelta(days=14)
        logs_14d = [l for l in all_logs if l.date >= fourteen_days_ago]
        if len(logs_14d) >= 2 and logs_14d[-1].weight_kg and logs_14d[0].weight_kg:
            recent_weight_diff = abs(float(logs_14d[-1].weight_kg) - float(logs_14d[0].weight_kg))
            if recent_weight_diff < 0.5:
                insights.append({"type": "plateau", "text": "Plateau Alert: Weight has changed less than 0.5kg in 14 days. Consider a small adjustment."})
        elif len(all_logs) > 3 and diet_consistency < 50:
            insights.append({"type": "diet", "text": "Insight: You've missed logging meals more than 50% of the time. Consistency is key!"})

        def _calc_bmi(w, h):
            if w and h and float(h) > 0:
                return round(float(w) / ((float(h)/100)**2), 1)
            return None

        metrics = {
            'initial_weight': first.weight_kg, 'current_weight': curr.weight_kg,
            'weight_delta': round(float(curr.weight_kg) - float(first.weight_kg), 1) if curr.weight_kg and first.weight_kg else None,
            'initial_bmi': _calc_bmi(first.weight_kg, first.height_cm),
            'current_bmi': _calc_bmi(curr.weight_kg, curr.height_cm),
            'initial_chest': first.chest_cm, 'current_chest': curr.chest_cm,
            'chest_delta': round(float(curr.chest_cm) - float(first.chest_cm), 1) if curr.chest_cm and first.chest_cm else None,
            'initial_waist': first.waist_cm, 'current_waist': curr.waist_cm,
            'waist_delta': round(float(curr.waist_cm) - float(first.waist_cm), 1) if curr.waist_cm and first.waist_cm else None,
        }

    # Raw Data for Matrix (last 30 days)
    raw_logs = []
    for p in ProgressLog.objects.filter(member=member_user).order_by('-date')[:30]:
        raw_logs.append({
            'date': p.date, 
            'weight_kg': p.weight_kg, 
            'height_cm': p.height_cm,
            'chest_cm': p.chest_cm, 
            'waist_cm': p.waist_cm, 
            'body_fat_pct': p.body_fat_pct, 
            'notes': p.notes,
            'workout_status': p.date in workout_days_list,
            'diet_status': bool(macro_history_qs.filter(date=p.date).exists())
        })

    return {
        'advanced_metrics': metrics,
        'macro_history': macro_history,
        'target_weight_kg': profile.target_weight_kg,
        'consistency': {'diet': diet_consistency, 'workout': workout_consistency},
        'insights': insights,
        'raw_logs': raw_logs
    }

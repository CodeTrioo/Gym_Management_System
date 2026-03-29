from django.contrib import admin
from nutrition.models import DietPlan, Meal, WorkoutPlan, Exercise, ProgressLog

admin.site.register(DietPlan)
admin.site.register(Meal)
admin.site.register(WorkoutPlan)
admin.site.register(Exercise)
admin.site.register(ProgressLog)

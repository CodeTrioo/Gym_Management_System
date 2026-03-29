from django.db import models
from django.contrib.auth.models import User


DAYS_CHOICES = [
    ('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'),
    ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday'),
    ('sunday', 'Sunday'),
]


class DietPlan(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diet_plans', null=True, blank=True)
    instructor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_diet_plans'
    )
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    calories_target = models.IntegerField(null=True, blank=True)
    protein_target = models.IntegerField(null=True, blank=True)  # grams
    is_template = models.BooleanField(default=False)
    category = models.CharField(max_length=100, blank=True)  # e.g. Keto, Bulking
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title}" + (f" for {self.member.email}" if self.member else " (Template)")

    class Meta:
        ordering = ['-updated_at']


class Meal(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('pre_workout', 'Pre-Workout'),
        ('post_workout', 'Post-Workout'),
    ]

    diet_plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE, related_name='meals')
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    day = models.CharField(max_length=20, choices=DAYS_CHOICES, default='monday')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    calories = models.IntegerField(null=True, blank=True)
    protein_g = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    carbs_g = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    fat_g = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    image_url = models.URLField(blank=True)  # Cloudinary or external URL
    video_url = models.URLField(blank=True)  # Instructions video
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.meal_type}: {self.name}"

    @property
    def youtube_embed_url(self):
        """Convert YouTube watch/shorts URLs to embed URLs."""
        import re
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/|youtube\.com/v/|youtube\.com/vi/)([^&?#/ ]+)', self.video_url, re.IGNORECASE)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube-nocookie.com/embed/{video_id}"
        return self.video_url

    @property
    def is_youtube(self):
        url = self.video_url.lower()
        return 'youtube.com' in url or 'youtu.be' in url

    class Meta:
        ordering = ['day', 'order', 'meal_type']



class WorkoutPlan(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_plans', null=True, blank=True)
    instructor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_workout_plans'
    )
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    is_template = models.BooleanField(default=False)
    category = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title}" + (f" for {self.member.email}" if self.member else " (Template)")

    class Meta:
        ordering = ['-updated_at']


class Exercise(models.Model):

    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='exercises')
    name = models.CharField(max_length=200)
    day = models.CharField(max_length=20, choices=DAYS_CHOICES, blank=True)
    sets = models.IntegerField(null=True, blank=True)
    reps = models.CharField(max_length=50, blank=True)  # e.g. "10-12" or "AMRAP"
    rest_seconds = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    video_url = models.URLField(blank=True)  # YouTube / Cloudinary / any URL
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.day})"

    @property
    def youtube_embed_url(self):
        """Convert YouTube watch/shorts URLs to embed URLs."""
        import re
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/|youtube\.com/v/|youtube\.com/vi/)([^&?#/ ]+)', self.video_url, re.IGNORECASE)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube-nocookie.com/embed/{video_id}"
        return self.video_url

    @property
    def is_youtube(self):
        url = self.video_url.lower()
        return 'youtube.com' in url or 'youtu.be' in url

    class Meta:
        ordering = ['day', 'order']


class ProgressLog(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_logs')
    date = models.DateField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    body_fat_pct = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    chest_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    waist_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    hip_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    notes = models.TextField(blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.email} - {self.date}"

    class Meta:
        ordering = ['-date']
        unique_together = ('member', 'date')


class GlobalWorkout(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    thumbnail_url = models.URLField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_global_workouts')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.category and self.created_by:
            try:
                spec = self.created_by.profile.speciality
                if spec:
                    self.category = spec
            except:
                pass
        if not self.category:
            self.category = "General"
        super().save(*args, **kwargs)

    @property
    def get_thumbnail_url(self):
        """Universal thumbnail generator for YouTube and Cloudinary."""
        if self.is_youtube:
            import re
            match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/|youtube\.com/v/|youtube\.com/vi/)([^&?#/ ]+)', self.video_url, re.IGNORECASE)
            if match:
                video_id = match.group(1)
                return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        
        if 'cloudinary.com' in self.video_url and '/video/upload/' in self.video_url:
            # Generate Cloudinary thumbnail: replace /video/upload/ with /video/upload/so_0/ and extension with .jpg
            url = self.video_url
            if '/video/upload/' in url:
                url = url.replace('/video/upload/', '/video/upload/so_0/')
            
            # Change extension to .jpg for the thumbnail
            import os
            base, ext = os.path.splitext(url)
            return base + ".jpg"

        return self.thumbnail_url or "https://via.placeholder.com/640x360?text=No+Preview"

    @property
    def youtube_thumbnail_url(self):
        """Deprecated: Use get_thumbnail_url instead. Kept for template compatibility."""
        return self.get_thumbnail_url

    @property
    def is_youtube(self):
        url = self.video_url.lower()
        return 'youtube.com' in url or 'youtu.be' in url

    class Meta:
        ordering = ['-created_at']

class DailyTaskCompletion(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_completions')
    exercise = models.ForeignKey('nutrition.Exercise', on_delete=models.CASCADE)
    date = models.DateField()
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.member.email} - {self.exercise.name} - {self.date}"

    class Meta:
        unique_together = ('member', 'exercise', 'date')
        ordering = ['-date']


class DailyMealCompletion(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_completions')
    meal = models.ForeignKey('nutrition.Meal', on_delete=models.CASCADE)
    date = models.DateField()
    is_completed = models.BooleanField(default=False)
    calories_snapshot = models.IntegerField(null=True, blank=True)
    protein_snapshot = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    carbs_snapshot = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    fat_snapshot = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)

    def __str__(self):
        return f"{self.member.email} - {self.meal.name} - {self.date}"

    class Meta:
        unique_together = ('member', 'meal', 'date')
        ordering = ['-date']


class WeeklyFeedback(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_feedback')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedback')
    date = models.DateField(auto_now_add=True)
    analysis = models.TextField()  # General analysis of performance
    rating = models.IntegerField(default=5)  # 1-10 or 1-5
    recommendations = models.TextField(blank=True)
    
    def __str__(self):
        return f"Feedback for {self.member.email} on {self.date}"

    class Meta:
        ordering = ['-date']

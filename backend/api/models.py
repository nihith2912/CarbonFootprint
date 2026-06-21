from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class BaseModel(models.Model):
    """
    Abstract base model that includes auditing and soft delete capabilities.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)


class Profile(BaseModel):
    LEVELS = (
        ('Seed', 'Seed'),
        ('Sapling', 'Sapling'),
        ('Tree', 'Tree'),
        ('Forest Guardian', 'Forest Guardian'),
        ('Planet Protector', 'Planet Protector'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.CharField(max_length=255, default='avatar_default', blank=True)
    bio = models.TextField(blank=True, max_length=500)
    green_points = models.IntegerField(default=0, db_index=True)
    level = models.CharField(max_length=30, choices=LEVELS, default='Seed')
    streak_count = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    carbon_budget = models.DecimalField(max_digits=10, decimal_places=2, default=500.00, help_text="Monthly target in kg CO2")

    def update_level(self):
        points = self.green_points
        if points >= 1000:
            self.level = 'Planet Protector'
        elif points >= 500:
            self.level = 'Forest Guardian'
        elif points >= 250:
            self.level = 'Tree'
        elif points >= 100:
            self.level = 'Sapling'
        else:
            self.level = 'Seed'
        self.save()

    def __str__(self):
        return f"{self.user.username}'s Profile (Level: {self.level})"


class EmissionCategory(BaseModel):
    CATEGORY_TYPES = (
        ('transport', 'Transportation'),
        ('energy', 'Home Energy'),
        ('food', 'Food Habits'),
        ('shopping', 'Shopping'),
        ('waste', 'Waste Management'),
    )

    name = models.CharField(max_length=100)
    key = models.CharField(max_length=100, unique=True, db_index=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, db_index=True)
    coefficient = models.DecimalField(max_digits=10, decimal_places=4, help_text="kg CO2 per unit")
    unit = models.CharField(max_length=30, help_text="e.g. km, kWh, kg, items")

    def __str__(self):
        return f"{self.name} ({self.category_type}) - {self.coefficient} kg CO2/{self.unit}"


class CarbonEntry(BaseModel):
    CATEGORIES = (
        ('transport', 'Transportation'),
        ('energy', 'Home Energy'),
        ('food', 'Food Habits'),
        ('shopping', 'Shopping'),
        ('waste', 'Waste Management'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carbon_entries')
    date = models.DateField(default=timezone.now, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORIES, db_index=True)
    inputs = models.JSONField(help_text="Detailed numeric user inputs for the category")
    emissions_co2 = models.DecimalField(max_digits=10, decimal_places=2, help_text="Emissions in kg CO2")

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.category} - {self.emissions_co2} kg CO2 ({self.date})"


class Recommendation(BaseModel):
    DIFFICULTIES = (
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    )
    COSTS = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    )
    TIMES = (
        ('Short', 'Short'),
        ('Medium', 'Medium'),
        ('Long', 'Long'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    category_type = models.CharField(max_length=20, choices=EmissionCategory.CATEGORY_TYPES)
    co2_savings_kg = models.DecimalField(max_digits=10, decimal_places=2)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTIES)
    cost_impact = models.CharField(max_length=20, choices=COSTS)
    time_required = models.CharField(max_length=20, choices=TIMES)
    environmental_benefits = models.TextField()

    def __str__(self):
        return self.title


class UserRecommendation(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_states')
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, related_name='user_states')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'recommendation')

    def __str__(self):
        return f"{self.user.username} - {self.recommendation.title} (Completed: {self.is_completed})"


class Challenge(BaseModel):
    LEVELS = (
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    level = models.CharField(max_length=20, choices=LEVELS, default='Beginner')
    points_reward = models.IntegerField(default=50)
    duration_days = models.IntegerField(default=7)
    category = models.CharField(max_length=20, choices=EmissionCategory.CATEGORY_TYPES)

    def __str__(self):
        return f"{self.title} ({self.level})"


class ChallengeProgress(BaseModel):
    STATUS_CHOICES = (
        ('Started', 'Started'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenges_progress')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='users_progress')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Started')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        unique_together = ('user', 'challenge', 'status') # allows joining same challenge again if completed/failed

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} ({self.status})"


class Badge(BaseModel):
    TYPES = (
        ('points', 'Green Points Threshold'),
        ('challenge_count', 'Challenges Completed'),
        ('entry_count', 'Carbon Calculations Recorded'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_name = models.CharField(max_length=100, default='award')
    requirement_type = models.CharField(max_length=30, choices=TYPES)
    requirement_value = models.IntegerField()

    def __str__(self):
        return self.name


class UserBadge(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')

    def __str__(self):
        return f"{self.user.username} unlocked {self.badge.name}"


class Leaderboard(models.Model):
    """
    A model to store historical snapshots or global rankings of top users based on green points.
    Typically, this can be calculated dynamically, but we define a model to save global rankings.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rank = models.IntegerField()
    points = models.IntegerField()
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['rank']

    def __str__(self):
        return f"Rank {self.rank}: {self.user.username} ({self.points} pts)"


class Article(BaseModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=100, help_text="e.g. Climate Change, Recycling")
    read_time = models.IntegerField(help_text="Read time in minutes")
    image_url = models.CharField(max_length=255, default='leaf')

    def __str__(self):
        return self.title


class Quiz(BaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    points_reward = models.IntegerField(default=30)

    def __str__(self):
        return self.title


class QuizQuestion(BaseModel):
    CHOICES = (
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    )

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=CHOICES)
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"Q for {self.quiz.title}: {self.question_text[:50]}..."


class UserQuizAttempt(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()  # percentage or correct count
    points_earned = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - Score: {self.score}"


class Notification(BaseModel):
    TYPES = (
        ('daily_reminder', 'Daily Reminder'),
        ('weekly_report', 'Weekly Report'),
        ('challenge', 'Challenge Update'),
        ('goal', 'Goal Completion'),
        ('tip', 'Sustainability Tip'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPES, default='tip')
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title} ({'Read' if self.is_read else 'Unread'})"


class Report(BaseModel):
    RANGES = (
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Annual', 'Annual'),
    )
    FORMATS = (
        ('PDF', 'PDF'),
        ('Excel', 'Excel'),
        ('CSV', 'CSV'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=200)
    range_type = models.CharField(max_length=20, choices=RANGES)
    format_type = models.CharField(max_length=10, choices=FORMATS)
    file_path = models.CharField(max_length=500)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.range_type} ({self.format_type})"


class CommunityPost(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    likes_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.user.username}: {self.title[:30]}..."


class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')


class Comment(BaseModel):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title[:20]}"

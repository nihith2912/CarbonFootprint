from rest_framework import serializers
from django.contrib.auth.models import User
from decimal import Decimal
from .models import (
    Profile, EmissionCategory, CarbonEntry, Recommendation, UserRecommendation,
    Challenge, ChallengeProgress, Badge, UserBadge, Leaderboard, Article,
    Quiz, QuizQuestion, UserQuizAttempt, Notification, Report, CommunityPost, Comment, PostLike
)
from .calculations import calculate_category_emissions


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('id', 'user', 'avatar', 'bio', 'green_points', 'level', 'streak_count', 'last_activity_date', 'carbon_budget')
        read_only_fields = ('green_points', 'level', 'streak_count', 'last_activity_date')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        # Profile is created automatically in backend or via signal. Let's make sure it is created here.
        Profile.objects.get_or_create(user=user)
        return user


class EmissionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionCategory
        fields = '__all__'


class CarbonEntrySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    emissions_co2 = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CarbonEntry
        fields = ('id', 'user', 'date', 'category', 'inputs', 'emissions_co2', 'created_at')

    def validate(self, data):
        category = data.get('category')
        inputs = data.get('inputs', {})

        if not isinstance(inputs, dict):
            raise serializers.ValidationError({"inputs": "Inputs must be a valid JSON object."})

        # Dynamically calculate the carbon footprint emissions based on the inputs
        try:
            emissions = calculate_category_emissions(category, inputs)
            self.context['calculated_emissions'] = emissions
        except Exception as e:
            raise serializers.ValidationError({"inputs": f"Error performing carbon calculation: {str(e)}"})

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        emissions = self.context.get('calculated_emissions', Decimal('0.0'))
        
        entry = CarbonEntry.objects.create(
            user=user,
            date=validated_data.get('date'),
            category=validated_data.get('category'),
            inputs=validated_data.get('inputs'),
            emissions_co2=emissions
        )
        
        # Award Green Points to profile: +10 pts per logged calculation
        profile = user.profile
        profile.green_points += 10
        profile.update_level()
        
        # Add a notification
        Notification.objects.create(
            user=user,
            title="Carbon Footprint Logged",
            message=f"You successfully logged emissions for {entry.get_category_display()}. You earned +10 Green Points!",
            notification_type='goal'
        )

        return entry


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = '__all__'


class UserRecommendationSerializer(serializers.ModelSerializer):
    recommendation = RecommendationSerializer(read_only=True)

    class Meta:
        model = UserRecommendation
        fields = ('id', 'recommendation', 'is_completed', 'completed_at')


class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = '__all__'


class ChallengeProgressSerializer(serializers.ModelSerializer):
    challenge = ChallengeSerializer(read_only=True)

    class Meta:
        model = ChallengeProgress
        fields = ('id', 'challenge', 'status', 'started_at', 'completed_at')


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = '__all__'


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ('id', 'badge', 'unlocked_at')


class LeaderboardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    level = serializers.CharField(source='user.profile.level')

    class Meta:
        model = Leaderboard
        fields = ('rank', 'username', 'points', 'level')


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'


class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ('id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'explanation')


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ('id', 'title', 'description', 'points_reward', 'questions')


class UserQuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)

    class Meta:
        model = UserQuizAttempt
        fields = ('id', 'quiz', 'quiz_title', 'score', 'points_earned', 'completed_at')


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'post', 'username', 'content', 'created_at')
        read_only_fields = ('user',)


class CommunityPostSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = ('id', 'username', 'title', 'content', 'likes_count', 'has_liked', 'comments', 'created_at')

    def get_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(user=request.user, post=obj).exists()
        return False

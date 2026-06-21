import os
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework import viewsets, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Profile, EmissionCategory, CarbonEntry, Recommendation, UserRecommendation,
    Challenge, ChallengeProgress, Badge, UserBadge, Leaderboard as LeaderboardModel,
    Article, Quiz, QuizQuestion, UserQuizAttempt, Notification, Report,
    CommunityPost, Comment, PostLike
)
from .serializers import (
    UserSerializer, ProfileSerializer, RegisterSerializer, EmissionCategorySerializer,
    CarbonEntrySerializer, RecommendationSerializer, UserRecommendationSerializer,
    ChallengeSerializer, ChallengeProgressSerializer, BadgeSerializer, UserBadgeSerializer,
    LeaderboardSerializer, ArticleSerializer, QuizSerializer, UserQuizAttemptSerializer,
    NotificationSerializer, ReportSerializer, CommunityPostSerializer, CommentSerializer
)
from .calculations import calculate_category_emissions, DEFAULT_COEFFICIENTS
from .eco_guide import generate_eco_guide_response
from .reports import create_user_report


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Award initial signup badge and points
        profile = user.profile
        profile.green_points = 20  # welcome bonus points
        profile.update_level()
        
        # Auto-unlock first badge "Eco Recruit"
        welcome_badge, _ = Badge.objects.get_or_create(
            name="Eco Recruit",
            defaults={
                "description": "Signed up to EcoTrack AI to protect the planet",
                "icon_name": "leaf",
                "requirement_type": "points",
                "requirement_value": 0
            }
        )
        UserBadge.objects.get_or_create(user=user, badge=welcome_badge)

        # Create welcome notification
        Notification.objects.create(
            user=user,
            title="Welcome to EcoTrack AI!",
            message="Your journey to save the planet has begun. Log your first activity in the Calculator tab to earn points!",
            notification_type='tip'
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "message": "User registered successfully! Check your email for verification instructions (mocked)."
        }, status=status.HTTP_201_CREATED)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        # Auto create profile if it doesn't exist for some reason
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class ForgotPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mock forgot password functionality
        user_exists = User.objects.filter(email=email).exists()
        if user_exists:
            # We mock sending a password reset token
            return Response({"message": "Password reset link has been sent to your email (mocked)."}, status=status.HTTP_200_OK)
        return Response({"error": "No user found with this email."}, status=status.HTTP_404_NOT_FOUND)


class ResetPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('password')
        if not email or not new_password:
            return Response({"error": "Email and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password reset successfully!"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User details not found."}, status=status.HTTP_404_NOT_FOUND)


# Dashboard Summary & History
class DashboardSummaryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        
        entries = CarbonEntry.objects.filter(user=user)
        total_co2 = entries.aggregate(total=Sum('emissions_co2'))['total'] or Decimal('0.0')
        
        # Monthly Emissions (current month)
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_entries = entries.filter(date__month=current_month, date__year=current_year)
        monthly_co2 = monthly_entries.aggregate(total=Sum('emissions_co2'))['total'] or Decimal('0.0')
        
        # Emission Reduction calculations vs average user benchmark
        # Benchmark: average person emits ~400 kg CO2 per month
        avg_monthly_benchmark = Decimal('400.00')
        reduction = avg_monthly_benchmark - monthly_co2 if monthly_co2 < avg_monthly_benchmark else Decimal('0.0')
        
        # Trees saved: 1 tree absorbs ~22kg of CO2 per year (~1.83kg per month)
        # Trees saved is calculated from cumulative lifetime reduction vs a standard benchmark of 400kg/mo
        days_since_signup = (timezone.now() - user.date_joined).days or 1
        months_since_signup = Decimal(str(max(1, days_since_signup // 30)))
        expected_benchmark = avg_monthly_benchmark * months_since_signup
        
        lifetime_reduction = expected_benchmark - total_co2 if total_co2 < expected_benchmark else Decimal('0.0')
        trees_saved = float(lifetime_reduction) / 22.0

        # Challenges completed count
        completed_challenges = ChallengeProgress.objects.filter(user=user, status='Completed').count()

        return Response({
            "total_carbon_footprint": round(total_co2, 2),
            "monthly_emissions": round(monthly_co2, 2),
            "emission_reduction": round(reduction, 2),
            "sustainability_score": max(10, min(100, int(100 - (float(monthly_co2)/float(avg_monthly_benchmark)*50) if monthly_co2 > 0 else 100))),
            "completed_challenges": completed_challenges,
            "trees_saved": round(trees_saved, 2),
            "green_points": profile.green_points,
            "level": profile.level,
            "carbon_budget": profile.carbon_budget
        })


class DashboardHistoryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        entries = CarbonEntry.objects.filter(user=user).order_by('date')
        
        # Daily history (last 7 days)
        today = timezone.now().date()
        daily_data = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            day_total = entries.filter(date=d).aggregate(total=Sum('emissions_co2'))['total'] or Decimal('0.0')
            daily_data.append({
                "label": d.strftime('%a'),
                "value": float(day_total)
            })

        # Weekly history (last 4 weeks)
        weekly_data = []
        for i in range(3, -1, -1):
            start = today - timedelta(weeks=i+1)
            end = today - timedelta(weeks=i)
            week_total = entries.filter(date__gt=start, date__lte=end).aggregate(total=Sum('emissions_co2'))['total'] or Decimal('0.0')
            weekly_data.append({
                "label": f"Wk -{i}",
                "value": float(week_total)
            })

        # Monthly history (last 6 months)
        monthly_data = []
        for i in range(5, -1, -1):
            # approximate 30-day blocks
            start = today - timedelta(days=(i+1)*30)
            end = today - timedelta(days=i*30)
            month_total = entries.filter(date__gt=start, date__lte=end).aggregate(total=Sum('emissions_co2'))['total'] or Decimal('0.0')
            monthly_data.append({
                "label": end.strftime('%b'),
                "value": float(month_total)
            })

        # Category distribution percentages
        cat_totals = entries.values('category').annotate(total=Sum('emissions_co2'))
        category_distribution = []
        total_all = sum([c['total'] for c in cat_totals]) or Decimal('1.0')
        for cat in cat_totals:
            category_distribution.append({
                "category": cat['category'].title(),
                "value": float(cat['total']),
                "percentage": round(float(cat['total'] / total_all) * 100, 1)
            })

        # Comparison average benchmark: user vs average user per category
        # Baseline benchmarks in kg CO2 per month: Transport 150, Energy 150, Food 60, Shopping 30, Waste 10
        user_cat_monthly = entries.filter(date__gte=today - timedelta(days=30)).values('category').annotate(total=Sum('emissions_co2'))
        user_cat_map = {c['category']: float(c['total']) for c in user_cat_monthly}
        
        benchmarks = {
            'transport': 150.0,
            'energy': 150.0,
            'food': 60.0,
            'shopping': 30.0,
            'waste': 10.0
        }
        
        comparison_data = []
        for key, name in [('transport', 'Transport'), ('energy', 'Energy'), ('food', 'Food'), ('shopping', 'Shopping'), ('waste', 'Waste')]:
            comparison_data.append({
                "category": name,
                "user": user_cat_map.get(key, 0.0),
                "average": benchmarks[key]
            })

        return Response({
            "daily": daily_data,
            "weekly": weekly_data,
            "monthly": monthly_data,
            "category_distribution": category_distribution,
            "comparison": comparison_data
        })


# Carbon Calculations List & Entries API
class EmissionCategoryListView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        categories = EmissionCategory.objects.all()
        if not categories.exists():
            # If DB not seeded, return defaults
            return Response(DEFAULT_COEFFICIENTS)
        
        serializer = EmissionCategorySerializer(categories, many=True)
        return Response(serializer.data)


class CarbonCalculateDryRunView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        category = request.data.get('category')
        inputs = request.data.get('inputs', {})
        if not category or not inputs:
            return Response({"error": "Category and inputs are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            emissions = calculate_category_emissions(category, inputs)
            return Response({
                "category": category,
                "calculated_emissions_co2": float(emissions),
                "unit": "kg"
            })
        except Exception as e:
            return Response({"error": f"Calculation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class CarbonEntryViewSet(viewsets.ModelViewSet):
    serializer_class = CarbonEntrySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return CarbonEntry.objects.filter(user=self.request.user).order_by('-date', '-created_at')

    def perform_create(self, serializer):
        serializer.save()


# AI Sustainability Coach Chat API
class EcoGuideChatView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        message = request.data.get('message')
        if not message:
            return Response({"error": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        response_text = generate_eco_guide_response(request.user, message)
        return Response({
            "reply": response_text,
            "coach": "EcoGuide AI"
        })


# Personalized Recommendations Engine
class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecommendationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Recommendation.objects.all().order_by('id')

    @action(detail=False, methods=['GET'], url_path='personalized')
    def personalized(self, request):
        user = request.user
        # Look at user's highest footprint category to rank recommendations
        highest_cat = CarbonEntry.objects.filter(user=user).values('category').annotate(total=Sum('emissions_co2')).order_by('-total')
        
        if highest_cat.exists():
            primary_category = highest_cat[0]['category']
            # Fetch recommendations of primary category first, then others
            recs = list(Recommendation.objects.filter(category_type=primary_category)) + list(Recommendation.objects.exclude(category_type=primary_category))
        else:
            recs = Recommendation.objects.all()

        completed_ids = UserRecommendation.objects.filter(user=user, is_completed=True).values_list('recommendation_id', flat=True)
        
        serializer = self.get_serializer(recs, many=True)
        # Inject completed status
        results = []
        for item in serializer.data:
            item['is_completed'] = item['id'] in completed_ids
            results.append(item)

        return Response(results)

    @action(detail=True, methods=['POST'], url_path='complete')
    def complete(self, request, pk=None):
        recommendation = self.get_object()
        user = request.user
        
        user_rec, created = UserRecommendation.objects.get_or_create(
            user=user,
            recommendation=recommendation
        )
        if user_rec.is_completed:
            return Response({"message": "Already completed!"}, status=status.HTTP_400_BAD_REQUEST)

        user_rec.is_completed = True
        user_rec.completed_at = timezone.now()
        user_rec.save()

        # Award points: +30 points for completing a recommendation
        profile = user.profile
        profile.green_points += 30
        profile.update_level()

        # Notification
        Notification.objects.create(
            user=user,
            title="Recommendation Completed!",
            message=f"You completed: '{recommendation.title}' and saved {recommendation.co2_savings_kg} kg of CO₂! +30 Green Points awarded.",
            notification_type='goal'
        )

        # Streak trigger verification
        self._check_streak(profile)

        # Check badges
        self._check_badges(user)

        return Response({
            "message": "Recommendation marked as completed!",
            "green_points": profile.green_points,
            "level": profile.level
        })

    def _check_streak(self, profile):
        today = timezone.now().date()
        if profile.last_activity_date == today - timedelta(days=1):
            profile.streak_count += 1
        elif profile.last_activity_date != today:
            profile.streak_count = 1
        profile.last_activity_date = today
        profile.save(update_fields=['streak_count', 'last_activity_date'])

    def _check_badges(self, user):
        points = user.profile.green_points
        challenges_count = ChallengeProgress.objects.filter(user=user, status='Completed').count()
        entries_count = CarbonEntry.objects.filter(user=user).count()

        badges = Badge.objects.all()
        for badge in badges:
            unlocked = False
            if badge.requirement_type == 'points' and points >= badge.requirement_value:
                unlocked = True
            elif badge.requirement_type == 'challenge_count' and challenges_count >= badge.requirement_value:
                unlocked = True
            elif badge.requirement_type == 'entry_count' and entries_count >= badge.requirement_value:
                unlocked = True

            if unlocked:
                # Award badge
                ub, created = UserBadge.objects.get_or_create(user=user, badge=badge)
                if created:
                    Notification.objects.create(
                        user=user,
                        title="New Badge Unlocked!",
                        message=f"Congratulations! You unlocked the '{badge.name}' badge: {badge.description}.",
                        notification_type='challenge'
                    )


# Challenges
class ChallengeViewSet(viewsets.ModelViewSet):
    serializer_class = ChallengeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Challenge.objects.all().order_by('id')

    @action(detail=True, methods=['POST'], url_path='join')
    def join(self, request, pk=None):
        challenge = self.get_object()
        user = request.user
        
        progress, created = ChallengeProgress.objects.get_or_create(
            user=user,
            challenge=challenge,
            status='Started'
        )
        if not created:
            return Response({"error": "You already started this challenge."}, status=status.HTTP_400_BAD_REQUEST)

        # Notify user
        Notification.objects.create(
            user=user,
            title="Challenge Started!",
            message=f"You joined the '{challenge.title}' challenge. Complete it in {challenge.duration_days} days to claim {challenge.points_reward} points!",
            notification_type='challenge'
        )

        return Response({
            "message": "Challenge joined successfully!",
            "status": "Started"
        })

    @action(detail=True, methods=['POST'], url_path='complete')
    def complete(self, request, pk=None):
        challenge = self.get_object()
        user = request.user

        try:
            progress = ChallengeProgress.objects.get(user=user, challenge=challenge, status='Started')
        except ChallengeProgress.DoesNotExist:
            return Response({"error": "You are not active in this challenge."}, status=status.HTTP_400_BAD_REQUEST)

        progress.status = 'Completed'
        progress.completed_at = timezone.now()
        progress.save()

        # Award rewards
        profile = user.profile
        profile.green_points += challenge.points_reward
        profile.update_level()

        # Streak check
        profile.last_activity_date = timezone.now().date()
        profile.save(update_fields=['last_activity_date'])

        # Notify
        Notification.objects.create(
            user=user,
            title="Challenge Completed!",
            message=f"Bravo! You finished '{challenge.title}' and earned +{challenge.points_reward} Green Points!",
            notification_type='goal'
        )

        # Unlock badges verification
        RecommendationViewSet()._check_badges(user)

        return Response({
            "message": "Challenge completed successfully!",
            "green_points": profile.green_points,
            "level": profile.level
        })


# Leaderboard view
class LeaderboardAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        profiles = Profile.objects.order_by('-green_points')
        rankings = []
        for rank, profile in enumerate(profiles[:50], 1): # Top 50 rankings
            rankings.append({
                "rank": rank,
                "username": profile.user.username,
                "points": profile.green_points,
                "level": profile.level
            })
        
        # Find current user rank
        user_profile = request.user.profile
        user_rank = 1
        for idx, p in enumerate(profiles):
            if p.user == request.user:
                user_rank = idx + 1
                break

        return Response({
            "leaderboard": rankings,
            "user_rank": {
                "rank": user_rank,
                "points": user_profile.green_points,
                "level": user_profile.level
            }
        })


# Educational Hub
class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ArticleSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Article.objects.all().order_by('id')


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QuizSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Quiz.objects.all().order_by('id')

    @action(detail=True, methods=['POST'], url_path='submit')
    def submit(self, request, pk=None):
        quiz = self.get_object()
        user = request.user
        answers = request.data.get('answers', {}) # format: {"question_id": "A"}

        # Fetch questions
        questions = quiz.questions.all()
        correct_count = 0
        total_questions = questions.count()
        
        if total_questions == 0:
            return Response({"error": "No questions inside this quiz."}, status=status.HTTP_400_BAD_REQUEST)

        results = {}
        for q in questions:
            user_ans = answers.get(str(q.id))
            is_correct = user_ans == q.correct_option
            if is_correct:
                correct_count += 1
            results[q.id] = {
                "correct": is_correct,
                "correct_option": q.correct_option,
                "explanation": q.explanation
            }

        score = int((correct_count / total_questions) * 100)
        points_earned = int((score / 100) * quiz.points_reward)

        # Log attempt
        attempt = UserQuizAttempt.objects.create(
            user=user,
            quiz=quiz,
            score=score,
            points_earned=points_earned
        )

        if points_earned > 0:
            profile = user.profile
            profile.green_points += points_earned
            profile.update_level()
            
            Notification.objects.create(
                user=user,
                title="Quiz Completed!",
                message=f"You scored {score}% on quiz '{quiz.title}' and earned +{points_earned} Green Points!",
                notification_type='goal'
            )

        return Response({
            "score": score,
            "points_earned": points_earned,
            "results": results
        })


# Community Forum
class CommunityPostViewSet(viewsets.ModelViewSet):
    serializer_class = CommunityPostSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = CommunityPost.objects.all().prefetch_related('comments', 'likes').order_by('-created_at')

    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)
        # Award +5 green points for sharing a sustainability tip
        profile = self.request.user.profile
        profile.green_points += 5
        profile.update_level()

    @action(detail=True, methods=['POST'], url_path='like')
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user
        
        like_qs = PostLike.objects.filter(user=user, post=post)
        if like_qs.exists():
            like_qs.delete()
            post.likes_count = max(0, post.likes_count - 1)
            post.save(update_fields=['likes_count'])
            return Response({"liked": False, "likes_count": post.likes_count})
        
        PostLike.objects.create(user=user, post=post)
        post.likes_count += 1
        post.save(update_fields=['likes_count'])
        return Response({"liked": True, "likes_count": post.likes_count})

    @action(detail=True, methods=['POST'], url_path='comment')
    def add_comment(self, request, pk=None):
        post = self.get_object()
        content = request.data.get('content')
        if not content:
            return Response({"error": "Content is required."}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(
            post=post,
            user=request.user,
            content=content
        )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


# Notifications & Reports
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['POST'], url_path='read')
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({"status": "read"})


class ReportGenerateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        reports = Report.objects.filter(user=request.user).order_by('-generated_at')
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data)

    def post(self, request):
        range_type = request.data.get('range_type') # Daily, Weekly, Monthly, Annual
        format_type = request.data.get('format_type') # PDF, Excel, CSV

        if range_type not in ['Daily', 'Weekly', 'Monthly', 'Annual']:
            return Response({"error": "Invalid range_type. Choose Daily, Weekly, Monthly, or Annual."}, status=status.HTTP_400_BAD_REQUEST)
        if format_type not in ['PDF', 'Excel', 'CSV']:
            return Response({"error": "Invalid format_type. Choose PDF, Excel, or CSV."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            report_db = create_user_report(request.user, range_type, format_type)
            serializer = ReportSerializer(report_db)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Failed to generate report: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

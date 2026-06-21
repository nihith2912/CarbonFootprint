from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterView, ProfileView, ForgotPasswordView, ResetPasswordView,
    DashboardSummaryView, DashboardHistoryView, EmissionCategoryListView,
    CarbonCalculateDryRunView, CarbonEntryViewSet, EcoGuideChatView,
    RecommendationViewSet, ChallengeViewSet, LeaderboardAPIView,
    ArticleViewSet, QuizViewSet, CommunityPostViewSet, NotificationViewSet,
    ReportGenerateView
)

router = DefaultRouter()
router.register(r'carbon/entries', CarbonEntryViewSet, basename='carbon-entries')
router.register(r'recommendations', RecommendationViewSet, basename='recommendations')
router.register(r'challenges', ChallengeViewSet, basename='challenges')
router.register(r'articles', ArticleViewSet, basename='articles')
router.register(r'quizzes', QuizViewSet, basename='quizzes')
router.register(r'community/posts', CommunityPostViewSet, basename='community-posts')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    # Router ViewSets
    path('', include(router.urls)),

    # Authentication
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='auth-reset-password'),
    
    # Profile
    path('profile/', ProfileView.as_view(), name='profile-detail'),

    # Analytics / Dashboard
    path('analytics/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('analytics/history/', DashboardHistoryView.as_view(), name='dashboard-history'),

    # Carbon Calc Config
    path('carbon/categories/', EmissionCategoryListView.as_view(), name='carbon-categories'),
    path('carbon/calculate/', CarbonCalculateDryRunView.as_view(), name='carbon-calculate-dryrun'),

    # AI Coach Chat
    path('coach/chat/', EcoGuideChatView.as_view(), name='coach-chat'),

    # Leaderboard
    path('leaderboard/', LeaderboardAPIView.as_view(), name='leaderboard'),

    # Reports
    path('reports/generate/', ReportGenerateView.as_view(), name='reports-generate'),
]

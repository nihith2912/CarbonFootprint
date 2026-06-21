from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import CarbonEntry, EmissionCategory, Recommendation, Quiz, QuizQuestion, Profile
from .calculations import calculate_category_emissions


class CarbonCalculationTestCase(TestCase):
    def setUp(self):
        # Set up categories with custom coefficients
        EmissionCategory.objects.create(key='transport_car_petrol', name='Car (Petrol)', category_type='transport', coefficient=0.18, unit='km')
        EmissionCategory.objects.create(key='transport_bike', name='Bike', category_type='transport', coefficient=0.08, unit='km')
        EmissionCategory.objects.create(key='energy_electricity', name='Electricity', category_type='energy', coefficient=0.50, unit='kWh')
        EmissionCategory.objects.create(key='food_vegan', name='Vegan Diet', category_type='food', coefficient=1.50, unit='day')
        EmissionCategory.objects.create(key='food_waste', name='Food Waste', category_type='food', coefficient=2.50, unit='kg')

    def test_transport_calculation(self):
        inputs = {
            'trips_per_week': 2,
            'car_distance': 100, # 100km by car
            'fuel_type': 'petrol',
            'bike_distance': 50,  # 50km by bike
        }
        # expected car emissions = 100 * 0.18 * 2 = 36.00
        # expected bike emissions = 50 * 0.08 * 2 = 8.00
        # total expected = 44.00
        emissions = calculate_category_emissions('transport', inputs)
        self.assertEqual(emissions, Decimal('44.00'))

    def test_energy_calculation(self):
        inputs = {
            'electricity_kwh': 200, # 200 kWh
            'lpg_kg': 0,
            'ac_hours': 0,
            'appliance_hours': 0,
        }
        # expected = 200 * 0.50 = 100.00
        emissions = calculate_category_emissions('energy', inputs)
        self.assertEqual(emissions, Decimal('100.00'))

    def test_food_calculation(self):
        inputs = {
            'diet_type': 'vegan',
            'food_waste_kg': 4 # 4 kg wasted
        }
        # expected diet = 1.50 * 7 days = 10.50
        # expected waste = 4 * 2.50 = 10.00
        # total expected = 20.50
        emissions = calculate_category_emissions('food', inputs)
        self.assertEqual(emissions, Decimal('20.50'))


class APIEndpointsTestCase(APITestCase):
    def setUp(self):
        # Create user
        self.username = 'ecotester'
        self.password = 'superpass123'
        self.email = 'tester@ecotrack.ai'
        self.user = User.objects.create_user(
            username=self.username, password=self.password, email=self.email
        )
        self.profile = Profile.objects.create(user=self.user)

        # Seed categories needed for endpoints
        EmissionCategory.objects.create(key='transport_car_petrol', name='Car (Petrol)', category_type='transport', coefficient=0.18, unit='km')

        # Obtain JWT Token
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_profile_retrieval(self):
        url = reverse('profile-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], self.username)

    def test_create_carbon_entry(self):
        url = reverse('carbon-entries-list')
        data = {
            'category': 'transport',
            'inputs': {
                'trips_per_week': 1,
                'car_distance': 50,
                'fuel_type': 'petrol'
            },
            'date': '2026-06-20'
        }
        # expected emissions: 50 * 0.18 * 1 = 9.00
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['emissions_co2']), 9.00)
        
        # Check that green points are awarded (+10)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.green_points, 10)

    def test_quiz_submission(self):
        quiz = Quiz.objects.create(title='General Science', description='Clean Energy Quiz', points_reward=50)
        question = QuizQuestion.objects.create(
            quiz=quiz,
            question_text='What is the chemical symbol for carbon dioxide?',
            option_a='CO',
            option_b='CO2',
            option_c='O2',
            option_d='CH4',
            correct_option='B'
        )
        
        url = reverse('quizzes-submit', kwargs={'pk': quiz.id})
        data = {
            'answers': {
                str(question.id): 'B'
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['score'], 100)
        self.assertEqual(response.data['points_earned'], 50)

        # Verify profile updated
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.green_points, 50)

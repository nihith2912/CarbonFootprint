from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import (
    EmissionCategory, Recommendation, Challenge, Badge, Article, Quiz, QuizQuestion, Profile
)
from api.calculations import DEFAULT_COEFFICIENTS


class Command(BaseCommand):
    help = 'Seeds initial default data for EcoTrack AI platform'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding Emission Categories...')
        for key, val in DEFAULT_COEFFICIENTS.items():
            EmissionCategory.objects.update_or_create(
                key=key,
                defaults={
                    'name': val['name'],
                    'category_type': val['category_type'],
                    'coefficient': val['coeff'],
                    'unit': val['unit']
                }
            )

        self.stdout.write('Seeding Recommendations...')
        recommendations = [
            {
                'title': 'Switch to LED Light Bulbs',
                'description': 'Replace traditional incandescent light bulbs with ENERGY STAR certified LEDs in your home.',
                'category_type': 'energy',
                'co2_savings_kg': 15.50,
                'difficulty': 'Easy',
                'cost_impact': 'Low',
                'time_required': 'Short',
                'environmental_benefits': 'LEDs use 75-80% less energy and last up to 25 times longer than standard bulbs.'
            },
            {
                'title': 'Start Commuting by Bicycle',
                'description': 'Ride a bike to work, school, or errands instead of driving a single-occupancy petrol vehicle.',
                'category_type': 'transport',
                'co2_savings_kg': 85.00,
                'difficulty': 'Hard',
                'cost_impact': 'Medium',
                'time_required': 'Medium',
                'environmental_benefits': 'Eliminates direct emissions from fossil fuels and reduces overall highway congestion.'
            },
            {
                'title': 'Adopt a Meatless Monday habit',
                'description': 'Eliminate meat products from your diet for at least one day every week.',
                'category_type': 'food',
                'co2_savings_kg': 35.00,
                'difficulty': 'Medium',
                'cost_impact': 'Low',
                'time_required': 'Short',
                'environmental_benefits': 'Livestock farming produces vast methane emissions. Plant-based diets use significantly less land and water resources.'
            },
            {
                'title': 'Upgrade to a Smart Thermostat',
                'description': 'Install a smart thermostat to control temperature scheduling and reduce AC runtime.',
                'category_type': 'energy',
                'co2_savings_kg': 45.00,
                'difficulty': 'Medium',
                'cost_impact': 'High',
                'time_required': 'Medium',
                'environmental_benefits': 'Reduces household electricity demand by automatically optimizing heating and cooling when you are away.'
            },
            {
                'title': 'Compost Organic Household Waste',
                'description': 'Set up a compost bin for kitchen scrap and garden waste instead of throwing it in landfill bins.',
                'category_type': 'waste',
                'co2_savings_kg': 20.00,
                'difficulty': 'Medium',
                'cost_impact': 'Low',
                'time_required': 'Long',
                'environmental_benefits': 'Landfill organic waste decomposes anaerobically producing high methane gas. Composting stores nutrients cleanly.'
            },
            {
                'title': 'Buy Circular/Preowned Clothes',
                'description': 'Purchase second-hand clothing items and donate old garments instead of fast fashion brands.',
                'category_type': 'shopping',
                'co2_savings_kg': 25.00,
                'difficulty': 'Easy',
                'cost_impact': 'Low',
                'time_required': 'Medium',
                'environmental_benefits': 'Reduces landfill waste and saves thousands of liters of water required for manufacturing new cotton garments.'
            }
        ]

        for rec in recommendations:
            Recommendation.objects.update_or_create(
                title=rec['title'],
                defaults=rec
            )

        self.stdout.write('Seeding Challenges...')
        challenges = [
            {
                'title': 'Avoid Plastic Bottles for 7 Days',
                'description': 'Do not buy or use any single-use plastic beverage bottles. Use a refillable metal/glass container instead.',
                'level': 'Beginner',
                'points_reward': 50,
                'duration_days': 7,
                'category': 'waste'
            },
            {
                'title': 'Switch Off Lights for One Week',
                'description': 'Ensure lights and electronic devices in unoccupied rooms are completely turned off for a full week.',
                'level': 'Beginner',
                'points_reward': 40,
                'duration_days': 7,
                'category': 'energy'
            },
            {
                'title': 'Use Public Transport for 10 Days',
                'description': 'Leave the private car parked. Use buses, trains, or carpools for all your major travel needs.',
                'level': 'Intermediate',
                'points_reward': 120,
                'duration_days': 10,
                'category': 'transport'
            },
            {
                'title': 'Reduce Meat Intake for One Month',
                'description': 'Commit to eating plant-based breakfasts and lunches, keeping meat consumption to a absolute minimum for 30 days.',
                'level': 'Intermediate',
                'points_reward': 200,
                'duration_days': 30,
                'category': 'food'
            },
            {
                'title': 'Zero-Waste Challenge Week',
                'description': 'Recycle and compost everything possible, aiming to create zero landfill bags of trash for a full week.',
                'level': 'Advanced',
                'points_reward': 250,
                'duration_days': 7,
                'category': 'waste'
            },
            {
                'title': 'No Private Vehicles Month',
                'description': 'Strictly use walk, bike, public transport, or EV transit options for all commutes during the calendar month.',
                'level': 'Advanced',
                'points_reward': 500,
                'duration_days': 30,
                'category': 'transport'
            }
        ]

        for chal in challenges:
            Challenge.objects.update_or_create(
                title=chal['title'],
                defaults=chal
            )

        self.stdout.write('Seeding Achievement Badges...')
        badges = [
            {
                'name': 'Eco Recruit',
                'description': 'Unlock this badge automatically when you sign up to start tracking your footprint.',
                'icon_name': 'leaf',
                'requirement_type': 'points',
                'requirement_value': 0
            },
            {
                'name': 'Carbon Conscious',
                'description': 'Log your first 5 carbon entries in the EcoTrack Calculator.',
                'icon_name': 'calculator',
                'requirement_type': 'entry_count',
                'requirement_value': 5
            },
            {
                'name': 'Green Hero',
                'description': 'Reach over 250 green points through completing challenges and quizzes.',
                'icon_name': 'award',
                'requirement_type': 'points',
                'requirement_value': 250
            },
            {
                'name': 'Challenge Champion',
                'description': 'Successfully finish 3 sustainability challenges.',
                'icon_name': 'trophy',
                'requirement_type': 'challenge_count',
                'requirement_value': 3
            },
            {
                'name': 'Earth Guardian',
                'description': 'Amass 1,000 green points to achieve top eco levels.',
                'icon_name': 'globe',
                'requirement_type': 'points',
                'requirement_value': 1000
            }
        ]

        for bg in badges:
            Badge.objects.update_or_create(
                name=bg['name'],
                defaults=bg
            )

        self.stdout.write('Seeding Educational Articles...')
        articles = [
            {
                'title': 'The Science of Climate Change Explained',
                'content': 'Climate change refers to long-term shifts in temperatures and weather patterns. These shifts may be natural, but since the 1800s, human activities have been the main driver of climate change, primarily due to burning fossil fuels like coal, oil, and gas, which produces heat-trapping greenhouse gases.',
                'category': 'Climate Change',
                'read_time': 5,
                'image_url': 'fire'
            },
            {
                'title': 'Understanding Carbon Footprint Basics',
                'content': 'A carbon footprint is the total amount of greenhouse gases (including carbon dioxide and methane) that are generated by our actions. The average carbon footprint for a person in the United States is 16 tons, one of the highest rates in the world. Globally, the average is closer to 4 tons.',
                'category': 'Carbon Footprint Basics',
                'read_time': 4,
                'image_url': 'calculator'
            },
            {
                'title': '5 Simple Steps to Sustainable Living',
                'content': 'Transitioning to sustainable living does not happen overnight. Start with simple actions: 1) Say no to single-use plastics, 2) Choose energy-efficient appliances, 3) Switch to a diet with more plants, 4) Practice active recycling and composting, and 5) Opt for low-carbon travel alternatives.',
                'category': 'Sustainable Living',
                'read_time': 6,
                'image_url': 'seedling'
            },
            {
                'title': 'The Role of Renewable Energy systems',
                'content': 'Renewable energy is energy derived from natural sources that are replenished at a higher rate than they are consumed. Solar, wind, geothermal, and hydroelectric power are great clean energy sources. Relying on green grids is the fastest way to eliminate household scope-2 carbon emissions.',
                'category': 'Renewable Energy',
                'read_time': 7,
                'image_url': 'sun'
            },
            {
                'title': 'Demystifying Recycling Codes and Sorting',
                'content': 'Not all materials can be recycled. Knowing plastic numbers (1 to 7) helps you sort waste correctly. Resin codes #1 (PET) and #2 (HDPE) are highly recyclable in standard municipal curbside recycling systems, whereas codes like #3 (PVC) and #6 (Polystyrene) must be handled at specialty centers.',
                'category': 'Recycling',
                'read_time': 5,
                'image_url': 'recycle'
            }
        ]

        for art in articles:
            Article.objects.update_or_create(
                title=art['title'],
                defaults=art
            )

        self.stdout.write('Seeding Quizzes...')
        
        # Quiz 1
        q1, _ = Quiz.objects.update_or_create(
            title='Carbon Footprint 101',
            defaults={'description': 'Test your basic knowledge of greenhouse gas sources, footprints and environmental impact.', 'points_reward': 50}
        )
        QuizQuestion.objects.update_or_create(
            quiz=q1,
            question_text='Which category typically contributes the largest share of an average individual’s carbon footprint in developed countries?',
            defaults={
                'option_a': 'Waste generation',
                'option_b': 'Transportation and energy usage',
                'option_c': 'Clothes shopping',
                'option_d': 'LPG consumption',
                'correct_option': 'B',
                'explanation': 'Car travel, flights, and home electricity/heating fuel dominate individual emissions.'
            }
        )
        QuizQuestion.objects.update_or_create(
            quiz=q1,
            question_text='What is the primary greenhouse gas emitted by human activities?',
            defaults={
                'option_a': 'Methane (CH4)',
                'option_b': 'Nitrous Oxide (N2O)',
                'option_c': 'Carbon Dioxide (CO2)',
                'option_d': 'Ozone (O3)',
                'correct_option': 'C',
                'explanation': 'Carbon Dioxide (CO2) accounts for the largest volume of global greenhouse gases.'
            }
        )

        # Quiz 2
        q2, _ = Quiz.objects.update_or_create(
            title='Clean Energy & Waste Mastery',
            defaults={'description': 'Prove your skills on renewable energy facts and sorting household plastics.', 'points_reward': 50}
        )
        QuizQuestion.objects.update_or_create(
            quiz=q2,
            question_text='Which plastic resin code represents PET/PETE (most common soda/water bottles)?',
            defaults={
                'option_a': 'Resin Code #1',
                'option_b': 'Resin Code #2',
                'option_c': 'Resin Code #5',
                'option_d': 'Resin Code #7',
                'correct_option': 'A',
                'explanation': 'PET is Resin Code 1 and is the most widely recycled plastic material.'
            }
        )
        QuizQuestion.objects.update_or_create(
            quiz=q2,
            question_text='Which clean energy source uses heat from deep within the earth?',
            defaults={
                'option_a': 'Hydroelectric',
                'option_b': 'Geothermal Energy',
                'option_c': 'Solar Photovoltaic',
                'option_d': 'Biomass',
                'correct_option': 'B',
                'explanation': 'Geothermal systems harness core earth thermal heat to power turbines.'
            }
        )

        # Add admin/mock users if none exist for easy testing
        if not User.objects.filter(is_superuser=True).exists():
            admin_user = User.objects.create_superuser('admin', 'admin@ecotrack.ai', 'adminpass123')
            Profile.objects.get_or_create(user=admin_user)
            self.stdout.write("Created Superuser: admin | Password: adminpass123")

        self.stdout.write(self.style.SUCCESS('Successfully seeded all EcoTrack AI default data!'))

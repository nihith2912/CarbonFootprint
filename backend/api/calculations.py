from decimal import Decimal
from .models import EmissionCategory

# Default emission coefficients (kg CO2 per unit) in case DB is not seeded
DEFAULT_COEFFICIENTS = {
    # Transportation (unit: km)
    'transport_car_petrol': {'name': 'Car (Petrol)', 'category_type': 'transport', 'coeff': 0.18, 'unit': 'km'},
    'transport_car_diesel': {'name': 'Car (Diesel)', 'category_type': 'transport', 'coeff': 0.17, 'unit': 'km'},
    'transport_car_electric': {'name': 'Car (Electric)', 'category_type': 'transport', 'coeff': 0.05, 'unit': 'km'},
    'transport_car_hybrid': {'name': 'Car (Hybrid/HEV)', 'category_type': 'transport', 'coeff': 0.11, 'unit': 'km'},
    'transport_car_phev': {'name': 'Car (Plug-in Hybrid/PHEV)', 'category_type': 'transport', 'coeff': 0.07, 'unit': 'km'},
    'transport_car_cng': {'name': 'Car (CNG)', 'category_type': 'transport', 'coeff': 0.13, 'unit': 'km'},
    'transport_car_lpg': {'name': 'Car (LPG)', 'category_type': 'transport', 'coeff': 0.14, 'unit': 'km'},
    'transport_car_biodiesel': {'name': 'Car (Biodiesel)', 'category_type': 'transport', 'coeff': 0.09, 'unit': 'km'},
    'transport_car_ethanol': {'name': 'Car (Ethanol/E85)', 'category_type': 'transport', 'coeff': 0.12, 'unit': 'km'},
    'transport_car_hydrogen': {'name': 'Car (Hydrogen Fuel Cell)', 'category_type': 'transport', 'coeff': 0.02, 'unit': 'km'},
    'transport_car_mild_hybrid': {'name': 'Car (Mild Hybrid/MHEV)', 'category_type': 'transport', 'coeff': 0.15, 'unit': 'km'},
    'transport_car_flex_fuel': {'name': 'Car (Flex-Fuel)', 'category_type': 'transport', 'coeff': 0.13, 'unit': 'km'},
    'transport_car_synthetic': {'name': 'Car (Synthetic E-Fuel)', 'category_type': 'transport', 'coeff': 0.08, 'unit': 'km'},
    'transport_car_solar_ev': {'name': 'Car (Solar-assisted EV)', 'category_type': 'transport', 'coeff': 0.01, 'unit': 'km'},
    'transport_car_petrol_cng': {'name': 'Car (Petrol + CNG Hybrid)', 'category_type': 'transport', 'coeff': 0.15, 'unit': 'km'},
    'transport_bike': {'name': 'Motorcycle/Bike', 'category_type': 'transport', 'coeff': 0.08, 'unit': 'km'},
    'transport_bus': {'name': 'Bus Ride', 'category_type': 'transport', 'coeff': 0.03, 'unit': 'km'},
    'transport_train': {'name': 'Train Ride', 'category_type': 'transport', 'coeff': 0.02, 'unit': 'km'},
    'transport_flight': {'name': 'Flight Journey', 'category_type': 'transport', 'coeff': 0.15, 'unit': 'km'},

    # Home Energy (unit: kWh, kg, hour)
    'energy_electricity': {'name': 'Grid Electricity', 'category_type': 'energy', 'coeff': 0.50, 'unit': 'kWh'},
    'energy_lpg': {'name': 'LPG Consumption', 'category_type': 'energy', 'coeff': 3.00, 'unit': 'kg'},
    'energy_ac': {'name': 'Air Conditioning Use', 'category_type': 'energy', 'coeff': 0.60, 'unit': 'hour'},
    'energy_appliances': {'name': 'Home Appliances Use', 'category_type': 'energy', 'coeff': 0.15, 'unit': 'hour'},

    # Food Habits (unit: days/week, kg)
    'food_vegan': {'name': 'Vegan Diet Factor', 'category_type': 'food', 'coeff': 1.50, 'unit': 'day'},
    'food_vegetarian': {'name': 'Vegetarian Diet Factor', 'category_type': 'food', 'coeff': 2.50, 'unit': 'day'},
    'food_eggetarian': {'name': 'Eggetarian Diet Factor', 'category_type': 'food', 'coeff': 3.20, 'unit': 'day'},
    'food_non_veg': {'name': 'Non-Vegetarian Diet Factor', 'category_type': 'food', 'coeff': 5.00, 'unit': 'day'},
    'food_pescatarian': {'name': 'Pescatarian Diet Factor', 'category_type': 'food', 'coeff': 3.80, 'unit': 'day'},
    'food_flexitarian': {'name': 'Flexitarian Diet Factor', 'category_type': 'food', 'coeff': 4.20, 'unit': 'day'},
    'food_keto': {'name': 'Keto Diet Factor', 'category_type': 'food', 'coeff': 5.50, 'unit': 'day'},
    'food_paleo': {'name': 'Paleo Diet Factor', 'category_type': 'food', 'coeff': 5.80, 'unit': 'day'},
    'food_mediterranean': {'name': 'Mediterranean Diet Factor', 'category_type': 'food', 'coeff': 3.00, 'unit': 'day'},
    'food_carnivore': {'name': 'Carnivore Diet Factor', 'category_type': 'food', 'coeff': 8.00, 'unit': 'day'},
    'food_low_carb': {'name': 'Low-Carb Diet Factor', 'category_type': 'food', 'coeff': 4.80, 'unit': 'day'},
    'food_gluten_free': {'name': 'Gluten-Free Diet Factor', 'category_type': 'food', 'coeff': 2.80, 'unit': 'day'},
    'food_dairy_free': {'name': 'Dairy-Free Diet Factor', 'category_type': 'food', 'coeff': 2.40, 'unit': 'day'},
    'food_whole30': {'name': 'Whole30 Diet Factor', 'category_type': 'food', 'coeff': 5.20, 'unit': 'day'},
    'food_raw_vegan': {'name': 'Raw Vegan Diet Factor', 'category_type': 'food', 'coeff': 1.20, 'unit': 'day'},
    'food_plant_based': {'name': 'Plant-Based Diet Factor', 'category_type': 'food', 'coeff': 1.80, 'unit': 'day'},
    'food_low_fodmap': {'name': 'Low-FODMAP Diet Factor', 'category_type': 'food', 'coeff': 3.50, 'unit': 'day'},
    'food_fruitarian': {'name': 'Fruitarian Diet Factor', 'category_type': 'food', 'coeff': 1.10, 'unit': 'day'},
    'food_halal': {'name': 'Halal Diet Factor', 'category_type': 'food', 'coeff': 5.00, 'unit': 'day'},
    'food_kosher': {'name': 'Kosher Diet Factor', 'category_type': 'food', 'coeff': 5.00, 'unit': 'day'},
    'food_waste': {'name': 'Food Wastage', 'category_type': 'food', 'coeff': 2.50, 'unit': 'kg'},

    # Shopping (unit: items, frequency factor)
    'shopping_clothes': {'name': 'Clothing Purchased', 'category_type': 'shopping', 'coeff': 10.00, 'unit': 'item'},
    'shopping_electronics': {'name': 'Electronics Purchased', 'category_type': 'shopping', 'coeff': 80.00, 'unit': 'item'},
    'shopping_online_delivery': {'name': 'Online Shopping Delivery', 'category_type': 'shopping', 'coeff': 2.00, 'unit': 'delivery'},

    # Waste Management (unit: kg, L, etc.)
    'waste_plastic': {'name': 'Plastic Usage', 'category_type': 'waste', 'coeff': 6.00, 'unit': 'kg'},
    'waste_recycled': {'name': 'Recycled Waste Offset', 'category_type': 'waste', 'coeff': -1.50, 'unit': 'kg'},
    'waste_water': {'name': 'Water Consumption', 'category_type': 'waste', 'coeff': 0.30, 'unit': 'kL (1000L)'},
    'waste_general': {'name': 'General Landfill Waste', 'category_type': 'waste', 'coeff': 1.00, 'unit': 'kg'},
}


def get_coefficient(key):
    """
    Get coefficient from database if available, else return the default.
    """
    try:
        category = EmissionCategory.objects.get(key=key)
        return Decimal(str(category.coefficient))
    except EmissionCategory.DoesNotExist:
        if key in DEFAULT_COEFFICIENTS:
            return Decimal(str(DEFAULT_COEFFICIENTS[key]['coeff']))
        return Decimal('0.0')


def calculate_category_emissions(category, inputs):
    """
    Calculate carbon emissions in kg CO2 for a specific category based on inputs.
    inputs is a dictionary.
    """
    emissions = Decimal('0.0')

    if category == 'transport':
        # distance (km), fuel_type (petrol/diesel/electric), trips_per_week
        # We estimate weekly emissions, or total emissions based on inputs. Let's calculate total emissions for the inputs.
        trips = Decimal(str(inputs.get('trips_per_week', 1)))
        
        # Car
        car_dist = Decimal(str(inputs.get('car_distance', 0)))
        fuel = inputs.get('fuel_type', 'petrol')
        car_coeff = get_coefficient(f'transport_car_{fuel}')
        emissions += car_dist * car_coeff * trips
        
        # Bike
        bike_dist = Decimal(str(inputs.get('bike_distance', 0)))
        emissions += bike_dist * get_coefficient('transport_bike') * trips

        # Bus
        bus_dist = Decimal(str(inputs.get('bus_distance', 0)))
        emissions += bus_dist * get_coefficient('transport_bus') * trips

        # Train
        train_dist = Decimal(str(inputs.get('train_distance', 0)))
        emissions += train_dist * get_coefficient('transport_train') * trips

        # Flight (trips per year, so we normalize to weekly or calculate straight up)
        flight_dist = Decimal(str(inputs.get('flight_distance', 0)))
        emissions += flight_dist * get_coefficient('transport_flight')

    elif category == 'energy':
        # electricity (kWh), lpg (kg), ac_usage (hours), appliance_usage (hours)
        electricity = Decimal(str(inputs.get('electricity_kwh', 0)))
        lpg = Decimal(str(inputs.get('lpg_kg', 0)))
        ac = Decimal(str(inputs.get('ac_hours', 0)))
        appliances = Decimal(str(inputs.get('appliance_hours', 0)))

        emissions += electricity * get_coefficient('energy_electricity')
        emissions += lpg * get_coefficient('energy_lpg')
        emissions += ac * get_coefficient('energy_ac')
        emissions += appliances * get_coefficient('energy_appliances')

    elif category == 'food':
        # diet_type (vegan/vegetarian/eggetarian/non_veg), food_waste_kg
        diet = inputs.get('diet_type', 'vegetarian')
        waste = Decimal(str(inputs.get('food_waste_kg', 0)))
        
        # Diet emissions calculated per week (assuming inputs represent weekly habits)
        diet_coeff = get_coefficient(f'food_{diet}')
        emissions += diet_coeff * Decimal('7')  # 7 days in a week
        emissions += waste * get_coefficient('food_waste')

    elif category == 'shopping':
        # clothes_count, electronics_count, online_orders_count
        clothes = Decimal(str(inputs.get('clothes_count', 0)))
        electronics = Decimal(str(inputs.get('electronics_count', 0)))
        online = Decimal(str(inputs.get('online_orders_count', 0)))

        emissions += clothes * get_coefficient('shopping_clothes')
        emissions += electronics * get_coefficient('shopping_electronics')
        emissions += online * get_coefficient('shopping_online_delivery')

    elif category == 'waste':
        # plastic_kg, recycled_kg, water_kl, general_waste_kg
        plastic = Decimal(str(inputs.get('plastic_kg', 0)))
        recycled = Decimal(str(inputs.get('recycled_kg', 0)))
        water = Decimal(str(inputs.get('water_kl', 0)))
        general = Decimal(str(inputs.get('general_waste_kg', 0)))

        emissions += plastic * get_coefficient('waste_plastic')
        emissions += recycled * get_coefficient('waste_recycled')  # recycled is negative offset
        emissions += water * get_coefficient('waste_water')
        emissions += general * get_coefficient('waste_general')

    # Ensure emissions are non-negative
    if emissions < Decimal('0.0'):
        emissions = Decimal('0.0')

    return emissions.quantize(Decimal('0.01'))

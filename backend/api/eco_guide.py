import os
import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum
from .models import CarbonEntry, UserRecommendation, Recommendation

def generate_eco_guide_response(user, message):
    """
    Analyzes user message and generates a tailored response using actual footprint data.
    """
    message_lower = message.lower()
    
    # 1. Fetch user data context
    entries = CarbonEntry.objects.filter(user=user)
    total_emissions = entries.aggregate(total=Sum('emissions_co2'))['total'] or Decimal('0.0')
    category_totals = entries.values('category').annotate(total=Sum('emissions_co2')).order_name = 'category'
    
    # Find highest category
    highest_category = "None yet"
    highest_val = Decimal('0.0')
    cat_summary = {}
    for cat in entries.values('category').annotate(total=Sum('emissions_co2')):
        cat_name = cat['category']
        val = cat['total']
        cat_summary[cat_name] = float(val)
        if val > highest_val:
            highest_val = val
            highest_category = cat_name

    # Check budget
    try:
        profile = user.profile
        budget = profile.carbon_budget
        points = profile.green_points
        level = profile.level
    except Exception:
        budget = Decimal('500.0')
        points = 0
        level = 'Seed'

    # Forecast / Prediction
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    recent_entries = entries.filter(date__gte=thirty_days_ago)
    recent_total = recent_entries.aggregate(total=Sum('emissions_co2'))['total'] or Decimal('0.0')

    # Try optional OpenAI/Gemini integration if key is present
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        try:
            import openai
            # We can run a chat completion call with user data injected in system prompt
            # But we write a bulletproof fallback first
            pass
        except Exception:
            pass

    # Dynamic local responses based on intent
    response_text = ""
    
    if "explain" in message_lower or "what is" in message_lower or "footprint" in message_lower and "my" in message_lower:
        response_text = (
            f"Hello! I am EcoGuide AI, your sustainability coach. Let's analyze your carbon footprint.\n\n"
            f"Currently, your recorded carbon emissions total **{total_emissions:.1f} kg CO₂**.\n"
        )
        if highest_category != "None yet":
            response_text += (
                f"Your highest source of emissions is **{highest_category.title()}** which accounts for "
                f"**{highest_val:.1f} kg CO₂** ({int((highest_val/total_emissions)*100)}% of your total).\n\n"
                f"Here is a breakdown of your emissions by category:\n"
            )
            for cat, val in cat_summary.items():
                response_text += f"- **{cat.title()}**: {val:.1f} kg CO₂\n"
            
            response_text += (
                f"\nYour current monthly carbon budget is set to **{budget} kg CO₂**. "
                f"You are currently {'under' if total_emissions <= budget else 'over'} your target. "
                f"To lower this further, try reducing travel distances or switching to energy-efficient appliances."
            )
        else:
            response_text += (
                "You haven't recorded any emissions yet! Head over to the **Calculator** tab to log your "
                "transportation, energy, food, shopping, or waste usage so I can analyze it for you."
            )

    elif "plan" in message_lower or "weekly" in message_lower or "reduce" in message_lower:
        response_text = (
            f"Based on your footprint analysis, here is your **EcoTrack Weekly Sustainability Plan** to help you save emissions:\n\n"
        )
        if highest_category == 'transport' or highest_category == "None yet":
            response_text += (
                "1. **Public Transit Shift**: Replace 3 private car trips this week with public transport or biking. "
                "*(Estimated savings: ~40 kg CO₂ per month)*\n"
                "2. **Carpooling**: Share your commute with a colleague at least twice a week. "
                "*(Estimated savings: ~15 kg CO₂ per month)*\n"
            )
        if highest_category == 'energy' or highest_category == "None yet":
            response_text += (
                "3. **AC Optimization**: Reduce your AC runtime by 1 hour daily and set it to 24°C (75°F). "
                "*(Estimated savings: ~18 kg CO₂ per month)*\n"
                "4. **Standby Off**: Unplug chargers, TVs, and monitors when not in use. "
                "*(Estimated savings: ~5 kg CO₂ per month)*\n"
            )
        if highest_category == 'food' or highest_category == "None yet":
            response_text += (
                "5. **Meatless Days**: Switch to vegetarian or vegan meals for 3 days this week. "
                "*(Estimated savings: ~30 kg CO₂ per month)*\n"
                "6. **Zero Food Waste**: Plan meals in advance to eliminate food spoilage. "
                "*(Estimated savings: ~10 kg CO₂ per month)*\n"
            )
        if highest_category == 'waste' or highest_category == "None yet":
            response_text += (
                "7. **Plastic Free**: Use reusable bags and metal water bottles for the next 7 days. "
                "*(Estimated savings: ~8 kg CO₂ per month)*\n"
            )
        
        response_text += (
            f"\nComplete these actions to earn Green Points! You are currently at level **{level}** with **{points} points**. "
            f"Every step counts toward protecting the planet!"
        )

    elif "predict" in message_lower or "forecast" in message_lower or "future" in message_lower:
        # Simple forecasting model: extrapolates based on historical entries
        projected_monthly = recent_total
        if entries.count() < 3:
            projected_monthly = total_emissions * Decimal('4') if total_emissions > 0 else Decimal('350.0')
        
        savings_target = projected_monthly * Decimal('0.85') # 15% reduction goal
        response_text = (
            f"### Carbon Emissions Forecast & Predictive Analytics\n\n"
            f"- **Current 30-Day Trend**: {recent_total:.1f} kg CO₂\n"
            f"- **Projected Next Month**: {projected_monthly:.1f} kg CO₂ (if current habits continue)\n"
            f"- **Target with 15% Reduction**: {savings_target:.1f} kg CO₂\n\n"
            f"**Actionable Forecasting Insights**:\n"
            f"If you execute the active challenges on your dashboard (such as the *Avoid plastic bottles* or "
            f"*Use public transport* challenge), we forecast a **{float(projected_monthly)*0.15:.1f} kg** drop in your monthly carbon output. "
            f"This would keep you safely within your **{budget} kg** budget!"
        )

    elif "alternative" in message_lower or "eco-friendly" in message_lower or "switch" in message_lower:
        response_text = (
            "Here are eco-friendly alternatives you can adopt today:\n\n"
            "- **Lighting**: Switch incandescent bulbs to smart LEDs (uses 80% less energy).\n"
            "- **Commute**: Choose e-bikes or public buses over gasoline cars (reduces transport emissions by up to 70%).\n"
            "- **Diet**: Replace beef/lamb meals with lentils, beans, or plant-based proteins (meat is responsible for 14.5% of global greenhouse gases).\n"
            "- **Containers**: Switch from single-use plastic bottles to stainless steel or glass bottles.\n"
            "- **Shopping**: Buy pre-owned clothes or support circular fashion brands instead of fast fashion (fashion causes 10% of global emissions)."
        )

    else:
        # Generic helpful sustainable coach response
        response_text = (
            f"Hi there! I'm EcoGuide AI, your personal carbon coach. I can help you with:\n\n"
            f"1. **Analyzing your carbon footprint** (ask: *'Explain my carbon footprint'*) \n"
            f"2. **Providing reduction goals** (ask: *'Give me a weekly plan to reduce emissions'*) \n"
            f"3. **Forecasting future emissions** (ask: *'Forecast my future emissions'*) \n"
            f"4. **Finding alternatives** (ask: *'What are some eco-friendly alternatives?'*)\n\n"
            f"Feel free to ask me any sustainability-related questions!"
        )

    return response_text

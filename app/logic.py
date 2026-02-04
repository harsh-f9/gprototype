from app.models import InitialFilterForm

def classify_user(data: InitialFilterForm) -> str:
    """
    Classifies the user based on the 7 initial filter questions.
    Returns: 'green', 'sll', or 'other'
    """
    score_green = 0
    score_sll = 0

    if data.is_manufacturing:
        score_green += 1
    if data.consumes_significant_energy:
        score_green += 1
        score_sll += 0.5 
    if data.tracks_env_metrics:
        score_green += 2 
    if data.measures_emissions:
        score_green += 2 
    
    if data.has_sustainability_goals:
        score_sll += 2
    if data.applied_for_esg_loan:
        score_sll += 1
    if data.has_employee_policies:
        score_sll += 1

    if score_green >= 3:
        return "green"
    elif score_sll >= 2:
        return "sll"
    else:
        return "other"

def calculate_carbon_proxy(data: dict) -> dict:
    """
    Calculate estimated carbon footprint based on proxy indicators.
    Emission factors (approximate for India):
    - Electricity: 0.82 kgCO2/kWh (India Grid Average)
    - Diesel/Fuel: 2.68 kgCO2/Litre
    - Water: 0.376 kgCO2/1000L (pumping & treatment)
    """
    
    # Extract values, default to 0 if missing
    elec = float(data.get("annual_electricity_kwh", 0) or 0)
    fuel = float(data.get("annual_fuel_litres", 0) or 0)
    water = float(data.get("water_consumption_litres", 0) or 0)
    
    # Emission Factors
    FACTOR_ELEC = 0.82  # kgCO2/kWh
    FACTOR_FUEL = 2.68  # kgCO2/L (diesel proxy)
    FACTOR_WATER = 0.000376  # kgCO2/L
    
    # Calculate emissions
    carbon_elec = elec * FACTOR_ELEC
    carbon_fuel = fuel * FACTOR_FUEL
    carbon_water = water * FACTOR_WATER
    
    total_carbon = carbon_elec + carbon_fuel + carbon_water
    
    return {
        "estimated_carbon": round(total_carbon, 2),
        "breakdown": {
            "electricity": round(carbon_elec, 2),
            "fuel": round(carbon_fuel, 2),
            "water": round(carbon_water, 2)
        },
        "unit": "kgCO2e/year"
    }


def generate_scorecard(category: str, data: dict) -> dict:
    """
    Generate a detailed ESG score (0-100) with breakdown and suggestions.
    """
    score = 0
    breakdown = {}
    suggestions = []
    
    if category == "green":
        # ===== GREEN LOAN SCORING (Environmental Focus) =====
        
        # 1. Renewable Energy % (25 points max)
        renewable_pct = float(data.get("renewable_energy_pct", 0) or 0)
        if renewable_pct > 50:
            renewable_score = 25
        elif renewable_pct >= 25:
            renewable_score = 18
        elif renewable_pct >= 10:
            renewable_score = 10
        elif renewable_pct > 0:
            renewable_score = 5
        else:
            renewable_score = 0
            suggestions.append({"text": "Install rooftop solar to start your renewable energy journey.", "icon": "☀️"})
        breakdown["Renewable Energy"] = renewable_score
        score += renewable_score
        
        # 2. Energy Intensity (15 points max) - Lower is better
        elec = float(data.get("annual_electricity_kwh", 0) or 0)
        if elec < 10000:
            energy_score = 15
        elif elec < 50000:
            energy_score = 10
        elif elec < 100000:
            energy_score = 5
        else:
            energy_score = 0
            suggestions.append({"text": "Consider an energy audit to identify reduction opportunities.", "icon": "⚡"})
        breakdown["Energy Efficiency"] = energy_score
        score += energy_score
        
        # 3. Fuel Dependency (15 points max) - Lower is better
        fuel = float(data.get("annual_fuel_litres", 0) or 0)
        if fuel < 1000:
            fuel_score = 15
        elif fuel < 5000:
            fuel_score = 10
        elif fuel < 10000:
            fuel_score = 5
        else:
            fuel_score = 0
            suggestions.append({"text": "Explore EV fleet transition or fuel-efficient logistics.", "icon": "🚗"})
        breakdown["Fuel Efficiency"] = fuel_score
        score += fuel_score
        
        # 4. Water Efficiency (10 points max) - Lower is better
        water = float(data.get("water_consumption_litres", 0) or 0)
        if water < 50000:
            water_score = 10
        elif water < 100000:
            water_score = 7
        elif water < 500000:
            water_score = 3
        else:
            water_score = 0
            suggestions.append({"text": "Implement rainwater harvesting and water recycling.", "icon": "💧"})
        breakdown["Water Management"] = water_score
        score += water_score
        
        # 5. Waste Management (15 points max) - Lower is better
        waste = float(data.get("waste_generated_kg_month", 0) or 0)
        if waste < 100:
            waste_score = 15
        elif waste < 500:
            waste_score = 10
        elif waste < 1000:
            waste_score = 5
        else:
            waste_score = 0
            suggestions.append({"text": "Implement waste segregation and partner with recyclers.", "icon": "♻️"})
        breakdown["Waste Reduction"] = waste_score
        score += waste_score
        
        # 6. Green Technology (15 points max)
        efficiency_equip = data.get("efficiency_equipment", "")
        if efficiency_equip and len(str(efficiency_equip)) > 5:
            tech_score = 15
        else:
            tech_score = 0
            suggestions.append({"text": "Invest in BEE-rated equipment and LED lighting.", "icon": "💡"})
        breakdown["Green Technology"] = tech_score
        score += tech_score
        
        # 7. Industry Sector Bonus (5 points max)
        industry = data.get("industry_code", "")
        green_sectors = ["35", "38", "39"]  # Electricity, Waste, Remediation
        if industry and any(industry.startswith(s) for s in green_sectors):
            sector_score = 5
        else:
            sector_score = 0
        breakdown["Sector Bonus"] = sector_score
        score += sector_score
        
    elif category == "sll":
        # ===== SLL SCORING (Social & Governance Focus) =====
        
        # 1. Target Clarity (20 points max)
        goals = str(data.get("target_improvement_goals", ""))
        import re
        has_numbers = bool(re.search(r'\d+%|\d+ percent', goals.lower()))
        if has_numbers and len(goals) > 30:
            goal_score = 20
        elif len(goals) > 20:
            goal_score = 10
        else:
            goal_score = 0
            suggestions.append({"text": "Define quantifiable targets (e.g., 'Reduce energy by 15% in 3 years').", "icon": "🎯"})
        breakdown["Goal Clarity"] = goal_score
        score += goal_score
        
        # 2. Safety Record (25 points max)
        incidents = int(data.get("safety_incident_count", 0) or 0)
        if incidents == 0:
            safety_score = 25
        elif incidents <= 2:
            safety_score = 15
        elif incidents <= 5:
            safety_score = 5
        else:
            safety_score = 0
            suggestions.append({"text": "Strengthen ISO 45001 safety protocols to reach zero incidents.", "icon": "⛑️"})
        breakdown["Safety Record"] = safety_score
        score += safety_score
        
        # 3. Workforce Diversity (15 points max)
        diversity = data.get("workforce_diversity_stats", "")
        if diversity and len(str(diversity)) > 5:
            diversity_score = 15
        else:
            diversity_score = 0
            suggestions.append({"text": "Track and report workforce diversity metrics.", "icon": "👥"})
        breakdown["Diversity Tracking"] = diversity_score
        score += diversity_score
        
        # 4. Governance Policies (20 points max)
        governance = str(data.get("governance_policies", "")).lower()
        gov_keywords = ["anti-corruption", "whistleblower", "ethics", "compliance", "audit"]
        matches = sum(1 for kw in gov_keywords if kw in governance)
        if matches >= 2:
            gov_score = 20
        elif matches == 1 or len(governance) > 20:
            gov_score = 10
        else:
            gov_score = 0
            suggestions.append({"text": "Formalize Anti-Corruption and Whistleblower policies.", "icon": "📜"})
        breakdown["Governance"] = gov_score
        score += gov_score
        
        # 5. Training Programs (10 points max)
        training = data.get("training_programs", "")
        if training and len(str(training)) > 5:
            training_score = 10
        else:
            training_score = 0
            suggestions.append({"text": "Implement regular skill development and safety training.", "icon": "📚"})
        breakdown["Employee Training"] = training_score
        score += training_score
        
        # 6. Scale Factor (10 points max)
        employees = int(data.get("num_employees", 0) or 0)
        if employees > 50:
            scale_score = 10
        elif employees >= 20:
            scale_score = 7
        else:
            scale_score = 5
        breakdown["Organization Scale"] = scale_score
        score += scale_score
        
    else:
        # ===== OTHER/ESG READINESS SCORING =====
        
        # 1. Business Description (20 points max)
        biz_info = str(data.get("business_info", ""))
        if len(biz_info) > 100:
            biz_score = 20
        elif len(biz_info) > 30:
            biz_score = 10
        else:
            biz_score = 5
        breakdown["Business Clarity"] = biz_score
        score += biz_score
        
        # 2. Existing Documentation (40 points max)
        docs = str(data.get("existing_docs", "")).lower()
        cert_keywords = ["iso", "bis", "fssai", "gmp", "haccp", "ohsas", "sa8000"]
        doc_matches = sum(1 for kw in cert_keywords if kw in docs)
        if doc_matches >= 2:
            doc_score = 40
        elif doc_matches == 1 or len(docs) > 30:
            doc_score = 20
        else:
            doc_score = 0
            suggestions.append({"text": "Start documenting your processes - it's the foundation of ESG.", "icon": "📋"})
        breakdown["Documentation"] = doc_score
        score += doc_score
        
        # 3. Interest Areas (40 points max)
        interests = str(data.get("interest_areas", "")).lower()
        interest_keywords = ["water", "energy", "waste", "solar", "recycle", "carbon", "green"]
        interest_matches = sum(1 for kw in interest_keywords if kw in interests)
        if interest_matches >= 3:
            interest_score = 40
        elif interest_matches >= 1:
            interest_score = 20
        else:
            interest_score = 10
            suggestions.append({"text": "Explore quick wins: LED lighting, waste segregation, water metering.", "icon": "🌱"})
        breakdown["Sustainability Interest"] = interest_score
        score += interest_score
        
        # Default suggestions for "other" category
        if not suggestions:
            suggestions.append({"text": "Start tracking monthly electricity and fuel bills.", "icon": "📊"})
            suggestions.append({"text": "Check if your industry is eligible for MSME green schemes.", "icon": "🏭"})
    
    # Cap score at 100
    score = min(score, 100)
    
    # Determine rating
    if score >= 80:
        rating = "A"
    elif score >= 60:
        rating = "B"
    elif score >= 40:
        rating = "C"
    else:
        rating = "D"
    
    return {
        "score": int(score),
        "rating": rating,
        "breakdown": breakdown,
        "suggestions": suggestions
    }


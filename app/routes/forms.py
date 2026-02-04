from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models import ContactForm, InitialFilterForm, GreenLoanIntake, SLLIntake, OtherIntake
from app.logic import classify_user, calculate_carbon_proxy, generate_scorecard

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/contact", response_class=HTMLResponse)
async def get_contact(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/contact", response_class=HTMLResponse)
async def post_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...)
):
    try:
        form_data = ContactForm(name=name, email=email)
        # Process logic here (e.g., send email)
        return RedirectResponse(url="/onboarding", status_code=303)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        return templates.TemplateResponse("index.html", {"request": request, "error_msg": error_msg})

# --- Onboarding & Intake Routes ---

@router.get("/onboarding", response_class=HTMLResponse)
async def get_onboarding(request: Request):
    return templates.TemplateResponse("onboarding.html", {"request": request})

@router.post("/onboarding", response_class=HTMLResponse)
async def post_onboarding(
    request: Request,
    is_manufacturing: bool = Form(False),
    consumes_significant_energy: bool = Form(False),
    tracks_env_metrics: bool = Form(False),
    measures_emissions: bool = Form(False),
    has_sustainability_goals: bool = Form(False),
    applied_for_esg_loan: bool = Form(False),
    has_employee_policies: bool = Form(False)
):
    try:
        # Create model instance
        form_data = InitialFilterForm(
            is_manufacturing=is_manufacturing,
            consumes_significant_energy=consumes_significant_energy,
            tracks_env_metrics=tracks_env_metrics,
            measures_emissions=measures_emissions,
            has_sustainability_goals=has_sustainability_goals,
            applied_for_esg_loan=applied_for_esg_loan,
            has_employee_policies=has_employee_policies
        )
        
        # Classify
        category = classify_user(form_data)
        
        # Save to session
        request.session["user_category"] = category
        request.session["initial_data"] = form_data.model_dump()
        
        # Check if user is logged in
        user_id = request.session.get("user_id")
        
        if user_id:
            # User is logged in, go to intake
            return RedirectResponse(url=f"/intake/{category}", status_code=303)
        else:
            # User needs to register/login
            return RedirectResponse(url="/register", status_code=303)
        
    except Exception as e:
        return templates.TemplateResponse("onboarding.html", {"request": request, "error_msg": str(e)})


@router.get("/intake/{category}", response_class=HTMLResponse)
async def get_intake(request: Request, category: str):
    # Auth check
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=303)

    # Validate category
    if category not in ["green", "sll", "other"]:
        return RedirectResponse(url="/onboarding")
        
    template_map = {
        "green": "intake_green.html",
        "sll": "intake_sll.html",
        "other": "intake_other.html"
    }
    
    return templates.TemplateResponse(template_map[category], {"request": request})

@router.post("/intake/submit", response_class=HTMLResponse)
async def post_intake_submit(request: Request):
    # Auth check
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=303)

    # Retrieve category from session or form
    form_data_raw = await request.form()
    category = form_data_raw.get("category", "other")
    
    # Save category to session just in case
    request.session["user_category"] = category
    
    # Parse data based on category
    data_dict = {}
    try:
        if category == "green":
            validated_data = GreenLoanIntake(**form_data_raw)
            data_dict = validated_data.model_dump()
            
        elif category == "sll":
            validated_data = SLLIntake(**form_data_raw)
            data_dict = validated_data.model_dump()
            
        else:
            validated_data = OtherIntake(**form_data_raw)
            data_dict = validated_data.model_dump()
            
    except Exception as e:
        # On error, send back to the intake form
        return templates.TemplateResponse(f"intake_{category}.html", {"request": request, "error_msg": f"Invalid data: {str(e)}"})

    # Run Scoring Logic
    carbon_result = calculate_carbon_proxy(data_dict)
    scorecard = generate_scorecard(category, data_dict)
    
    # Generate AI Verdict (server-side, synchronous)
    from app.ai_verdict import generate_verdict_sync
    ai_verdict = await generate_verdict_sync(
        category=category,
        score=scorecard.get("score", 0),
        rating=scorecard.get("rating", "N/A"),
        carbon_estimate=carbon_result.get("estimated_carbon", 0),
        user_data=data_dict,
        suggestions=scorecard.get("suggestions", [])
    )
    
    # Render Dashboard with AI verdict included
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "category": category,
        "scorecard": scorecard,
        "carbon_result": carbon_result,
        "intake_data": data_dict,
        "ai_verdict": ai_verdict
    })




@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    # This endpoint is for direct navigation/refresh where we might not have fresh POST data
    category = request.session.get("user_category", "unknown")
    # For now, return empty scorecard/results or retrieve from session if we persisted it
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "category": category,
        "scorecard": None,
        "carbon_result": None
    })

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.ai_verdict import generate_verdict_stream
import json

router = APIRouter()

@router.get("/api/generate-verdict")
async def stream_ai_verdict(request: Request):
    """
    Streaming endpoint for AI verdict generation.
    Returns Server-Sent Events (SSE) for real-time text streaming.
    """
    # Get assessment results from session
    results = request.session.get("assessment_results")
    
    if not results:
        async def error_stream():
            yield f"data: {json.dumps({'error': 'No assessment data found'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    # Extract data
    category = results.get("category")
    scorecard = results.get("scorecard")
    carbon_result = results.get("carbon_result")
    intake_data = results.get("intake_data")
    
    # Stream the AI verdict
    return StreamingResponse(
        generate_verdict_stream(
            category=category,
            score=scorecard["score"],
            rating=scorecard["rating"],
            carbon_estimate=carbon_result["estimated_carbon"],
            user_data=intake_data,
            suggestions=scorecard["suggestions"]
        ),
        media_type="text/event-stream"
    )

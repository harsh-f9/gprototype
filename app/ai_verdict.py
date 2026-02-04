"""
GreenBridge AI Verdict Generator
Uses Google Gemini API to generate personalized ESG assessment verdicts.
"""
from typing import Optional, AsyncGenerator
import httpx
import json
from app.config import settings

# Gemini API Configuration
GEMINI_API_KEY = settings.GEMINI_API_KEY
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
GEMINI_STREAM_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent"

# System prompts for each category
SYSTEM_PROMPTS = {
    "green": """You are an ESG expert for GreenBridge, helping Indian SMEs with Green Loans.
Based on the user's environmental assessment data, provide a structured, detailed verdict.

Your response MUST follow this structure:
1. **Assessment Summary**: A clear statement on their Green Loan eligibility based on the score.
2. **Key Strengths**: Identify 2 specific areas where they are performing well.
3. **improvement Areas**: Identify 2 specific gaps that need attention.
4. **Actionable Roadmap**: Provide 3 concrete steps to improve their score.
5. **Funding Opportunities**: Mention 1-2 relevant Indian schemes (e.g., SIDBI, IREDA).

Keep the tone professional and encouraging. Total length should be around 200 words.
DO NOT STOP MID-SENTENCE. COMPLETE YOUR ANALYSIS.""",

    "sll": """You are an ESG expert for GreenBridge, helping Indian SMEs with Sustainability-Linked Loans (SLL).
Based on the user's social and governance data, provide a structured, detailed verdict.

Your response MUST follow this structure:
1. **Assessment Summary**: Evaluate their trajectory for SLL eligibility.
2. **Social & Governance Highlights**: Comment on their safety/diversity/policy data.
3. **Gaps & Risks**: Identify missing policies or high-risk areas.
4. **KPI Recommendations**: Suggest 2-3 specific KPIs for loan linkage.
5. **Next Steps**: Recommend certifications (ISO/SA8000) or policy drafts.

Keep the tone professional and expert. Total length should be around 200 words.
DO NOT STOP MID-SENTENCE. COMPLETE YOUR ANALYSIS.""",

    "other": """You are an ESG expert for GreenBridge, guiding Indian SMEs on ESG Readiness.
Based on their initial input, provide a structured, encouraging verdict.

Your response MUST follow this structure:
1. **Welcome & Context**: Welcome them to the sustainability journey.
2. **Quick Wins**: Identify 2 low-hanging fruits based on their sector/interest.
3. **Business Case**: Briefly explain why ESG matters for them (funding/market access).
4. **Relevant Schemes**: Suggest 1 government scheme or certification to explore.
5. **Next Steps**: Encourage them to take the full Green Loan or SLL assessment.

Keep the tone motivating and simple. Total length should be around 150 words.
DO NOT STOP MID-SENTENCE. COMPLETE YOUR ANALYSIS."""
}


async def generate_verdict_sync(
    category: str,
    score: int,
    rating: str,
    carbon_estimate: float,
    user_data: dict,
    suggestions: list
) -> str:
    """
    Generate AI verdict synchronously and return the complete text.
    This is used for server-side rendering.
    """
    if not GEMINI_API_KEY:
        return "⚠️ AI verdict unavailable. Please configure GEMINI_API_KEY."
    
    # Build user context
    system_prompt = SYSTEM_PROMPTS.get(category, SYSTEM_PROMPTS["other"])
    
    # Format user data for the prompt
    data_summary = "\n".join([f"- {k}: {v}" for k, v in user_data.items() if v])
    suggestions_text = "\n".join([f"- {s.get('text', s)}" for s in suggestions]) if suggestions else "None"
    
    user_message = f"""
USER ASSESSMENT RESULTS:
Category: {category.upper()}
Score: {score}/100
Rating: {rating}
Estimated Carbon Footprint: {carbon_estimate:,.0f} kgCO2e/year

USER'S SUBMITTED DATA:
{data_summary}

SYSTEM-GENERATED SUGGESTIONS:
{suggestions_text}

Based on the above, provide your expert verdict and personalized recommendations.
"""

    # Prepare API request (non-streaming)
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": system_prompt + "\n\n" + user_message}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000,
            "topP": 0.9
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                print(f"Gemini API error: {response.status_code} - {response.text}")
                return f"⚠️ AI service temporarily unavailable (Error {response.status_code})"
            
            response_data = response.json()
            
            # Extract text from response
            candidates = response_data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "Unable to generate verdict.")
            
            return "Unable to generate verdict."
            
    except httpx.TimeoutException:
        return "⚠️ AI service timed out. Please try again."
    except Exception as e:
        print(f"Error generating verdict: {e}")
        return "⚠️ An error occurred while generating the verdict."

async def generate_verdict_stream(
    category: str,
    score: int,
    rating: str,
    carbon_estimate: float,
    user_data: dict,
    suggestions: list
) -> AsyncGenerator[str, None]:
    """
    Stream AI-powered verdict using Google Gemini API with Server-Sent Events.
    Yields chunks of text as they're generated.
    """
    if not GEMINI_API_KEY:
        yield f"data: {json.dumps({'text': '⚠️ AI verdict unavailable. Please configure GEMINI_API_KEY.'})}\n\n"
        yield "data: [DONE]\n\n"
        return
    
    # Build user context
    system_prompt = SYSTEM_PROMPTS.get(category, SYSTEM_PROMPTS["other"])
    
    # Format user data for the prompt
    data_summary = "\n".join([f"- {k}: {v}" for k, v in user_data.items() if v])
    suggestions_text = "\n".join([f"- {s.get('text', s)}" for s in suggestions]) if suggestions else "None"
    
    user_message = f"""
USER ASSESSMENT RESULTS:
Category: {category.upper()}
Score: {score}/100
Rating: {rating}
Estimated Carbon Footprint: {carbon_estimate:,.0f} kgCO2e/year

USER'S SUBMITTED DATA:
{data_summary}

SYSTEM-GENERATED SUGGESTIONS:
{suggestions_text}

Based on the above, provide your expert verdict and personalized recommendations.
"""

    # Prepare API request
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": system_prompt + "\n\n" + user_message}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500,
            "topP": 0.9
        }
    }
    
    try:
        print(f"Starting Gemini stream request to: {GEMINI_STREAM_URL}")
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{GEMINI_STREAM_URL}?key={GEMINI_API_KEY}",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                print(f"Gemini response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    print(f"Gemini API error: {response.status_code} - {error_text.decode()}")
                    yield f"data: {json.dumps({'error': f'API Error {response.status_code}'})}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                
                # Collect the full response
                full_response = b""
                async for chunk in response.aiter_bytes():
                    full_response += chunk
                
                # Parse the complete JSON response
                try:
                    response_data = json.loads(full_response.decode('utf-8'))
                    print(f"Full response parsed: {response_data}")
                    
                    # Gemini returns an array of response objects
                    if isinstance(response_data, list):
                        for item in response_data:
                            candidates = item.get("candidates", [])
                            if candidates:
                                content = candidates[0].get("content", {})
                                parts = content.get("parts", [])
                                if parts:
                                    text_chunk = parts[0].get("text", "")
                                    print(f"Extracted text: {text_chunk}")
                                    if text_chunk:
                                        # Send text word-by-word for typing effect
                                        words = text_chunk.split(' ')
                                        for i, word in enumerate(words):
                                            chunk_text = word if i == 0 else ' ' + word
                                            yield f"data: {json.dumps({'text': chunk_text})}\n\n"
                    else:
                        # Single object response
                        candidates = response_data.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                text_chunk = parts[0].get("text", "")
                                print(f"Extracted text: {text_chunk}")
                                if text_chunk:
                                    words = text_chunk.split(' ')
                                    for i, word in enumerate(words):
                                        chunk_text = word if i == 0 else ' ' + word
                                        yield f"data: {json.dumps({'text': chunk_text})}\n\n"
                
                except json.JSONDecodeError as e:
                    print(f"Failed to parse full response: {e}")
                    print(f"Response text: {full_response.decode('utf-8')}")
                    yield f"data: {json.dumps({'error': 'Failed to parse API response'})}\n\n"
                
                print("Stream complete")
                yield "data: [DONE]\n\n"
                
    except httpx.TimeoutException:
        yield f"data: {json.dumps({'error': 'Request timed out'})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        print(f"Gemini streaming error: {e}")
        yield f"data: {json.dumps({'error': 'Generation failed'})}\n\n"
        yield "data: [DONE]\n\n"


async def generate_verdict(
    category: str,
    score: int,
    rating: str,
    carbon_estimate: float,
    user_data: dict,
    suggestions: list
) -> Optional[str]:
    """
    Generate an AI-powered verdict using Google Gemini API (non-streaming).
    """
    if not GEMINI_API_KEY:
        return "⚠️ AI verdict unavailable. Please configure GEMINI_API_KEY in your environment."
    
    # Build user context
    system_prompt = SYSTEM_PROMPTS.get(category, SYSTEM_PROMPTS["other"])
    
    # Format user data for the prompt
    data_summary = "\n".join([f"- {k}: {v}" for k, v in user_data.items() if v])
    suggestions_text = "\n".join([f"- {s.get('text', s)}" for s in suggestions]) if suggestions else "None"
    
    user_message = f"""
USER ASSESSMENT RESULTS:
Category: {category.upper()}
Score: {score}/100
Rating: {rating}
Estimated Carbon Footprint: {carbon_estimate:,.0f} kgCO2e/year

USER'S SUBMITTED DATA:
{data_summary}

SYSTEM-GENERATED SUGGESTIONS:
{suggestions_text}

Based on the above, provide your expert verdict and personalized recommendations.
"""

    # Prepare API request
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": system_prompt + "\n\n" + user_message}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500,
            "topP": 0.9
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                # Extract text from Gemini response
                candidates = result.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                return "Unable to parse AI response."
            else:
                error_msg = response.text
                print(f"Gemini API error: {response.status_code} - {error_msg}")
                return f"AI service temporarily unavailable. (Error: {response.status_code})"
                
    except httpx.TimeoutException:
        return "AI verdict timed out. Please try again."
    except Exception as e:
        print(f"Gemini API exception: {e}")
        return "AI verdict generation failed. Please check your API configuration."

from fastapi import APIRouter

from app.schemas.game import AnalyzeRequest, HealthResponse

router = APIRouter(prefix="/api", tags=["analysis"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()


@router.post("/analyze")
async def analyze_game(request: AnalyzeRequest):
    """Analyze a Steam game and generate marketing report.

    TODO: Implement full pipeline:
    1. Parse Steam URL/app ID
    2. Fetch game data via Steam API
    3. Run AI analysis with Claude
    4. Store results in DB
    5. Return analysis report
    """
    return {"status": "not_implemented", "message": "Analysis pipeline coming soon", "url": request.url}

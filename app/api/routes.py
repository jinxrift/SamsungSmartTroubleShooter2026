from fastapi import APIRouter
from pydantic import BaseModel

from app.models.schema import ContextDeeplinkResponse
from app.services.siis_engine import process_siis
from app.services.deeplink_matcher import match_deeplinks
from app.services.cache import get, set


router = APIRouter()


class SIISResponse(BaseModel):
    title: str
    content: str


class TroubleshootRequest(BaseModel):
    query: str
    siis_response: SIISResponse


@router.post(
    "/v1/troubleshoot",
    response_model=ContextDeeplinkResponse
)
def troubleshoot(request: TroubleshootRequest):

    # 1. Create cache key
    cache_key = request.query

    # 2. Check cache
    cached_result = get(cache_key)

    if cached_result is not None:
        return cached_result

    # 3. Process SIIS response
    troubleshooting = process_siis(
        request.query,
        request.siis_response
    )

    # 4. Match Samsung deeplinks
    result = match_deeplinks(troubleshooting)

    # 5. Cache result
    response = {
        "contexts": result.get("goals", [])
    }

    set(cache_key, response)

    # 6. Return final response
    return response
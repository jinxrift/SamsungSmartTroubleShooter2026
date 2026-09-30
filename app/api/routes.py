import hashlib
import json

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
    siis_payload = {
        "title": request.siis_response.title,
        "content": request.siis_response.content,
    }
    payload_digest = hashlib.sha256(
        json.dumps(siis_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    cache_key = f"{request.query} {payload_digest}"
    cached_result = get(cache_key)
    if cached_result is not None:
        return cached_result

    troubleshooting = process_siis(
        request.query,
        request.siis_response
    )
    result = match_deeplinks(troubleshooting)
    response = ContextDeeplinkResponse(contexts=result.get("goals", []))
    response_data = response.model_dump()
    set(cache_key, response_data)
    return response
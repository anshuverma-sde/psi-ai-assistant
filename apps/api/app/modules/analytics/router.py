from fastapi import APIRouter

from app.core.deps import CurrentAuth, DbSession
from app.core.responses import ApiResponse, ok
from app.modules.analytics.schemas import UsageOut
from app.modules.analytics.service import AnalyticsService

router = APIRouter(prefix="/api/admin/usage", tags=["analytics (admin)"])


@router.get("", response_model=ApiResponse[UsageOut])
async def usage(auth: CurrentAuth, db: DbSession):
    return ok(await AnalyticsService(db).usage(auth.org_id))

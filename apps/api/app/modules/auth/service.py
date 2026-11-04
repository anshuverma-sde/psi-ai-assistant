import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.core.security.passwords import hash_password, verify_password
from app.modules.assistant.token.service import AssistantTokenService
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginIn, RegisterIn, SessionOut, UserOut
from app.modules.organization.repository import OrganizationRepository
from app.modules.organization.schemas import OrganizationOut

# Constant-time-ish login: verify against a dummy hash when the user doesn't exist.
_DUMMY_HASH = hash_password("timing-equalizer")


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.orgs = OrganizationRepository(db)

    async def register(self, data: RegisterIn) -> tuple[User, SessionOut]:
        email = data.email.lower()
        if await self.db.scalar(select(User.id).where(func.lower(User.email) == email)):
            raise AppError(ErrorCode.EMAIL_TAKEN, field="email")

        org = await self.orgs.create(data.organization_name)
        user = User(org_id=org.id, email=email, password_hash=hash_password(data.password))
        self.db.add(user)
        await AssistantTokenService(self.db).create_for_org(org.id)
        await self.db.commit()
        return user, await self.session_for(user.id, org.id)

    async def login(self, data: LoginIn) -> tuple[User, SessionOut]:
        user = await self.db.scalar(select(User).where(func.lower(User.email) == data.email.lower()))
        if not verify_password(data.password, user.password_hash if user else _DUMMY_HASH) or not user:
            raise AppError(ErrorCode.INVALID_CREDENTIALS)
        return user, await self.session_for(user.id, user.org_id)

    async def session_for(self, user_id: uuid.UUID, org_id: uuid.UUID) -> SessionOut:
        user = await self.db.get(User, user_id)
        org = await self.orgs.get(org_id)
        if user is None or org is None:
            raise AppError(ErrorCode.UNAUTHORIZED)
        return SessionOut(user=UserOut(id=user.id, email=user.email),
                          organization=OrganizationOut.model_validate(org))

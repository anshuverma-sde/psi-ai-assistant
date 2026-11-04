from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, CreatedAt, UUIDPrimaryKey


class Organization(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(120), nullable=False)

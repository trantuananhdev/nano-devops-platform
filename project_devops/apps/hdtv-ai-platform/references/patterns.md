# Code Patterns — HDTV AI Platform

Tài liệu này chứa code mẫu đầy đủ cho từng layer. Đọc phần tương ứng trước khi viết code.

---

## 1. Model (entities.py)

```python
# app/models/entities.py — THÊM vào cuối file
class ProcurementItem(Base):
    """Hạng mục mua sắm trong hồ sơ."""
    __tablename__ = "procurement_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dossier_id: Mapped[int] = mapped_column(ForeignKey("dossiers.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float | None] = mapped_column(nullable=True)   # VND
    spec: Mapped[dict] = mapped_column(JSONB, default=dict)           # technical specs
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dossier: Mapped["Dossier"] = relationship(back_populates="items")

# Thêm vào Dossier class:
# items: Mapped[list["ProcurementItem"]] = relationship(back_populates="dossier")
```

**Rules:**
- Tất cả model trong `entities.py` — không tạo file model riêng
- Enum dùng `(str, enum.Enum)` để JSON-serializable
- JSONB mutable default: `default=dict` hoặc `default=list` (callable, not `{}` or `[]`)
- `Mapped[T | None]` cho nullable columns

---

## 2. Migration (Alembic)

```python
# alembic/versions/019_add_procurement_items.py
"""Add procurement items table

Revision ID: 019
Revises: 018
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'procurement_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dossier_id', sa.Integer(), sa.ForeignKey('dossiers.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('spec', JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_procurement_items_dossier_id', 'procurement_items', ['dossier_id'])


def downgrade() -> None:
    op.drop_index('ix_procurement_items_dossier_id', 'procurement_items')
    op.drop_table('procurement_items')
```

**Rules:**
- `revision` phải là chuỗi liên tiếp
- Migration hiện tại cuối là `018` → tiếp theo là `019`
- Enum mới: dùng `sa.Enum(..., name='enumname', create_type=True)` trong upgrade; `op.execute("DROP TYPE enumname")` trong downgrade
- KHÔNG dùng `Base.metadata.create_all()`

---

## 3. Schema (Pydantic v2)

```python
# app/schemas/procurement_item.py
from pydantic import BaseModel, ConfigDict
from typing import Any


class ProcurementItemCreate(BaseModel):
    name: str
    quantity: int = 1
    unit_price: float | None = None
    spec: dict[str, Any] = {}


class ProcurementItemUpdate(BaseModel):
    name: str | None = None
    quantity: int | None = None
    unit_price: float | None = None
    spec: dict[str, Any] | None = None


class ProcurementItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dossier_id: int
    name: str
    quantity: int
    unit_price: float | None
    spec: dict[str, Any]
```

**Rules:**
- `ConfigDict(from_attributes=True)` thay vì `orm_mode = True`
- `model_validate(orm_obj)` thay vì `from_orm(orm_obj)`

---

## 4. Service

```python
# app/services/procurement_item_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import ProcurementItem
from app.schemas.procurement_item import ProcurementItemCreate, ProcurementItemOut


async def list_items(session: AsyncSession, dossier_id: int) -> list[ProcurementItemOut]:
    result = await session.execute(
        select(ProcurementItem).where(ProcurementItem.dossier_id == dossier_id)
    )
    return [ProcurementItemOut.model_validate(r) for r in result.scalars().all()]


async def create_item(
    session: AsyncSession, dossier_id: int, data: ProcurementItemCreate
) -> ProcurementItemOut:
    item = ProcurementItem(dossier_id=dossier_id, **data.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)   # ← luôn refresh sau commit
    return ProcurementItemOut.model_validate(item)


async def delete_item(session: AsyncSession, item_id: int) -> None:
    result = await session.execute(select(ProcurementItem).where(ProcurementItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return
    await session.delete(item)
    await session.commit()
```

**Rules:**
- Luôn dùng `select()` + `await session.execute()` — không dùng `session.query()`
- `await session.refresh(obj)` sau mỗi commit trước khi return
- Relationship: dùng `selectinload()` để tránh `MissingGreenlet`
- Service thuần, không gọi `publish_event()` — để router gọi

---

## 5. Router

```python
# app/routers/procurement_items.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.procurement_item import ProcurementItemCreate, ProcurementItemOut
from app.services import procurement_item_service
from app.services.pubsub import publish_event

router = APIRouter()


@router.get("", response_model=list[ProcurementItemOut])
async def list_items(dossier_id: int, session: AsyncSession = Depends(get_db)):
    return await procurement_item_service.list_items(session, dossier_id)


@router.post("", response_model=ProcurementItemOut, status_code=201)
async def create_item(
    dossier_id: int,
    body: ProcurementItemCreate,
    session: AsyncSession = Depends(get_db),
):
    item = await procurement_item_service.create_item(session, dossier_id, body)
    await publish_event("procurement_item_added", {"dossier_id": dossier_id, "item_id": item.id})
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, session: AsyncSession = Depends(get_db)):
    await procurement_item_service.delete_item(session, item_id)
```

**Đăng ký trong `app/routers/__init__.py`:**
```python
from app.routers import procurement_items
api_router.include_router(procurement_items.router, prefix="/dossiers/{dossier_id}/items", tags=["procurement-items"])
```

---

## 6. Seed

```python
# seeds/seed_procurement_items.py
import asyncio
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.entities import ProcurementItem


ITEMS_DATA = [
    {"dossier_doc_no": "EVNHANOI-UAV-198-2024", "name": "UAV DJI Matrice 300 RTK", "quantity": 3, "unit_price": 485_000_000},
    {"dossier_doc_no": "EVNHANOI-UAV-198-2024", "name": "Camera Zenmuse H20T", "quantity": 3, "unit_price": 125_000_000},
]


async def seed_procurement_items(dossier_id_map: dict[str, int]) -> None:
    async with async_session_factory() as session:
        for item_data in ITEMS_DATA:
            doc_no = item_data.pop("dossier_doc_no")
            dossier_id = dossier_id_map.get(doc_no)
            if not dossier_id:
                continue
            existing = (await session.execute(
                select(ProcurementItem).where(
                    ProcurementItem.dossier_id == dossier_id,
                    ProcurementItem.name == item_data["name"],
                )
            )).scalar_one_or_none()
            if existing:
                item_data["dossier_doc_no"] = doc_no
                continue
            session.add(ProcurementItem(dossier_id=dossier_id, **item_data))
            item_data["dossier_doc_no"] = doc_no
        await session.commit()
```

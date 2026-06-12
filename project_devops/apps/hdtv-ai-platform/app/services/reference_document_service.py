from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import ReferenceDocument
from app.schemas.dossier import ReferenceDocumentCreate


async def create_reference_document(
    session: AsyncSession,
    dossier_id: int,
    data: ReferenceDocumentCreate,
    uploaded_by: int | None = None,
) -> ReferenceDocument:
    """Create a new reference document for a dossier."""
    doc = ReferenceDocument(
        dossier_id=dossier_id,
        file_name=data.file_name,
        file_key=data.file_key,
        file_size=data.file_size,
        content_type=data.content_type,
        uploaded_by=uploaded_by,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


async def list_reference_documents(session: AsyncSession, dossier_id: int) -> list[ReferenceDocument]:
    """List all reference documents for a dossier."""
    result = await session.execute(
        select(ReferenceDocument).where(ReferenceDocument.dossier_id == dossier_id)
    )
    return list(result.scalars().all())


async def get_reference_document(session: AsyncSession, document_id: int) -> ReferenceDocument | None:
    """Get a single reference document by ID."""
    result = await session.execute(
        select(ReferenceDocument).where(ReferenceDocument.id == document_id)
    )
    return result.scalar_one_or_none()


async def delete_reference_document(session: AsyncSession, document_id: int) -> None:
    """Delete a reference document by ID."""
    result = await session.execute(
        select(ReferenceDocument).where(ReferenceDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if doc:
        await session.delete(doc)
        await session.commit()

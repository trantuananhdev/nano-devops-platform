from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.entities import DocumentVersion


async def create_document_version(
    session: AsyncSession,
    dossier_id: int,
    content: str | None,
    content_type: str | None,
    change_description: str | None,
    created_by: int | None = None,
) -> DocumentVersion:
    """Create a new document version, automatically incrementing the version number."""
    
    # Get the latest version number for the dossier
    latest_version = await get_latest_document_version(session, dossier_id)
    next_version = latest_version.version_number + 1 if latest_version else 1
    
    doc_version = DocumentVersion(
        dossier_id=dossier_id,
        version_number=next_version,
        content=content,
        content_type=content_type,
        change_description=change_description,
        created_by=created_by,
    )
    session.add(doc_version)
    await session.commit()
    await session.refresh(doc_version)
    return doc_version


async def get_latest_document_version(
    session: AsyncSession,
    dossier_id: int,
) -> DocumentVersion | None:
    """Get the latest (highest version number) document version for a dossier."""
    result = await session.execute(
        select(DocumentVersion)
        .where(DocumentVersion.dossier_id == dossier_id)
        .order_by(DocumentVersion.version_number.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_document_versions(
    session: AsyncSession,
    dossier_id: int,
) -> list[DocumentVersion]:
    """Get all document versions for a dossier, ordered from newest to oldest."""
    result = await session.execute(
        select(DocumentVersion)
        .where(DocumentVersion.dossier_id == dossier_id)
        .order_by(DocumentVersion.version_number.desc())
    )
    return list(result.scalars().all())


async def get_document_version(
    session: AsyncSession,
    version_id: int,
) -> DocumentVersion | None:
    """Get a specific document version by ID."""
    result = await session.execute(
        select(DocumentVersion).where(DocumentVersion.id == version_id)
    )
    return result.scalar_one_or_none()

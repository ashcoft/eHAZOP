"""Report generation routes."""

import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])
STUDY_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


@router.post("/generate/{study_id}/pdf")
async def generate_pdf_report(
    study_id: str,
    include_safeguards: bool = True,
    include_actions: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate a PDF report for a study."""
    if not STUDY_ID_PATTERN.fullmatch(study_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid study_id format",
        )

    report_service = ReportService(db)
    try:
        pdf_bytes = await report_service.generate_pdf_report(
            study_id,
            include_safeguards=include_safeguards,
            include_actions=include_actions,
        )

        # Save report to storage
        filename = f"report_{study_id}.pdf"
        result = await report_service.save_report(
            study_id=study_id,
            report_type="pdf",
            content=pdf_bytes,
            filename=filename,
        )

        return {
            "status": "success",
            "document_id": result["document_id"],
            "file_name": filename,
            "size": len(pdf_bytes),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/generate/{study_id}/excel")
async def generate_excel_report(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate an Excel report for a study."""
    if not STUDY_ID_PATTERN.fullmatch(study_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid study_id format",
        )

    report_service = ReportService(db)
    try:
        excel_bytes = await report_service.generate_excel_report(study_id)

        # Save report to storage
        filename = f"worksheet_{study_id}.xlsx"
        result = await report_service.save_report(
            study_id=study_id,
            report_type="excel",
            content=excel_bytes,
            filename=filename,
        )

        return {
            "status": "success",
            "document_id": result["document_id"],
            "file_name": filename,
            "size": len(excel_bytes),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/download/{document_id}")
async def download_report(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Download a generated report."""
    from app.services.storage_service import StorageService
    storage_service = StorageService(db)

    content = await storage_service.download_file(document_id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={document_id}"},
    )

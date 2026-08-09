"""数据导入导出路由"""
from __future__ import annotations

import io
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ImportResult
from ..services.csv_io import export_to_csv, import_from_csv

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("/export")
def export_data(db: Session = Depends(get_db)):
    """导出 4 个 CSV 为 zip 文件"""
    zip_bytes = export_to_csv(db)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=lizhang_export.zip"},
    )


@router.post("/import", response_model=ImportResult)
async def import_data(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """接收上传的 CSV 文件，导入数据库

    上传时按文件名识别（persons.csv / relations.csv / events.csv / gifts.csv）
    """
    files_dict = {}
    for f in files:
        content = await f.read()
        files_dict[f.filename] = io.BytesIO(content)
    result = import_from_csv(db, files_dict)
    return result

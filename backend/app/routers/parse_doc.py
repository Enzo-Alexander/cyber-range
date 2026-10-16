"""文档解析：上传 docx/pdf，提取文本和图片。"""
import io
import os
import re
import uuid

from docx import Document as DocxDocument
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pdfminer.high_level import extract_text as extract_pdf_text
from PIL import Image

from ..dependencies import require_role

router = APIRouter(prefix="/admin/parse-doc", tags=["admin-parse-doc"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "articles")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _extract_docx(file_bytes: bytes) -> dict:
    doc = DocxDocument(io.BytesIO(file_bytes))
    lines: list[str] = []
    image_refs: list[str] = []

    # 提取段落文本
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            # 简单处理标题层级
            style = para.style.name if para.style else ""
            if style.startswith("Heading 1") or style == "Title":
                lines.append(f"# {text}")
            elif style.startswith("Heading 2"):
                lines.append(f"## {text}")
            elif style.startswith("Heading 3"):
                lines.append(f"### {text}")
            else:
                lines.append(text)

    # 提取图片：docx 内部 zip 里 word/media/ 下的文件
    from docx.oxml.ns import qn

    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            img_data = rel.target_part.blob
            img_ext = rel.target_part.content_type.split("/")[-1].replace("jpeg", "jpg")
            img_name = f"{uuid.uuid4().hex}.{img_ext}"
            img_path = os.path.join(UPLOAD_DIR, img_name)
            with open(img_path, "wb") as f:
                f.write(img_data)
            image_refs.append(f"/uploads/articles/{img_name}")

    content = "\n\n".join(lines)
    # 在末尾追加图片 markdown
    for ref in image_refs:
        content += f"\n\n![image]({ref})"

    return {"title": "", "content": content, "images": image_refs}


def _extract_pdf(file_bytes: bytes) -> dict:
    text = extract_pdf_text(io.BytesIO(file_bytes))
    # 清理多余空行
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    return {"title": "", "content": text, "images": []}


@router.post("")
async def parse_document(
    file: UploadFile = File(...),
    _admin=Depends(require_role("admin")),
) -> dict:
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ("docx", "pdf"):
        raise HTTPException(status_code=400, detail="仅支持 .docx 和 .pdf 文件")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

    try:
        if ext == "docx":
            result = _extract_docx(file_bytes)
        else:
            result = _extract_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {e}")

    # 用文件名（去扩展名）作为建议标题
    suggested_title = os.path.splitext(filename)[0]
    result["suggested_title"] = suggested_title
    return result

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import APIRouter
from pydantic import BaseModel
from core.data_analyzer import DataFrameAnalyzer

router = APIRouter()

class AnalyzeDataInput(BaseModel):
    dataframe_path: str
    task: str

@router.post("/analyze-dataframe")
async def analyze_dataframe(data_input: AnalyzeDataInput):
    """Analyze dataframe using AI"""
    try:
        analyzer = DataFrameAnalyzer()
        result = analyzer.analyze(data_input.dataframe_path, data_input.task)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


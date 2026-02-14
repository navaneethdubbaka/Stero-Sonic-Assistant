import pandas as pd
from typing import Optional
import re

from core.llm_factory import create_llm


class DataFrameAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        # LLM from factory: uses local Ollama when LOCAL_LLM=True, else Gemini/OpenAI
        self.llm = create_llm(temperature=1)
    
    def analyze(self, dataframe_path: str, task: str) -> dict:
        """Analyze dataframe based on user task"""
        try:
            # Load dataframe
            df = pd.read_csv(dataframe_path)
            columns = df.columns.tolist()
            
            # Create prompt
            prompt = f"""You will be provided with a DataFrame containing specific column names in a Pandas dataset. 
            Based on the operations I want to perform on the DataFrame, you should provide the corresponding Pandas code to achieve those tasks. 
            Also when user asks for visualization you will use NumPy and Matplotlib for better visualization, 
            The code should be clean, well-commented, and optimized for readability.
            
            The dataframe contains the columns {columns}. 
            Now, {task}
            
            If result was a dataframe dont forget to print the dataframe.
            Please provide only the code lines, nothing extra.
            """
            
            # Get response from LLM
            response = self.llm.invoke(prompt)
            code = response.content
            
            # Clean the code
            cleaned_code = self._extract_code(response.content)
            
            # Execute code with dataframe context
            local_vars = {"df": df, "pd": pd}
            exec(cleaned_code, {"__builtins__": __builtins__}, local_vars)
            
            return {
                "code": cleaned_code,
                "success": True,
                "columns": columns,
                "shape": df.shape
            }
        except Exception as e:
            return {
                "code": code if 'code' in locals() else "",
                "success": False,
                "error": str(e)
            }
    
    def _extract_code(self, text: str) -> str:
        """Extract Python code from markdown code blocks"""
        # Remove markdown code blocks
        code = re.sub(r'```python\n?', '', text)
        code = re.sub(r'```\n?', '', code)
        return code.strip()


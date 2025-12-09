import asyncio
import json
import logging
import os
import uuid
import shutil
import google.generativeai as genai
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from google.api_core.exceptions import GoogleAPICallError, RetryError, ResourceExhausted
import pandas as pd
import numpy as np
import zipfile
import openpyxl
from app.core.config import settings
from .precompute_memory import PrecomputeMemory

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure the API key
genai.configure(api_key=settings.GEMINI_API_KEY)

# Get a model instance
model = genai.GenerativeModel(settings.DEFAULT_GEMINI_MODEL)

class PrecomputeService:
    def __init__(self):
        self.precompute_memory = PrecomputeMemory()
        self.data_dir = Path(settings.DATA_DIR)
        self.summary_dir = Path(settings.SUMMARY_DIR)
        self.temp_dir = Path(settings.TEMP_DIR)
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def _symbolic_precompute(self, file_path: Path) -> Dict[str, Any]:
        """Performs symbolic precomputation using pandas."""
        try:
            suffix = file_path.suffix.lower()
            df = pd.DataFrame() # Initialize empty dataframe
            
            if suffix == '.csv':
                try:
                    # Try with the most common encoding first
                    df = await asyncio.to_thread(pd.read_csv, file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    logging.warning(f"UTF-8 decoding failed for {file_path}. Trying 'latin1' encoding.")
                    # Fallback to a more permissive encoding
                    df = await asyncio.to_thread(pd.read_csv, file_path, encoding='latin1')
            elif suffix in ['.xlsx', '.xls']:
                df = await asyncio.to_thread(pd.read_excel, file_path)
            elif suffix == '.json':
                df = await asyncio.to_thread(pd.read_json, file_path, lines=True, orient='records')

            if df.empty:
                return {"error": "The file is empty or could not be parsed."}

            # Generate a more detailed and structured summary
            numeric_df = df.select_dtypes(include=np.number)
            if numeric_df.empty or numeric_df.shape[1] == 0:
                description = {}
            else:
                description = numeric_df.describe().to_dict()

            # Clean up description to be JSON serializable
            for col, stats in description.items():
                for stat, value in stats.items():
                    if pd.isna(value):
                        description[col][stat] = None # Replace NaN with None

            summary = {
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'head': df.head().to_dict('records'),
                'missing_values': {col: int(df[col].isnull().sum()) for col in df.columns if df[col].isnull().sum() > 0},
                'numeric_description': description
            }
            return summary
        except Exception as e:
            logging.exception(f"Error during symbolic precomputation for {file_path}: {e}")
            # Return a structured error to be stored in the context
            return {"error": f"Failed to perform symbolic precomputation: {str(e)}"}

    async def _neuro_symbolic_precompute(self, summary: Dict[str, Any]) -> str:
        """Performs neuro-symbolic precomputation using Gemini."""
        prompt = f"Provide a concise, insightful overview of the following dataset: {json.dumps(summary, indent=2, default=str)}"
        try:
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text
        except ResourceExhausted as exc:
            logging.warning("Gemini API quota exhausted: %s", exc)
            return "AI summary temporarily unavailable due to rate limits. Please try again later."
        except (GoogleAPICallError, RetryError) as exc:
            logging.error("Gemini API error: %s", exc)
            return "Unable to generate AI summary at this time. Please try again later."
        except Exception as e:
            logging.exception("Unexpected error during neuro-symbolic precomputation: %s", e)
            return "An unexpected error occurred while generating the summary."

    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyzes a data file and returns a structured context summary.
        """
        try:
            file_path_obj = Path(file_path)
            
            # Symbolic precomputation
            symbolic_summary = await self._symbolic_precompute(file_path_obj)

            # Neuro-symbolic precomputation for a natural language overview
            neuro_symbolic_overview = await self._neuro_symbolic_precompute(symbolic_summary)

            # Combine into a structured context
            context = {
                "data_id": str(uuid.uuid4()),
                "file_path": str(file_path),
                "symbolic_summary": symbolic_summary,
                "neuro_symbolic_overview": neuro_symbolic_overview,
            }
            
            return context

        except Exception as e:
            logging.error(f"Error processing data for context generation: {e}")
            return {"error": str(e)}

def get_precompute_service():
    return PrecomputeService()

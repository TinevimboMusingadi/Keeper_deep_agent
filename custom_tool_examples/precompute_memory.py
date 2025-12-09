from typing import Dict, Any

class PrecomputeMemory:
    def __init__(self):
        self._summaries: Dict[str, Dict[str, Any]] = {}

    def store_summary(self, data_id: str, summary: Dict[str, Any]):
        self._summaries[data_id] = summary

    def get_summary(self, data_id: str) -> Dict[str, Any]:
        return self._summaries.get(data_id)

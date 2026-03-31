from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseExecutor(ABC):
    """Base class for database executors."""
    
    @abstractmethod
    def execute(self, query: str, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SQL query and return standardized result.
        
        Args:
            query: SQL query string
            connection_config: Database connection configuration
            
        Returns:
            Dict with keys: success, columns, rows, row_count, execution_time, error
        """
        raise NotImplementedError

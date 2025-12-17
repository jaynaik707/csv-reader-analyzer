"""
Abstract base class for data readers
Follows Interface Segregation Principle (ISP) - single responsibility
"""
from abc import ABC, abstractmethod
import pandas as pd


class DataReader(ABC):
    """
    Abstract base class for all data readers
    
    This follows the Open/Closed Principle:
    - Open for extension (can create new readers)
    - Closed for modification (doesn't change existing code)
    """
    
    @abstractmethod
    def read(self) -> pd.DataFrame:
        """
        Read data from source and return as DataFrame
        
        Returns:
            pd.DataFrame: Data in standardized DataFrame format
            
        Raises:
            Exception: If reading fails
        """
        pass
    
    @abstractmethod
    def validate_source(self) -> bool:
        """
        Validate that the data source is accessible
        
        Returns:
            bool: True if source is valid and accessible
        """
        pass


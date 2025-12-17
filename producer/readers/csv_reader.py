"""
CSV Reader implementation
Follows Single Responsibility Principle - only handles CSV reading
"""
import pandas as pd
import os
import logging
from typing import Optional
from .base_reader import DataReader

# Get logger for this module
logger = logging.getLogger(__name__)


class CSVReader(DataReader):
    """
    Reads order data from CSV files
    
    This class:
    - Implements the DataReader interface (Liskov Substitution Principle)
    - Has single responsibility: CSV file reading
    - Is independent of Kafka or any other downstream system
    """
    
    def __init__(self, file_path: str, encoding: str = 'utf-8'):
        """
        Initialize CSV reader
        
        Args:
            file_path: Path to CSV file
            encoding: File encoding (default: utf-8)
        """
        self.file_path = file_path
        self.encoding = encoding
        self._validate_file_path()
    
    def _validate_file_path(self) -> None:
        """
        Validate file path on initialization
        
        Raises:
            ValueError: If file path is empty or invalid
        """
        if not self.file_path:
            raise ValueError("File path cannot be empty")
        
        if not self.file_path.endswith('.csv'):
            raise ValueError(f"Expected CSV file, got: {self.file_path}")
    
    def validate_source(self) -> bool:
        """
        Check if CSV file exists and is readable
        
        Returns:
            bool: True if file exists and is accessible
        """
        return os.path.isfile(self.file_path) and os.access(self.file_path, os.R_OK)
    
    def read(self) -> pd.DataFrame:
        """
        Read orders from CSV file
        
        Returns:
            pd.DataFrame: Orders data
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            Exception: If reading fails for other reasons
        """
        if not self.validate_source():
            raise FileNotFoundError(f"CSV file not found or not readable: {self.file_path}")
        
        try:
            df = pd.read_csv(self.file_path, encoding=self.encoding)
            logger.info("Loaded %d records from %s", len(df), os.path.basename(self.file_path))
            
            # Basic validation
            if df.empty:
                logger.warning("CSV file is empty: %s", self.file_path)
            
            return df
            
        except pd.errors.EmptyDataError:
            logger.warning("CSV file is empty: %s", self.file_path)
            return pd.DataFrame()
            
        except Exception as e:
            logger.error("Error reading CSV file %s: %s", self.file_path, str(e))
            raise Exception(f"Error reading CSV file {self.file_path}: {str(e)}")
    
    def get_row_count(self) -> int:
        """
        Get number of rows in CSV without loading entire file
        
        Returns:
            int: Number of rows (excluding header)
        """
        if not self.validate_source():
            return 0
        
        with open(self.file_path, 'r', encoding=self.encoding) as f:
            return sum(1 for _ in f) - 1  # Subtract header
    
    def __repr__(self) -> str:
        """String representation"""
        return f"CSVReader(file='{self.file_path}')"


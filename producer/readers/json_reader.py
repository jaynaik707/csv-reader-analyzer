"""
JSON Reader implementation - Example of extensibility
Demonstrates how easy it is to add new data sources
"""
import pandas as pd
import json
import os
import logging
from typing import Optional
from .base_reader import DataReader

# Get logger for this module
logger = logging.getLogger(__name__)


class JSONReader(DataReader):
    """
    Reads order data from JSON files
    
    This demonstrates the Open/Closed Principle:
    - We extended functionality (added JSON support)
    - Without modifying existing code (CSVReader, Pipeline unchanged)
    
    The pipeline can use this reader without any modifications!
    """
    
    def __init__(self, file_path: str, encoding: str = 'utf-8'):
        """
        Initialize JSON reader
        
        Args:
            file_path: Path to JSON file
            encoding: File encoding (default: utf-8)
        """
        self.file_path = file_path
        self.encoding = encoding
        self._validate_file_path()
    
    def _validate_file_path(self) -> None:
        """Validate file path on initialization"""
        if not self.file_path:
            raise ValueError("File path cannot be empty")
        
        if not self.file_path.endswith('.json'):
            raise ValueError(f"Expected JSON file, got: {self.file_path}")
    
    def validate_source(self) -> bool:
        """
        Check if JSON file exists and is readable
        
        Returns:
            bool: True if file exists and is accessible
        """
        return os.path.isfile(self.file_path) and os.access(self.file_path, os.R_OK)
    
    def read(self) -> pd.DataFrame:
        """
        Read orders from JSON file
        
        Supports two JSON formats:
        1. Array of objects: [{"order_id": 1, ...}, {...}]
        2. Lines format: One JSON object per line
        
        Returns:
            pd.DataFrame: Orders data
            
        Raises:
            FileNotFoundError: If JSON file doesn't exist
            Exception: If reading fails
        """
        if not self.validate_source():
            raise FileNotFoundError(f"JSON file not found or not readable: {self.file_path}")
        
        try:
            # Try reading as JSON array first
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                data = json.load(f)
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Single object, wrap in list
                df = pd.DataFrame([data])
            else:
                raise ValueError(f"Unsupported JSON structure: {type(data)}")
            
            logger.info("Loaded %d records from %s", len(df), os.path.basename(self.file_path))
            
            if df.empty:
                logger.warning("JSON file contains no data")
            
            return df
            
        except json.JSONDecodeError as e:
            # Try reading as JSON Lines format
            try:
                df = pd.read_json(self.file_path, lines=True)
                logger.info("Loaded %d records from JSON Lines format", len(df))
                return df
            except Exception:
                logger.error("Invalid JSON format in %s: %s", self.file_path, e)
                raise Exception(f"Invalid JSON format in {self.file_path}: {e}")
        
        except Exception as e:
            logger.error("Error reading JSON file %s: %s", self.file_path, str(e))
            raise Exception(f"Error reading JSON file {self.file_path}: {str(e)}")
    
    def __repr__(self) -> str:
        """String representation"""
        return f"JSONReader(file='{self.file_path}')"


# Example usage:
"""
from readers.json_reader import JSONReader
from producers.kafka_producer import OrderKafkaProducer
from pipeline import OrderPipeline

# Same pipeline code, different reader!
reader = JSONReader('orders.json')

with OrderKafkaProducer('localhost:9092', 'orders') as producer:
    pipeline = OrderPipeline(reader, producer)
    pipeline.run()
"""


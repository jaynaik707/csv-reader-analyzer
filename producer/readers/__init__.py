"""
Data readers package for various data sources
Demonstrates Open/Closed Principle - open for extension
"""
from .base_reader import DataReader
from .csv_reader import CSVReader
from .json_reader import JSONReader

__all__ = ['DataReader', 'CSVReader', 'JSONReader']


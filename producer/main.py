"""
Main entry point for Order Pipeline
Demonstrates clean architecture with separated concerns
"""
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from logging_config import setup_logging
from readers.csv_reader import CSVReader
from producers.kafka_producer import OrderKafkaProducer
from pipeline import OrderPipeline
from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    CSV_FILE_PATH,
    DELAY_SECONDS,
    LOOP_CONTINUOUSLY
)

# Get logger for this module
logger = logging.getLogger(__name__)


def main():
    """
    Main execution function
    
    This demonstrates:
    - Dependency Injection: Components are created and injected
    - Single Responsibility: Each class has one job
    - Open/Closed: Easy to swap implementations
    - Liskov Substitution: Can use any DataReader implementation
    - Interface Segregation: Clean, focused interfaces
    - Dependency Inversion: Main depends on abstractions
    """
    # Setup logging first
    setup_logging(
        level=logging.INFO,  # Change to logging.DEBUG for verbose output
        log_file='logs/pipeline.log',
        log_to_console=True,
        log_to_file=True
    )
    
    logger.info("=" * 60)
    logger.info("  ORDER STREAMING PIPELINE")
    logger.info("=" * 60)
    logger.info("Kafka: %s", KAFKA_BOOTSTRAP_SERVERS)
    logger.info("Topic: %s", KAFKA_TOPIC)
    logger.info("Data Source: %s", CSV_FILE_PATH)
    logger.info("Streaming delay: %ss", DELAY_SECONDS)
    logger.info("Loop continuously: %s", LOOP_CONTINUOUSLY)
    logger.info("=" * 60)
    
    try:
        # Step 1: Create data reader (can easily swap to JSONReader, APIReader, etc.)
        logger.info("Initializing data reader...")
        reader = CSVReader(file_path=CSV_FILE_PATH)
        
        # Validate source before starting
        if not reader.validate_source():
            logger.error("Data source not accessible: %s", CSV_FILE_PATH)
            return 1
        
        logger.info("Data source validated: %s", CSV_FILE_PATH)
        logger.info("Total rows available: %d", reader.get_row_count())
        
        # Step 2: Create Kafka producer with context manager (automatic cleanup)
        logger.info("Setting up Kafka producer...")
        
        with OrderKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            topic=KAFKA_TOPIC,
            use_ssl=False  # Set to True for production with SSL config
        ) as producer:
            
            # Step 3: Create pipeline (orchestrator)
            logger.info("Creating pipeline...")
            pipeline = OrderPipeline(
                reader=reader,
                producer=producer,
                delay_seconds=DELAY_SECONDS,
                batch_size=None  # None = one-by-one, or set to 10 for batch mode
            )
            
            # Step 4: Run pipeline
            pipeline.run(loop_continuously=LOOP_CONTINUOUSLY)
        
        # Producer automatically closed here via context manager
        
        logger.info("Pipeline completed successfully!")
        return 0
        
    except FileNotFoundError as e:
        logger.error("File error: %s", e)
        return 1
    
    except ConnectionError as e:
        logger.error("Connection error: %s", e)
        logger.error("Make sure Kafka is running: docker-compose up -d")
        return 1
    
    except KeyboardInterrupt:
        logger.warning("Interrupted by user (Ctrl+C)")
        return 130
    
    except Exception as e:
        logger.critical("Unexpected error: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    """Entry point when script is run directly"""
    exit_code = main()
    sys.exit(exit_code)


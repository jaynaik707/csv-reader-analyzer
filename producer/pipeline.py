"""
Order Pipeline - Orchestrates data reading and Kafka producing
Follows Single Responsibility Principle - only handles orchestration
"""
import time
import logging
from typing import Optional
from readers.base_reader import DataReader
from producers.kafka_producer import OrderKafkaProducer

# Get logger for this module
logger = logging.getLogger(__name__)


class OrderPipeline:
    """
    Pipeline that orchestrates data flow from reader to producer
    
    This class:
    - Follows Dependency Inversion Principle: depends on abstractions (DataReader), not concrete classes
    - Has single responsibility: orchestrate data flow
    - Is Open/Closed: can work with any DataReader implementation without modification
    """
    
    def __init__(
        self, 
        reader: DataReader, 
        producer: OrderKafkaProducer, 
        delay_seconds: float = 0.1,
        batch_size: Optional[int] = None
    ):
        """
        Initialize pipeline
        
        Args:
            reader: Any DataReader implementation (CSV, JSON, API, etc.)
            producer: Kafka producer instance
            delay_seconds: Delay between messages to simulate streaming
            batch_size: If set, send in batches instead of one-by-one
        """
        self.reader = reader
        self.producer = producer
        self.delay_seconds = delay_seconds
        self.batch_size = batch_size
        self.stats = {'iterations': 0, 'total_records': 0}
    
    def run(self, loop_continuously: bool = False) -> None:
        """
        Execute pipeline: Read data and send to Kafka
        
        Args:
            loop_continuously: If True, loop through data indefinitely
        """
        logger.info("Starting Order Pipeline")
        logger.info("Reader: %s", self.reader)
        logger.info("Producer: %s", self.producer)
        logger.info("Streaming delay: %ss", self.delay_seconds)
        logger.info("-" * 60)
        
        try:
            while True:
                self.stats['iterations'] += 1
                
                if loop_continuously:
                    logger.info("Iteration %d", self.stats['iterations'])
                
                # Read data from source
                self._process_iteration()
                
                # Exit if not looping
                if not loop_continuously:
                    break
                
                logger.debug("Pausing before next iteration...")
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.warning("Pipeline interrupted by user")
            raise
        except Exception as e:
            logger.error("Pipeline error: %s", e, exc_info=True)
            raise
        finally:
            self._print_summary()
    
    def _process_iteration(self) -> None:
        """Process one iteration of reading and sending data"""
        # Read data
        logger.info("Reading data...")
        df = self.reader.read()
        
        if df.empty:
            logger.warning("No data to process")
            return
        
        # Send to Kafka
        logger.info("Sending %d records to Kafka...", len(df))
        
        if self.batch_size:
            self._send_in_batches(df)
        else:
            self._send_one_by_one(df)
        
        self.stats['total_records'] += len(df)
    
    def _send_one_by_one(self, df) -> None:
        """
        Send records one by one with delay (simulates streaming)
        
        Args:
            df: DataFrame with records
        """
        for idx, row in df.iterrows():
            order_dict = row.to_dict()
            self.producer.send(order_dict, add_metadata=True)
            
            # Simulate streaming delay
            if self.delay_seconds > 0:
                time.sleep(self.delay_seconds)
    
    def _send_in_batches(self, df) -> None:
        """
        Send records in batches (more efficient for large datasets)
        
        Args:
            df: DataFrame with records
        """
        batch_data = []
        
        for idx, row in df.iterrows():
            batch_data.append(row.to_dict())
            
            # Send batch when size reached
            if len(batch_data) >= self.batch_size:
                self.producer.send_batch(batch_data, add_metadata=True)
                batch_data = []
                time.sleep(self.delay_seconds)
        
        # Send remaining records
        if batch_data:
            self.producer.send_batch(batch_data, add_metadata=True)
    
    def _print_summary(self) -> None:
        """Print pipeline execution summary"""
        logger.info("=" * 60)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 60)
        logger.info("Total iterations: %d", self.stats['iterations'])
        logger.info("Total records processed: %d", self.stats['total_records'])
        
        # Get producer stats
        producer_stats = self.producer.get_stats()
        logger.info("Messages sent: %d", producer_stats['sent'])
        logger.info("Messages failed: %d", producer_stats['failed'])
        
        if 'messages_per_second' in producer_stats:
            logger.info("Throughput: %.2f msg/sec", producer_stats['messages_per_second'])
        
        success_rate = 0
        if producer_stats['sent'] + producer_stats['failed'] > 0:
            success_rate = (producer_stats['sent'] / (producer_stats['sent'] + producer_stats['failed'])) * 100
        
        logger.info("Success rate: %.2f%%", success_rate)
        logger.info("=" * 60)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"OrderPipeline(reader={self.reader}, producer={self.producer})"


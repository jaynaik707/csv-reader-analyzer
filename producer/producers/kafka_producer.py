"""
Kafka Producer implementation
Follows Single Responsibility Principle - only handles Kafka operations
Uses confluent-kafka (official Apache Kafka Python client)
"""
from confluent_kafka import Producer
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Get logger for this module
logger = logging.getLogger(__name__)


class OrderKafkaProducer:
    """
    Kafka producer for streaming order data
    
    This class:
    - Has single responsibility: Kafka message production
    - Is independent of data source (doesn't know about CSV)
    - Implements context manager protocol for resource management
    - Follows Dependency Inversion: depends on abstractions (dict), not concrete implementations
    """
    
    def __init__(
        self, 
        bootstrap_servers: str, 
        topic: str,
        use_ssl: bool = False, 
        ssl_config: Optional[Dict[str, Any]] = None,
        producer_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: Kafka bootstrap servers (e.g., 'localhost:9092')
            topic: Kafka topic name
            use_ssl: Whether to use SSL/TLS (for production)
            ssl_config: SSL configuration dictionary
            producer_config: Additional Kafka producer configurations
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.use_ssl = use_ssl
        self.ssl_config = ssl_config or {}
        self.producer_config = producer_config or {}
        self.producer: Optional[Producer] = None
        self.stats = {'sent': 0, 'failed': 0, 'start_time': None, 'end_time': None}
        self.send_timeout_seconds = 10
    
    def __enter__(self):
        """
        Context manager entry point. Initializes the Kafka producer.
        """
        logger.info("Initializing Kafka producer for topic '%s' on servers: %s", self.topic, self.bootstrap_servers)
        self.stats['start_time'] = datetime.now()
        self.producer = self._create_producer()
        logger.info("Kafka producer initialized successfully.")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point. Closes the Kafka producer gracefully.
        Ensures all buffered messages are sent before closing.
        """
        self.stats['end_time'] = datetime.now()
        
        if exc_type is not None:
            logger.error("An error occurred during producer execution: %s: %s", exc_type.__name__, exc_val, exc_info=True)
        
        self.close()
        logger.info("Kafka producer context exited.")
        return False  # Do not suppress exceptions
    
    def _create_producer(self) -> Producer:
        """
        Creates and returns a Producer instance with the configured settings.
        """
        config = {
            'bootstrap.servers': self.bootstrap_servers,
            'acks': 'all',  # Ensure all replicas acknowledge the message
            'retries': 3,   # Number of retries on transient errors
            'max.in.flight.requests.per.connection': 1,  # Guarantees order
            'enable.idempotence': True,  # Prevents duplicates on retries
            'compression.type': 'gzip',  # Compress messages
            **self.producer_config  # Allow overriding default producer configs
        }
        
        if self.use_ssl:
            config.update({
                'security.protocol': 'SSL',
                **self.ssl_config
            })
            logger.info("SSL/TLS enabled for Kafka producer.")
        
        logger.debug("Kafka producer configuration: %s", {k: v for k, v in config.items() if 'ssl' not in k.lower() and 'password' not in k.lower()})
        return Producer(config)
    
    @staticmethod
    def _serialize_json(data: Any) -> bytes:
        """
        Serialize data to JSON bytes.
        Uses default=str to handle non-serializable types like datetime objects.
        """
        return json.dumps(data, default=str).encode('utf-8')
    
    def _add_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds ingestion timestamp and a unique producer ID to the data.
        """
        data_with_metadata = data.copy()
        data_with_metadata['ingestion_time'] = datetime.now().isoformat()
        data_with_metadata['producer_id'] = f'kafka_producer_{id(self)}'  # Unique ID for this producer instance
        return data_with_metadata
    
    def _delivery_callback(self, err, msg):
        """
        Callback function called when a message is delivered or fails.
        
        Args:
            err: Error if message delivery failed, None otherwise
            msg: Message object containing topic, partition, offset
        """
        if err is not None:
            self.stats['failed'] += 1
            logger.error("Message delivery failed: %s", err)
        else:
            self.stats['sent'] += 1
            logger.debug("Message delivered to topic %s partition %d offset %d", 
                        msg.topic(), msg.partition(), msg.offset())
    
    def send(self, data: Dict[str, Any], add_metadata: bool = True) -> bool:
        """
        Sends a single message (order) to the Kafka topic.
        
        Args:
            data: Dictionary containing the message data
            add_metadata: Whether to add ingestion timestamp and producer ID
            
        Returns:
            bool: True if message was queued successfully, False otherwise
        """
        if add_metadata:
            data_to_send = self._add_metadata(data)
        else:
            data_to_send = data
        
        try:
            # Serialize data
            value = self._serialize_json(data_to_send)
            
            # Produce message (non-blocking)
            self.producer.produce(
                topic=self.topic,
                value=value,
                callback=self._delivery_callback
            )
            
            # Poll to trigger callbacks and handle delivery reports
            self.producer.poll(0)
            
            order_id = data_to_send.get('order_id', 'N/A')
            logger.debug("Queued order %s for sending to topic %s", order_id, self.topic)
            return True
                
        except BufferError as e:
            self.stats['failed'] += 1
            logger.error("Local producer queue is full (%d messages awaiting delivery): %s", 
                        len(self.producer), e)
            # Wait for some messages to be delivered
            self.producer.poll(1)
            return False
        except Exception as e:
            self.stats['failed'] += 1
            logger.error("Unexpected error sending message. Order ID: %s: %s", 
                        data_to_send.get('order_id', 'N/A'), e, exc_info=True)
            return False
    
    def flush(self, timeout: float = 30.0) -> int:
        """
        Wait for all messages in the Producer queue to be delivered.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Number of messages still in queue (0 means all delivered)
        """
        logger.info("Flushing producer queue...")
        remaining = self.producer.flush(timeout=timeout)
        if remaining > 0:
            logger.warning("%d messages were not delivered within the timeout", remaining)
        else:
            logger.info("All messages flushed successfully.")
        return remaining
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get producer statistics
        
        Returns:
            Dictionary with sent/failed counts and timing
        """
        stats = self.stats.copy()
        if stats['start_time'] and stats['end_time']:
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            stats['duration_seconds'] = round(duration, 2)
            if duration > 0:
                stats['messages_per_second'] = round(stats['sent'] / duration, 2)
        return stats
    
    def close(self) -> None:
        """
        Close the producer and ensure all messages are sent.
        """
        if self.producer is not None:
            logger.info("Closing Kafka producer...")
            remaining = self.flush()
            if remaining == 0:
                logger.info("Producer closed successfully. Total sent: %d, Failed: %d", 
                           self.stats['sent'], self.stats['failed'])
            else:
                logger.warning("Producer closed with %d messages not delivered", remaining)
            self.producer = None

"""
Configuration for Kafka Producer
"""

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'orders'

# CSV Configuration
CSV_FILE_PATH = '../data/orders.csv'

# Streaming Configuration
DELAY_SECONDS = 0.1  # Delay between messages to simulate streaming
LOOP_CONTINUOUSLY = False  # Set to True to loop through CSV infinitely

# Producer Configuration
PRODUCER_CONFIG = {
    'bootstrap_servers': KAFKA_BOOTSTRAP_SERVERS,
    'value_serializer': lambda v: v.encode('utf-8') if isinstance(v, str) else v,
    'acks': 'all',  # Wait for all replicas to acknowledge
    'retries': 3,
    'max_in_flight_requests_per_connection': 1
}


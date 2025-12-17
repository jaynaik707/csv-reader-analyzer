# Order Pipeline - Clean Architecture Implementation

A professional-grade data pipeline demonstrating SOLID principles and clean architecture patterns.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Order Pipeline                         │
│                    (Orchestrator)                           │
└─────────────────────────────────────────────────────────────┘
                    ↓                    ↓
        ┌───────────────────┐    ┌──────────────────┐
        │   Data Reader     │    │  Kafka Producer  │
        │   (Abstract)      │    │                  │
        └───────────────────┘    └──────────────────┘
                    ↓
        ┌───────────────────┐
        │   CSV Reader      │
        │ (Implementation)  │
        └───────────────────┘
```

## SOLID Principles Applied

### 1. **Single Responsibility Principle (SRP)**
- `CSVReader`: Only reads CSV files
- `OrderKafkaProducer`: Only handles Kafka operations
- `OrderPipeline`: Only orchestrates data flow

### 2. **Open/Closed Principle (OCP)**
- Open for extension: Can add `JSONReader`, `APIReader` without changing existing code
- Closed for modification: Core classes don't need changes for new data sources

### 3. **Liskov Substitution Principle (LSP)**
- Any `DataReader` implementation can replace another without breaking the pipeline
- Pipeline works with `CSVReader`, `JSONReader`, or any future reader

### 4. **Interface Segregation Principle (ISP)**
- Clean, focused interfaces
- `DataReader` only defines necessary methods
- No fat interfaces with unused methods

### 5. **Dependency Inversion Principle (DIP)**
- High-level `OrderPipeline` depends on `DataReader` abstraction
- Low-level `CSVReader` implements the abstraction
- Easy to inject different implementations

## Project Structure

```
producer/
├── main.py                    # Entry point
├── config.py                  # Configuration
├── pipeline.py                # Orchestrator
│
├── readers/                   # Data reading layer
│   ├── __init__.py
│   ├── base_reader.py        # Abstract interface
│   └── csv_reader.py         # CSV implementation
│
├── producers/                 # Message producing layer
│   ├── __init__.py
│   └── kafka_producer.py     # Kafka implementation
│
└── requirements.txt

```

## Design Patterns Used

### 1. **Context Manager Pattern**
- `OrderKafkaProducer` implements `__enter__` and `__exit__`
- Automatic resource cleanup
- Exception-safe resource management

### 2. **Strategy Pattern**
- `DataReader` is the strategy interface
- Different readers (CSV, JSON, API) are concrete strategies
- Pipeline can use any strategy without modification

### 3. **Dependency Injection**
- Components are created externally and injected
- Loose coupling between components
- Easy testing with mocks

### 4. **Template Method Pattern** (partial)
- `DataReader` defines the template (`read()`, `validate_source()`)
- Concrete readers implement specific behavior

## Usage

### Basic Usage

```python
from readers.csv_reader import CSVReader
from producers.kafka_producer import OrderKafkaProducer
from pipeline import OrderPipeline

# Create components
reader = CSVReader('orders.csv')

with OrderKafkaProducer('localhost:9092', 'orders') as producer:
    pipeline = OrderPipeline(reader, producer, delay_seconds=0.1)
    pipeline.run()
```

### Run the Pipeline

```bash
# Start Kafka (in docker-compose directory)
cd ../../spark
docker-compose up -d

# Run the pipeline
cd ../csv-collector/producer
python main.py
```

### Custom Configuration

```python
# Use different reader
from readers.json_reader import JSONReader  # If implemented
reader = JSONReader('orders.json')

# Custom producer config
producer_config = {
    'compression_type': 'snappy',
    'linger_ms': 100
}

with OrderKafkaProducer(
    'localhost:9092', 
    'orders',
    producer_config=producer_config
) as producer:
    pipeline = OrderPipeline(reader, producer)
    pipeline.run()
```

## Extending the System

### Add New Data Source

```python
# readers/api_reader.py
from .base_reader import DataReader

class APIReader(DataReader):
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def validate_source(self) -> bool:
        # Check if API is accessible
        pass
    
    def read(self) -> pd.DataFrame:
        # Fetch from API and convert to DataFrame
        pass
```

Usage:
```python
reader = APIReader('https://api.example.com/orders')
# Rest of code unchanged!
```

### Add New Producer

```python
# producers/rabbitmq_producer.py
class OrderRabbitMQProducer:
    def send(self, data):
        # Send to RabbitMQ
        pass
```

## Testing

Each component can be tested independently:

```python
# Test CSV Reader
def test_csv_reader():
    reader = CSVReader('test_data.csv')
    df = reader.read()
    assert len(df) > 0

# Test Kafka Producer (with mock)
def test_kafka_producer(mocker):
    mock_kafka = mocker.patch('kafka.KafkaProducer')
    producer = OrderKafkaProducer('localhost:9092', 'test')
    # Test producer logic
```

## Benefits of This Architecture

### 1. **Maintainability**
- Each class has one clear responsibility
- Easy to understand and modify
- Changes are localized

### 2. **Testability**
- Components can be tested in isolation
- Easy to mock dependencies
- Clear interfaces for testing

### 3. **Extensibility**
- Add new readers without changing pipeline
- Add new producers without changing readers
- Add new features without modifying existing code

### 4. **Reusability**
- `CSVReader` can be used in other projects
- `KafkaProducer` can be used with different data sources
- Components are decoupled

### 5. **Production-Ready**
- Context managers ensure resource cleanup
- Proper error handling
- Comprehensive logging
- Statistics tracking

## Interview Talking Points

> "I designed this pipeline following SOLID principles. The CSVReader and KafkaProducer are completely decoupled—the reader doesn't know about Kafka, and the producer doesn't know about CSV. This separation allows me to easily swap a JSON or API reader without changing any Kafka code. I used the Strategy pattern for data sources and Context Manager pattern for resource management, ensuring clean, testable, production-ready code."

## Configuration

Edit `config.py` to customize:

```python
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'orders'
CSV_FILE_PATH = '../data/orders.csv'
DELAY_SECONDS = 0.1  # Simulate streaming
LOOP_CONTINUOUSLY = False  # Set True for infinite loop
```

## Error Handling

The pipeline handles:
- Missing CSV files
- Kafka connection failures
- Data validation errors
- Keyboard interrupts (Ctrl+C)
- Automatic resource cleanup on errors

## Performance

- **Throughput tracking**: Messages per second
- **Success rate calculation**: Sent vs failed
- **Batch mode**: Optional batching for higher throughput
- **Compression**: Configurable compression (gzip, snappy)

---

**Author**: Built for Staff Data Platform Engineer portfolio  
**Demonstrates**: Clean Architecture, SOLID Principles, Production-Ready Code


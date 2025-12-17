# Architecture Documentation

## System Overview

This pipeline demonstrates enterprise-grade software architecture following SOLID principles and clean code practices.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│                    (Entry Point / DI Container)                  │
│                                                                  │
│  Creates and injects:                                           │
│  - DataReader (CSVReader / JSONReader / APIReader)             │
│  - OrderKafkaProducer                                           │
│  - OrderPipeline                                                │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ creates & injects
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                      OrderPipeline                               │
│                    (Orchestration Layer)                         │
│                                                                  │
│  Responsibilities:                                              │
│  - Coordinate data flow from reader to producer                │
│  - Handle iteration logic                                       │
│  - Manage streaming delays                                      │
│  - Track statistics                                             │
│                                                                  │
│  Dependencies (injected):                                       │
│  - reader: DataReader (interface)                              │
│  - producer: OrderKafkaProducer                                │
└─────────────────────────────────────────────────────────────────┘
              │                                    │
              │ uses                              │ uses
              ↓                                    ↓
┌─────────────────────────────┐    ┌──────────────────────────────┐
│      DataReader             │    │   OrderKafkaProducer         │
│   (Abstract Interface)      │    │   (Concrete Implementation)  │
│                             │    │                              │
│  + read(): DataFrame        │    │  + send(data): bool          │
│  + validate_source(): bool  │    │  + send_batch(list): dict    │
│                             │    │  + get_stats(): dict         │
│                             │    │  + __enter__()               │
│                             │    │  + __exit__()                │
└─────────────────────────────┘    └──────────────────────────────┘
              ↑                                    │
              │ implements                         │ uses
              │                                    ↓
    ┌─────────┴─────────┐              ┌──────────────────┐
    │                   │              │  KafkaProducer   │
    ↓                   ↓              │  (kafka-python)  │
┌──────────┐    ┌──────────┐         └──────────────────┘
│CSVReader │    │JSONReader│
│          │    │          │
│+ read()  │    │+ read()  │
│          │    │          │
└──────────┘    └──────────┘
```

## Data Flow

```
CSV File              JSON File              REST API
  │                     │                      │
  │                     │                      │
  └──────────┬──────────┴──────────────────────┘
             │ read()
             ↓
      ┌─────────────┐
      │ DataReader  │  Abstract interface
      └─────────────┘
             │ returns DataFrame
             ↓
      ┌─────────────┐
      │  Pipeline   │  Orchestrates flow
      └─────────────┘
             │ for each row
             ↓
      ┌─────────────┐
      │   Producer  │  Adds metadata, sends to Kafka
      └─────────────┘
             │ serializes to JSON
             ↓
      ┌─────────────┐
      │    Kafka    │  Distributed message broker
      │   Topic     │
      └─────────────┘
             │
             ↓
      (Consumed by Spark Streaming)
```

## SOLID Principles Implementation

### 1. Single Responsibility Principle (SRP)

Each class has ONE reason to change:

| Class | Single Responsibility | What Would Cause Change |
|-------|---------------------|------------------------|
| `CSVReader` | Read CSV files | CSV format changes |
| `JSONReader` | Read JSON files | JSON format changes |
| `OrderKafkaProducer` | Send to Kafka | Kafka API changes |
| `OrderPipeline` | Orchestrate flow | Pipeline logic changes |

### 2. Open/Closed Principle (OCP)

```python
# OPEN for extension (add new readers)
class APIReader(DataReader):  # ← New reader
    def read(self):
        # Fetch from API
        pass

# CLOSED for modification (Pipeline code unchanged)
pipeline = OrderPipeline(reader=APIReader(), producer=producer)
pipeline.run()  # Works without any changes!
```

### 3. Liskov Substitution Principle (LSP)

```python
# Any DataReader can replace another
def create_pipeline(reader: DataReader):  # Accepts interface
    with OrderKafkaProducer(...) as producer:
        pipeline = OrderPipeline(reader, producer)
        pipeline.run()

# All of these work identically
create_pipeline(CSVReader('orders.csv'))
create_pipeline(JSONReader('orders.json'))
create_pipeline(APIReader('http://api.example.com/orders'))
```

### 4. Interface Segregation Principle (ISP)

```python
# DataReader interface is minimal and focused
class DataReader(ABC):
    @abstractmethod
    def read(self) -> pd.DataFrame:  # Only what's needed
        pass
    
    @abstractmethod
    def validate_source(self) -> bool:  # Only what's needed
        pass

# No unnecessary methods like:
# - write() ← Not needed in a reader
# - transform() ← Not reader's responsibility
# - send_to_kafka() ← Not reader's responsibility
```

### 5. Dependency Inversion Principle (DIP)

```python
# HIGH-level module (Pipeline) depends on ABSTRACTION (DataReader)
class OrderPipeline:
    def __init__(self, reader: DataReader, producer: OrderKafkaProducer):
        self.reader = reader  # ← Depends on interface, not implementation
        
# LOW-level module (CSVReader) implements ABSTRACTION
class CSVReader(DataReader):  # ← Implements interface
    def read(self):
        pass

# Both depend on the same abstraction (DataReader)
# Neither depends on the other's concrete implementation
```

## Design Patterns

### 1. Strategy Pattern

```python
# Strategy interface
class DataReader(ABC):
    @abstractmethod
    def read(self): pass

# Concrete strategies
class CSVReader(DataReader): ...
class JSONReader(DataReader): ...

# Context uses strategy
class OrderPipeline:
    def __init__(self, reader: DataReader):  # ← Strategy injection
        self.reader = reader
```

### 2. Dependency Injection

```python
# Dependencies created externally and injected
reader = CSVReader('orders.csv')
producer = OrderKafkaProducer('localhost:9092', 'orders')

# Injected into pipeline
pipeline = OrderPipeline(reader, producer)
```

**Benefits:**
- Loose coupling
- Easy testing (inject mocks)
- Flexible configuration

### 3. Context Manager

```python
class OrderKafkaProducer:
    def __enter__(self):
        # Setup: Create Kafka connection
        self.producer = KafkaProducer(...)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup: Close connection
        self.producer.close()

# Automatic resource management
with OrderKafkaProducer(...) as producer:
    producer.send(data)
# Automatically closed, even if exception
```

## Error Handling Strategy

### Layered Error Handling

```
┌─────────────────────────────────────────┐
│  main.py                                │
│  - Catches all exceptions               │
│  - Provides user-friendly messages      │
│  - Returns appropriate exit codes       │
└─────────────────────────────────────────┘
             │ try/except
             ↓
┌─────────────────────────────────────────┐
│  pipeline.py                            │
│  - Catches iteration errors             │
│  - Logs failures                        │
│  - Continues or stops based on config   │
└─────────────────────────────────────────┘
             │ try/except
             ↓
┌──────────────────┐    ┌─────────────────┐
│  CSVReader       │    │ KafkaProducer   │
│  - File errors   │    │  - Connection   │
│  - Format errors │    │  - Send errors  │
└──────────────────┘    └─────────────────┘
```

## Testing Strategy

### Unit Tests (Test Each Component Independently)

```python
# Test reader in isolation
def test_csv_reader():
    reader = CSVReader('test.csv')
    df = reader.read()
    assert len(df) == expected_count

# Test producer in isolation (with mock)
def test_kafka_producer(mocker):
    mock_kafka = mocker.patch('kafka.KafkaProducer')
    producer = OrderKafkaProducer('localhost:9092', 'test')
    result = producer.send({'order_id': 1})
    assert result == True
    mock_kafka.send.assert_called_once()

# Test pipeline (with mocks for reader and producer)
def test_pipeline(mocker):
    mock_reader = mocker.Mock(spec=DataReader)
    mock_producer = mocker.Mock(spec=OrderKafkaProducer)
    
    pipeline = OrderPipeline(mock_reader, mock_producer)
    pipeline.run()
    
    mock_reader.read.assert_called_once()
    assert mock_producer.send.call_count > 0
```

### Integration Tests

```python
# Test with real Kafka (test container)
def test_integration():
    reader = CSVReader('test_data.csv')
    
    with OrderKafkaProducer('testcontainer:9092', 'test') as producer:
        pipeline = OrderPipeline(reader, producer)
        pipeline.run()
        
        stats = producer.get_stats()
        assert stats['sent'] > 0
```

## Extending the System

### Adding a New Data Source (Example: PostgreSQL)

```python
# readers/postgres_reader.py
import psycopg2
from .base_reader import DataReader

class PostgresReader(DataReader):
    def __init__(self, connection_string: str, query: str):
        self.connection_string = connection_string
        self.query = query
    
    def validate_source(self) -> bool:
        try:
            conn = psycopg2.connect(self.connection_string)
            conn.close()
            return True
        except:
            return False
    
    def read(self) -> pd.DataFrame:
        conn = psycopg2.connect(self.connection_string)
        df = pd.read_sql(self.query, conn)
        conn.close()
        return df

# Usage (no changes to pipeline!)
reader = PostgresReader('postgresql://...', 'SELECT * FROM orders')
with OrderKafkaProducer(...) as producer:
    pipeline = OrderPipeline(reader, producer)
    pipeline.run()
```

## Performance Considerations

### Current Implementation
- **Throughput**: ~10-100 msg/sec (with delay simulation)
- **Latency**: Synchronous sends with ack wait
- **Resource usage**: Minimal (single-threaded)

### Optimization Options

1. **Batch Mode**:
```python
pipeline = OrderPipeline(reader, producer, batch_size=100)
# Sends 100 messages at once
```

2. **Async Sends**:
```python
# In producer: Remove future.get() for async
future = self.producer.send(self.topic, value=data)
# Don't wait for ack
```

3. **Compression**:
```python
producer = OrderKafkaProducer(
    ...,
    producer_config={'compression_type': 'snappy'}
)
```

## Monitoring & Observability

### Built-in Metrics

```python
stats = producer.get_stats()
# {
#     'sent': 100,
#     'failed': 2,
#     'elapsed_seconds': 10.5,
#     'messages_per_second': 9.52
# }
```

### Future Enhancements

- Prometheus metrics export
- Grafana dashboards
- Alert on failure rate > threshold
- Distributed tracing (OpenTelemetry)

---

## Summary

This architecture demonstrates:
- ✅ Clean separation of concerns
- ✅ Testable components
- ✅ Extensible design
- ✅ Production-ready patterns
- ✅ SOLID principles
- ✅ Professional code organization

**Perfect for Staff Engineer interviews!**


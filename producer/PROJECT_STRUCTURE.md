# Project Structure

## Complete Directory Tree

```
csv-collector/
│
├── data/                                # Data files
│   └── orders.csv                       # Sample order data (102 rows)
│
├── producer/                            # Producer application
│   │
│   ├── main.py                          # 🚀 ENTRY POINT - Run this!
│   ├── pipeline.py                      # Orchestration logic
│   ├── config.py                        # Configuration settings
│   ├── requirements.txt                 # Python dependencies
│   │
│   ├── readers/                         # 📖 Data reading layer
│   │   ├── __init__.py                  # Package initialization
│   │   ├── base_reader.py               # Abstract DataReader interface
│   │   ├── csv_reader.py                # CSV implementation
│   │   └── json_reader.py               # JSON implementation (example)
│   │
│   ├── producers/                       # 📤 Message producing layer
│   │   ├── __init__.py                  # Package initialization
│   │   └── kafka_producer.py            # Kafka producer implementation
│   │
│   ├── README.md                        # User guide
│   ├── ARCHITECTURE.md                  # Architecture documentation
│   ├── REFACTORING_SUMMARY.md           # Before/After comparison
│   ├── PROJECT_STRUCTURE.md             # This file
│   │
│   └── kafka_producer_old.py.bak        # Original monolithic code (backup)
│
├── consumer/                            # Spark consumer (TODO)
│   └── spark_consumer.py                # To be implemented
│
└── output/                              # Output directories
    ├── valid_orders/                    # Valid processed orders
    ├── invalid_orders/                  # Invalid/rejected orders
    └── metrics/                         # Calculated metrics
```

## File Descriptions

### Core Application Files

#### **main.py** 🚀
- **Purpose**: Application entry point
- **Responsibilities**: 
  - Dependency injection
  - Component initialization
  - Error handling
  - Exit code management
- **Run**: `python main.py`

#### **pipeline.py**
- **Purpose**: Data flow orchestration
- **Responsibilities**:
  - Coordinate reader → producer flow
  - Handle streaming delays
  - Track statistics
  - Manage iterations
- **Key Class**: `OrderPipeline`

#### **config.py**
- **Purpose**: Configuration management
- **Contains**:
  - Kafka settings
  - File paths
  - Timing configurations
- **Modify this** to change settings

### Readers Package

#### **readers/base_reader.py**
- **Purpose**: Abstract interface for all readers
- **Key Class**: `DataReader` (ABC)
- **Methods**:
  - `read() -> DataFrame`
  - `validate_source() -> bool`
- **Pattern**: Template Method

#### **readers/csv_reader.py**
- **Purpose**: Read orders from CSV files
- **Key Class**: `CSVReader`
- **Features**:
  - File validation
  - Error handling
  - Row count tracking
- **Usage**: `reader = CSVReader('orders.csv')`

#### **readers/json_reader.py**
- **Purpose**: Read orders from JSON files
- **Key Class**: `JSONReader`
- **Features**:
  - Supports JSON array format
  - Supports JSON Lines format
  - Automatic format detection
- **Usage**: `reader = JSONReader('orders.json')`

### Producers Package

#### **producers/kafka_producer.py**
- **Purpose**: Send messages to Kafka
- **Key Class**: `OrderKafkaProducer`
- **Features**:
  - Context manager protocol
  - SSL/TLS support
  - Statistics tracking
  - Batch sending
  - Metadata injection
- **Usage**:
```python
with OrderKafkaProducer('localhost:9092', 'orders') as producer:
    producer.send({'order_id': 1})
```

### Documentation Files

#### **README.md**
- User guide
- Quick start instructions
- Usage examples
- Extensibility guide

#### **ARCHITECTURE.md**
- System architecture
- SOLID principles explanation
- Design patterns
- Data flow diagrams
- Testing strategy

#### **REFACTORING_SUMMARY.md**
- Before/After comparison
- Code examples
- Benefits of refactoring
- Interview talking points

## Dependencies

```
requirements.txt:
├── kafka-python==2.0.2     # Kafka client
├── pandas==2.1.4           # Data manipulation
└── python-dateutil==2.8.2  # Date/time utilities
```

Install: `pip install -r requirements.txt`

## How to Run

### 1. Start Kafka
```bash
cd ../../spark
docker-compose up -d
```

### 2. Install Dependencies
```bash
cd ../csv-collector/producer
pip install -r requirements.txt
```

### 3. Run Pipeline
```bash
python main.py
```

### 4. Verify Output
```bash
# Check Kafka topic
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --from-beginning
```

## Quick Test

```python
# test.py
from readers.csv_reader import CSVReader
from producers.kafka_producer import OrderKafkaProducer
from pipeline import OrderPipeline

reader = CSVReader('../data/orders.csv')

with OrderKafkaProducer('localhost:9092', 'orders') as producer:
    pipeline = OrderPipeline(reader, producer, delay_seconds=0.1)
    pipeline.run()
```

## Adding New Features

### Add New Data Source

1. Create `readers/your_reader.py`
2. Implement `DataReader` interface
3. Add to `readers/__init__.py`
4. Use in `main.py`:
   ```python
   reader = YourReader(...)
   ```

### Add New Producer

1. Create `producers/your_producer.py`
2. Implement similar interface
3. Update `pipeline.py` if needed

## Code Statistics

```
Total Files: 14
Total Lines: ~1500

Breakdown:
- main.py:               90 lines
- pipeline.py:          150 lines
- config.py:             25 lines
- readers/base_reader.py:        40 lines
- readers/csv_reader.py:        120 lines
- readers/json_reader.py:       100 lines
- producers/kafka_producer.py:  200 lines
- Documentation:       ~800 lines
```

## Architecture Layers

```
┌─────────────────────────────────────┐
│         Presentation Layer          │
│            (main.py)                │
│    - CLI interface                  │
│    - Dependency injection           │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│        Application Layer            │
│          (pipeline.py)              │
│    - Business logic                 │
│    - Orchestration                  │
└─────────────────────────────────────┘
                 ↓
┌──────────────────┬──────────────────┐
│   Domain Layer   │   Domain Layer   │
│    (readers/)    │   (producers/)   │
│  - Data sources  │  - Messaging     │
└──────────────────┴──────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      Infrastructure Layer           │
│  - kafka-python                     │
│  - pandas                           │
│  - file system                      │
└─────────────────────────────────────┘
```

## Testing Structure (To Be Added)

```
tests/
├── unit/
│   ├── test_csv_reader.py
│   ├── test_json_reader.py
│   ├── test_kafka_producer.py
│   └── test_pipeline.py
│
├── integration/
│   ├── test_csv_to_kafka.py
│   └── test_end_to_end.py
│
└── fixtures/
    ├── test_orders.csv
    └── test_orders.json
```

## Git Structure

```
.gitignore includes:
- __pycache__/
- *.pyc
- .venv/
- output/
- *.bak
```

---

**Navigation**:
- 📖 [README.md](README.md) - User guide
- 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture details
- 🔄 [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - Before/After
- 🚀 [main.py](main.py) - Run this to start!


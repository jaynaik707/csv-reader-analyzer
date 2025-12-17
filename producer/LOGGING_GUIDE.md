# Logging Guide

## Overview

The Order Pipeline now uses Python's `logging` module for professional, production-ready logging instead of print statements.

---

## Benefits Over Print Statements

| Feature | print() | logging |
|---------|---------|---------|
| **Timestamps** | ❌ No | ✅ Automatic |
| **Log Levels** | ❌ No | ✅ DEBUG, INFO, WARNING, ERROR, CRITICAL |
| **File Output** | ❌ Manual | ✅ Automatic |
| **Filtering** | ❌ No | ✅ By level and module |
| **Production-Ready** | ❌ No | ✅ Yes |
| **Structured** | ❌ No | ✅ Yes |

---

## Log Levels

### When to Use Each Level

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG - Detailed diagnostic information
logger.debug("Serializing data: %s", data)
logger.debug("Connecting to %s", server)

# INFO - General informational messages
logger.info("Loaded 102 records from orders.csv")
logger.info("Sent order 1001 to partition 0")

# WARNING - Something unexpected, but not an error
logger.warning("CSV file is empty")
logger.warning("Retrying connection...")

# ERROR - Error occurred, but application continues
logger.error("Failed to send order: %s", error)
logger.error("Connection refused")

# CRITICAL - Severe error, application might crash
logger.critical("Kafka cluster unreachable")
logger.critical("Out of memory")
```

---

## Configuration

### Current Setup (in main.py)

```python
from logging_config import setup_logging

# Setup logging at application start
setup_logging(
    level=logging.INFO,              # Log level
    log_file='logs/pipeline.log',    # Log file path
    log_to_console=True,              # Print to console
    log_to_file=True                  # Write to file
)
```

### Change Log Level

```python
# For production - only important messages
setup_logging(level=logging.INFO)

# For debugging - everything
setup_logging(level=logging.DEBUG)

# For quiet mode - only errors
setup_logging(level=logging.ERROR)
```

---

## Output Formats

### Console Output (Readable)
```
2025-12-17 12:30:45 - main                     - INFO     - Starting Order Pipeline
2025-12-17 12:30:45 - readers.csv_reader       - INFO     - Loaded 102 records from orders.csv
2025-12-17 12:30:45 - producers.kafka_producer - INFO     - Connected to Kafka: localhost:9092
2025-12-17 12:30:46 - producers.kafka_producer - DEBUG    - Sent order 1001 to partition 0
```

### File Output (Detailed)
```
2025-12-17 12:30:45 - main - INFO - main:35 - Starting Order Pipeline
2025-12-17 12:30:45 - readers.csv_reader - INFO - read:67 - Loaded 102 records from orders.csv
```

Includes:
- Timestamp
- Module name
- Log level
- Function name and line number
- Message

---

## Usage Examples

### In Your Modules

```python
# At the top of each file
import logging

logger = logging.getLogger(__name__)  # Use module name

# In your code
class MyClass:
    def my_method(self):
        logger.info("Starting process")
        
        try:
            result = do_something()
            logger.debug("Result: %s", result)
            return result
        except Exception as e:
            logger.error("Process failed: %s", e, exc_info=True)
            raise
```

### String Formatting

**❌ Bad (slow):**
```python
logger.info(f"Sent order {order_id}")  # Formats even if not logged
```

**✅ Good (fast):**
```python
logger.info("Sent order %s", order_id)  # Only formats if logged
```

### Including Exception Details

```python
try:
    risky_operation()
except Exception as e:
    # Logs exception with full traceback
    logger.error("Operation failed", exc_info=True)
    
    # Or
    logger.exception("Operation failed")  # Automatically includes traceback
```

---

## Log File Location

```
producer/
└── logs/
    └── pipeline.log    # All logs written here
```

**Log rotation** (optional, add later):
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/pipeline.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5            # Keep 5 old files
)
```

---

## Controlling Verbosity

### Environment-Based Configuration

```python
import os
import logging

# In main.py
log_level = os.getenv('LOG_LEVEL', 'INFO')
setup_logging(level=getattr(logging, log_level))
```

**Usage:**
```bash
# Normal mode
python main.py

# Debug mode
LOG_LEVEL=DEBUG python main.py

# Quiet mode
LOG_LEVEL=ERROR python main.py
```

---

## Module-Specific Logging

### Reduce Noise from kafka-python

Already configured in `logging_config.py`:

```python
# Reduce Kafka library verbosity
logging.getLogger('kafka').setLevel(logging.WARNING)
```

### Debug Only Specific Modules

```python
# After setup_logging()

# Debug only the producer
logging.getLogger('producers.kafka_producer').setLevel(logging.DEBUG)

# Keep others at INFO
logging.getLogger('readers').setLevel(logging.INFO)
```

---

## Production Best Practices

### 1. Use Appropriate Levels

```python
# ✅ Good
logger.info("Pipeline started")              # User-facing info
logger.debug("Config: %s", config)           # Debug details
logger.error("Connection failed: %s", e)     # Errors

# ❌ Bad
logger.info("Variable x = 5")                # Too verbose for INFO
logger.error("User logged in")               # Not an error!
```

### 2. Don't Log Sensitive Data

```python
# ❌ Bad - logs password
logger.info("Connecting with password: %s", password)

# ✅ Good - hides password
logger.info("Connecting with credentials")
logger.debug("Password length: %d chars", len(password))
```

### 3. Use Structured Logging (Advanced)

```python
# Install: pip install python-json-logger

from pythonjsonlogger import jsonlogger

handler = logging.FileHandler('logs/pipeline.json')
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)

logger.info("Order sent", extra={
    'order_id': 1001,
    'user_id': 501,
    'amount': 599.99
})
```

**Output (JSON):**
```json
{
  "timestamp": "2025-12-17T12:30:45",
  "level": "INFO",
  "message": "Order sent",
  "order_id": 1001,
  "user_id": 501,
  "amount": 599.99
}
```

---

## Monitoring & Alerting

### Log Aggregation

Send logs to:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **AWS CloudWatch**
- **Datadog**
- **Azure Monitor**

### Simple Log Analysis

```bash
# Count errors
grep "ERROR" logs/pipeline.log | wc -l

# Find specific order
grep "order 1001" logs/pipeline.log

# Tail logs in real-time
tail -f logs/pipeline.log

# Last 100 errors
grep "ERROR" logs/pipeline.log | tail -100
```

---

## Troubleshooting

### Logs Not Appearing

```python
# Check logging is configured
import logging
print(logging.root.level)  # Should not be 0

# Force immediate flush
logging.getLogger().handlers[0].flush()
```

### Too Verbose

```python
# Increase log level
setup_logging(level=logging.WARNING)  # Only warnings and above
```

### Want Console Only

```python
setup_logging(
    log_to_console=True,
    log_to_file=False
)
```

---

## Interview Talking Points

> "I implemented comprehensive logging using Python's logging module instead of print statements. I configured different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) to provide operational visibility. Logs include timestamps, module names, and context, and are written to both console and file. This enables monitoring, debugging, and troubleshooting in production. I also reduced noise from third-party libraries like kafka-python by setting module-specific log levels."

**Shows:**
- ✅ Production-ready thinking
- ✅ Operational awareness
- ✅ Best practices
- ✅ Professional development

---

## Quick Reference

```python
# Setup (once in main.py)
from logging_config import setup_logging
setup_logging(level=logging.INFO)

# Use in any module
import logging
logger = logging.getLogger(__name__)

# Log messages
logger.debug("Detailed info")
logger.info("General info")
logger.warning("Warning")
logger.error("Error: %s", error)
logger.critical("Critical issue")

# With exception
logger.exception("Failed")  # Includes traceback
```

---

## Summary

✅ **Replaced all print() statements with logger calls**  
✅ **Configured console and file logging**  
✅ **Added appropriate log levels**  
✅ **Included timestamps and module names**  
✅ **Production-ready logging infrastructure**

**Your pipeline now has professional logging!** 🚀


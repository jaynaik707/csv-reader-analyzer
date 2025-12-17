"""
Spark Kafka Consumer
Reads streaming data from Kafka topic and provides DataFrame for processing
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_spark_session(app_name: str = "OrderStreamingConsumer") -> SparkSession:
    """
    Create Spark session with Kafka integration
    
    Returns:
        SparkSession configured for Kafka streaming
    """
    logger.info("Creating Spark session...")
    
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .config("spark.sql.streaming.checkpointLocation", "./checkpoint") \
        .master("local[*]") \
        .getOrCreate()
    
    # Set log level
    spark.sparkContext.setLogLevel("WARN")
    
    logger.info("Spark session created successfully")
    return spark


def get_order_schema() -> StructType:
    """
    Define the schema for order data from Kafka
    
    Returns:
        StructType: Schema matching the order JSON structure
    """
    return StructType([
        StructField("order_id", StringType(), True),
        StructField("user_id", StringType(), True),
        StructField("product_id", StringType(), True),
        StructField("category", StringType(), True),
        StructField("price_per_unit", DoubleType(), True),
        StructField("amount", DoubleType(), True),
        StructField("status", StringType(), True),
        StructField("order_timestamp", StringType(), True),  # We'll parse this to timestamp
        StructField("ingestion_time", StringType(), True),
        StructField("producer_id", StringType(), True),
    ])


def read_from_kafka(spark: SparkSession, 
                    kafka_bootstrap_servers: str = "localhost:9092",
                    topic: str = "orders",
                    starting_offset: str = "earliest") -> "DataFrame":
    """
    Read streaming data from Kafka topic
    
    Args:
        spark: SparkSession instance
        kafka_bootstrap_servers: Kafka server address
        topic: Kafka topic name
        starting_offset: Where to start reading ('earliest' or 'latest')
        
    Returns:
        Streaming DataFrame with parsed order data
    """
    logger.info(f"Connecting to Kafka: {kafka_bootstrap_servers}")
    logger.info(f"Reading from topic: {topic}")
    logger.info(f"Starting offset: {starting_offset}")
    
    # Read from Kafka
    kafka_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", topic) \
        .option("startingOffsets", starting_offset) \
        .load()
    
    logger.info("Connected to Kafka successfully")
    
    # Kafka gives us: key, value, topic, partition, offset, timestamp, timestampType
    # We need to parse the 'value' field which contains our JSON
    
    # Convert binary value to string
    kafka_df = kafka_df.selectExpr("CAST(value AS STRING) as json_string")
    
    # Define schema for parsing
    order_schema = get_order_schema()
    
    # Parse JSON and extract fields
    parsed_df = kafka_df.select(
        from_json(col("json_string"), order_schema).alias("data")
    ).select("data.*")
    
    logger.info("DataFrame schema:")
    parsed_df.printSchema()
    
    return parsed_df


def main():
    """
    Main entry point - sets up Kafka connection and provides DataFrame
    """
    logger.info("=" * 60)
    logger.info("  SPARK KAFKA CONSUMER")
    logger.info("=" * 60)
    
    # Configuration
    # Use 'kafka:9093' when Spark runs in Docker
    # Use 'localhost:9092' when Spark runs on host machine
    KAFKA_SERVERS = "kafka:9093"  # Docker-to-Docker communication
    TOPIC = "orders"
    
    try:
        # Create Spark session
        spark = create_spark_session()
        
        # Read from Kafka
        orders_df = read_from_kafka(
            spark=spark,
            kafka_bootstrap_servers=KAFKA_SERVERS,
            topic=TOPIC,
            starting_offset="earliest"  # Read all messages from beginning
        )
        
        logger.info("=" * 60)
        logger.info("  DATAFRAME READY FOR PROCESSING")
        logger.info("=" * 60)
        logger.info("Available columns:")
        for col_name in orders_df.columns:
            logger.info(f"  - {col_name}")
        logger.info("=" * 60)
        
        # ============================================================
        # TODO: ADD YOUR PROCESSING LOGIC HERE
        # ============================================================
        # 
        # The 'orders_df' is now available for you to:
        # 1. Apply data validation (check for nulls, negative amounts, etc.)
        # 2. Filter valid vs invalid records
        # 3. Calculate metrics (aggregations, windowing)
        # 4. Write outputs to files/console
        #
        # Example operations you can do:
        # - orders_df.filter(col("total_amount") > 0)
        # - orders_df.groupBy("category").count()
        # - orders_df.writeStream.format("console").start()
        # ============================================================
        
        # For now, just display the data to console
        logger.info("Starting streaming query (displaying to console)...")
        
        query = orders_df \
            .writeStream \
            .outputMode("append") \
            .format("console") \
            .option("truncate", False) \
            .start()
        
        logger.info("Streaming query started. Press Ctrl+C to stop...")
        query.awaitTermination()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal. Stopping...")
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down Spark session...")
        if 'spark' in locals():
            spark.stop()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()


"""
Quick test to verify Kafka connectivity
"""
import socket
from confluent_kafka import Consumer, KafkaException

def test_port(host, port):
    """Test if port is open"""
    print(f"\n1. Testing TCP connection to {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Port {port} is OPEN and accessible")
            return True
        else:
            print(f"   ❌ Port {port} is CLOSED")
            print(f"   💡 Hint: Run 'docker-compose up -d' in csv-collector/")
            return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def test_kafka_consumer(bootstrap_servers):
    """Test Kafka consumer connection"""
    print(f"\n2. Testing Kafka consumer with {bootstrap_servers}...")
    try:
        conf = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': 'test-connection-group',
            'auto.offset.reset': 'earliest',
            'session.timeout.ms': 6000
        }
        
        consumer = Consumer(conf)
        
        # Try to list topics (this forces a connection)
        metadata = consumer.list_topics(timeout=10)
        
        print(f"   ✅ Successfully connected to Kafka!")
        print(f"   ✅ Found {len(metadata.topics)} topics:")
        
        for topic_name in metadata.topics.keys():
            print(f"      - {topic_name}")
        
        if 'orders' in metadata.topics:
            print(f"   ✅ Topic 'orders' exists and is ready")
        else:
            print(f"   ⚠️  Topic 'orders' NOT found")
            print(f"   💡 Hint: Run producer first: cd ../producer && python main.py")
        
        consumer.close()
        return True
        
    except KafkaException as e:
        print(f"   ❌ Kafka error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def main():
    print("=" * 60)
    print("  KAFKA CONNECTION TEST")
    print("=" * 60)
    
    # Test localhost:9092
    host = "localhost"
    port = 9092
    bootstrap_servers = f"{host}:{port}"
    
    # Test 1: Port accessibility
    port_open = test_port(host, port)
    
    if not port_open:
        print("\n" + "=" * 60)
        print("  ❌ FAILED: Kafka port not accessible")
        print("=" * 60)
        print("\nTroubleshooting steps:")
        print("1. cd csv-collector")
        print("2. docker-compose up -d")
        print("3. docker-compose logs kafka")
        print("4. Wait for 'started (kafka.server.KafkaServer)'")
        return
    
    # Test 2: Kafka connection
    kafka_ok = test_kafka_consumer(bootstrap_servers)
    
    print("\n" + "=" * 60)
    if kafka_ok:
        print("  ✅ SUCCESS: Kafka is ready!")
        print("=" * 60)
        print(f"\nYou can now run:")
        print("  python spark_consumer.py")
    else:
        print("  ❌ FAILED: Kafka connection failed")
        print("=" * 60)
        print("\nCheck Docker logs:")
        print("  docker-compose logs kafka")

if __name__ == "__main__":
    main()


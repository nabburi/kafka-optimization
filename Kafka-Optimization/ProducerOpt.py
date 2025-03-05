from kafka import KafkaProducer
import json
import time

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    buffer_memory=104857600  # 100MB buffer (default 32MB)
    )  # Default settings
start_time = time.time()
for i in range(10000):
    message = json.dumps({"id": i, "data": "test"})
    producer.send('test-opt-2', value=message.encode('utf-8'))
producer.flush()
end_time = time.time()
print(f"Producer time: {end_time - start_time:.2f}s, Throughput: {1000 / (end_time - start_time):.2f} events/sec")
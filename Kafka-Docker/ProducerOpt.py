from kafka import KafkaProducer
import time

start = time.perf_counter()
producer = KafkaProducer(
    bootstrap_servers=['localhost:19092', 'localhost:19093', 'localhost:19094'],
    batch_size=32 * 1024, # 32KB
    linger_ms=10,# 5ms before sending a batch
    compression_type='gzip', # Gzip compression
    acks='all', # Wait for all replicas to acknowledge
    )
payload = "x" * 1000
for i in range(21000):
    producer.send('test-topic', value=(f"msg-{i}-{payload}").encode(), partition=i % 6)
producer.flush()
end = time.perf_counter()
elapsed = end - start
throughput = 21000 / elapsed
print(f"Producer time: {elapsed:.2f}s, Throughput: {throughput:.2f} events/sec")
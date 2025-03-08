from kafka import KafkaProducer
import time

start = time.time()
producer = KafkaProducer(bootstrap_servers=['localhost:19092', 'localhost:19093', 'localhost:19094'])
payload = "x" * 1000
for i in range(21000):
    producer.send('test-topic-1', value=(f"msg-{i}-{payload}").encode(), partition=i % 3)
producer.flush()
end = time.time()
elapsed = end - start
throughput = 21000 / elapsed
print(f"Producer time: {elapsed:.2f}s, Throughput: {throughput:.2f} events/sec")
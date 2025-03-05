from confluent_kafka import Consumer, TopicPartition
from multiprocessing import Process
import json
import time

def consume_messages(consumer_id):
    conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': f'test-group-{consumer_id}',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
        'fetch.max.bytes': 524288000,
        'max.partition.fetch.bytes': 10485760,
        'fetch.min.bytes': 1,
        'socket.receive.buffer.bytes': 100000000
    }
    consumer = Consumer(conf)
    consumer.subscribe(['test-opt-1'])
    consumer.assign([TopicPartition('test-opt-2', 0, 0)])
    start_time = time.time()
    count = 0
    while count < 5000:
        msg = consumer.poll(timeout=0.005)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer {consumer_id} error: {msg.error()}")
            break
        count += 1
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Consumer {consumer_id} fetched {count} messages in {total_time:.2f}s, Throughput: {5000 / total_time:.2f} events/sec")
    consumer.close()
    return total_time

if __name__ == '__main__':
    processes = []
    start_time = time.time()
    for i in range(2):
        p = Process(target=consume_messages, args=(i,))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total Consumer time: {total_time:.2f}s, Throughput: {10000 / total_time:.2f} events/sec")
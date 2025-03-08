from confluent_kafka import Consumer, TopicPartition
from multiprocessing import Process
import json
import time

def consume_messages(consumer_id):
    conf = {
        'bootstrap.servers': 'localhost:19092',
        'group.id': f'test-group-{consumer_id}',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
        'fetch.max.bytes': 52428800,
        'max.partition.fetch.bytes': 10485760,
        'fetch.min.bytes': 524288,
        'socket.receive.buffer.bytes': 100000000,
    }
    consumer = Consumer(conf)
    consumer.subscribe(['test-topic-1'])
    consumer.assign([TopicPartition('test-topic-1', consumer_id, 0)])
    start_time = time.perf_counter()
    count = 0
    while count < 7000:
        msg = consumer.poll(timeout=0.1)
        
        if msg is None:
            continue
        elif msg.error():
            print(f"Consumer {consumer_id} error: {msg.error()}")
            break
        count += 1
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f"Consumer {consumer_id} fetched {count} messages in {total_time:.2f}s, Throughput: {7000 / total_time:.2f} events/sec")
    consumer.close()
    return total_time

if __name__ == '__main__':
    processes = []
    start_time = time.perf_counter()
    for i in range(3):
        p = Process(target=consume_messages, args=(i,))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f"Total Consumer time: {total_time:.2f}s, Throughput: {21000 / total_time:.2f} events/sec")
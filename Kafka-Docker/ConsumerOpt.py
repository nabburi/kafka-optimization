from confluent_kafka import Consumer, TopicPartition
from multiprocessing import Process
import time

MAX_EMPTY_POLLS = 5  # Stop after 5 empty polls

def consume_messages(consumer_id, partition):
    conf = {
        'bootstrap.servers': 'localhost:19092',
        'group.id': 'test-group',  
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,  
        'fetch.max.bytes': 100000000,  # 100MB
        'max.partition.fetch.bytes': 20000000,  # 20MB
        'fetch.min.bytes': 1048576,  # 1MB
        'socket.receive.buffer.bytes': 50000000,  # 50MB
        'session.timeout.ms': 120000,  # Avoid unnecessary rebalances (120 sec)
        'heartbeat.interval.ms': 40000,  # Reduce heartbeat overhead (40 sec)
    }

    consumer = Consumer(conf)
    consumer.assign([TopicPartition('test-topic', partition)])

    start_time = time.perf_counter()
    count = 0
    empty_polls = 0

    while empty_polls < MAX_EMPTY_POLLS:
        msg = consumer.poll(timeout=0.1)

        if msg is None:
            empty_polls += 1
            continue
        elif msg.error():
            print(f"Consumer {consumer_id} error: {msg.error()}")
            break

        count += 1
        empty_polls = 0  # Reset empty poll count

    end_time = time.perf_counter()
    total_time = end_time - start_time
    throughput = count / total_time if total_time > 0 else 0

    print(f"Consumer {consumer_id} fetched {count} messages in {total_time:.2f}s, Throughput: {throughput:.2f} events/sec")

    consumer.close()

if __name__ == '__main__':
    processes = []
    start_time = time.perf_counter()

    for i in range(6):  # Launch 6 consumers for 6 partitions
        p = Process(target=consume_messages, args=(i, i))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f"Total Consumer time: {total_time:.2f}s, Throughput: {21000 / total_time:.2f} events/sec")
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'test-topic',
    bootstrap_servers='localhost:9092',
    group_id='my-group',
    auto_offset_reset='earliest',  # Ch. 3 reliability
    #enable_auto_commit=True  # Ch. 3 reliability
)

print('polling "test-topic" with "my-group"...')
while True:
    try:
        messages = consumer.poll(timeout_ms=1000)
        for topic_partition, partition_messages in messages.items():
            for message in partition_messages:
                print(f"Received: {message.value.decode('utf-8')}, key: {message.key.decode('utf-8')}, Partition: {message.partition}")
    except Exception as e:
        print(f"Error: {e}")
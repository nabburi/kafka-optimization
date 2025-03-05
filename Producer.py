from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    acks=1  # Ch. 3 reliability
)

topic = 'test-topic'
for i in range(1, 80):
    message = f"test {i}"
    key = b"User A"  # Ch. 3 + blog #4 order
    producer.send(topic, key=key, value=message.encode('utf-8'))
    print(f"Sent: {message}")

producer.flush()
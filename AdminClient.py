from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaProducer
import time

# Initialize the Kafka admin client
admin_client = KafkaAdminClient(
    bootstrap_servers=['localhost:9092'],
    client_id='preferred-leader-election'
)

# List all topics
topics = admin_client.list_topics()

# For each topic, perform a preferred leader election
for topic in topics:
    partitions = admin_client.describe_topics([topic])[0].partitions
    for partition in partitions:
        admin_client.elect_preferred_leader(topic, partition.partition)

admin_client.close()
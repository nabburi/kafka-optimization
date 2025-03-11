#!/bin/bash

# Variables
TOPIC="__consumer_offsets"
BROKER1=1  # Broker ID 1
BROKER2=2  # Broker ID 2
BROKER3=3  # Broker ID 3
PARTITION_COUNT=50  # Number of partitions for __consumer_offsets topic

# Start of JSON file
echo '{"topics": [' > reassign-topic-replica.json
echo '  {' >> reassign-topic-replica.json
echo '    "topic": "__consumer_offsets",' >> reassign-topic-replica.json
echo '    "partitions": [' >> reassign-topic-replica.json

# Loop through all partitions
for i in $(seq 0 $((PARTITION_COUNT-1))); do
  if [ $i -eq 0 ]; then
    # First partition does not have a comma before it
    echo "      {\"partition\": $i, \"replicas\": [$BROKER1, $BROKER2, $BROKER3]}" >> reassign-topic-replica.json
  else
    # Subsequent partitions have a comma before them
    echo "      ,{\"partition\": $i, \"replicas\": [$BROKER1, $BROKER2, $BROKER3]}" >> reassign-topic-replica.json
  fi
done

# End of JSON file
echo '    ]' >> reassign-topic-replica.json
echo '  }' >> reassign-topic-replica.json
echo ']' >> reassign-topic-replica.json
echo '}' >> reassign-topic-replica.json

echo "Reassignment JSON file created: reassign-topic-replica.json"
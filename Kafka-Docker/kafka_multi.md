- 3-broker cluster up (kafka-1:9092/19092, kafka-2:9093/19093, kafka-3:9094/19094) + Zookeeper (2181).
- Challenges:
  - Wrong path: /usr/bin/kafka-topics.sh - used /usr/bin/kafka-topics.
  - Timeouts: "Timed out waiting for a node assignment" - localhost vs. kafka-1:9092.
  - Connectivity: "Node 2 unreachable" - restarted, listed all brokers.
  - Crashes: Container exits - cleared ports (netstat).
  - Listener Errors: Port clashes, name mismatches - fixed with dual listeners (909X/1909X).
  - Producer: ~33.12 events/sec - corrected loop/timing.
  - Consumer: "Bootstrap broker disconnected" - added PLAINTEXT_HOST on 1909X.
  - Group: "test-group does not exist" - created via consumer.
- Fixes:
  - Corrected paths, used service names (kafka-X:909X).
  - KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:909X,PLAINTEXT_HOST://0.0.0.0:1909X.
  - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka-X:909X,PLAINTEXT_HOST://localhost:1909X.
  - Producer: ~19k events/sec on 1909X, consumer via localhost:19092, group test-group.
- Result: test-topic (2 replicas, 3 partitions), ~19k events/sec, spread (e.g., kafka-1: 6k, kafka-2: 6k, kafka-3: 7k).

KAFKA_ADVERTISED_LISTENERS: The most common issue is that the KAFKA_ADVERTISED_LISTENERS setting in your broker configuration is incorrect or missing. This setting tells Kafka clients where to connect to the brokers.

    Internal vs. External Addresses: If you're running Kafka in Docker, you likely need to configure the brokers to listen on two endpoints: one for internal communication within the Docker network and another for external access from clients outside the Docker environment.
            KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://<internal_ip_address>:9092,EXTERNAL://<external_ip_address>:9092

https://docs.confluent.io/platform/current/kafka/multi-node.html

version: '3': Docker Compose spec—ensures compatibility.
image: confluentinc/cp-zookeeper:latest: Official Zookeeper—Kafka’s coordinator for broker election, metadata.
ports: "2181:2181": Maps host port 2181 to container 2181—Zookeeper client access.
ZOOKEEPER_CLIENT_PORT: 2181: Tells Zookeeper where to listen—matches port mapping.
image: confluentinc/cp-kafka:latest: Official Kafka—runs brokers.
ports: "9092:9092", "19092:19092": Maps internal 9092 (cluster) and 19092 (host) to host ports—dual access.
depends_on: - zookeeper: Ensures Zookeeper starts first—Kafka needs it.
KAFKA_BROKER_ID: 1: Unique broker identifier—required for cluster.
KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181: Links Kafka to Zookeeper—service name resolves in Docker network.
KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,PLAINTEXT_HOST://0.0.0.0:19092: Defines bind addresses—9092 for internal cluster, 19092 for host (unsecured).
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka-1:9092,PLAINTEXT_HOST://localhost:19092: What clients use—kafka-1:9092 for internal, localhost:19092 for host.
KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT: Maps listener names to protocols—all unencrypted for simplicity.
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 2: Replicates offset topic across 2 brokers—ensures fault tolerance (3 brokers, 2 replicas safe).
=======================================================================================================
Calculation Check:

    Per consumer: 7,000 messages ÷ 2.19s ≈ 3,196–3,199 events/sec (matches your output).
    Total: 21,000 messages ÷ 2.20s ≈ 9,562 events/sec (matches your output).

The numbers align with a localhost Kafka broker serving small messages (10 bytes) with a 100µs delay per message slowing things down intentionally.

How to Calculate Throughput

Throughput in event streaming is simply the number of events (messages) processed divided by the time taken, expressed as events per second (events/sec). Here’s how it works in your code:
Per Consumer:

    Formula: throughput = target_messages / total_time
    Example (Consumer 0):
        target_messages = 7,000
        total_time = 2.19s
        throughput = 7,000 ÷ 2.19 ≈ 3,196.87 events/sec

Total Across All Consumers:

    Formula: total_throughput = total_target_messages / total_time
    Example:
        total_target_messages = 7,000 × 3 = 21,000
        total_time = 2.20s (time from start of first process to end of last)
        total_throughput = 21,000 ÷ 2.20 ≈ 9,562.09 events/sec

Key Notes:

    Parallelism: Since you’re using 3 processes, the total throughput is the sum of individual throughputs, adjusted for the fact that they run concurrently. The total_time is the wall-clock time, not the sum of individual times.
    Precision: Use time.perf_counter() (as you did) for accurate timing, especially for short durations.

Key Observations:

    Runtime Consistency:
        All consumers finish in ~2.19s, and the total time is 2.20s. This is expected with multiprocessing.Process, as the consumers run in parallel, and the total time reflects the longest-running process plus minor overhead.
    Artificial Delay Impact:
        You added time.sleep(0.0001) (100µs) per message.
        For 7,000 messages: 7,000 × 0.0001s = 0.7s of pure sleep time.
        Actual runtime is 2.19s, so ~1.49s is spent on fetching, processing, and overhead. This suggests the Kafka fetch operations are still relatively fast (~4,700 events/sec without the delay).
    Throughput Drop:
        Reducing fetch.max.bytes to 5MB (from 50MB) and removing max.poll.records likely forced smaller batches, spreading the work over more poll() calls and reducing the throughput from the previous unrealistic levels.
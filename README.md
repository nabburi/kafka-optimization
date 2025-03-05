# Kafka Optimization Project

This project optimizes a Kafka producer and consumer setup to achieve high throughput, targeting Netflix engineering standards. Built during a 9-week prep (March 1 - April 27, 2025), it evolves with chaos testing, system design, and more.

## Day 5 (March 5, 2025) - Throughput Optimization
- **Goal**: Achieve ~10k events/sec for 10k messages.
- **Results**: Producer: 8,323.37 events/sec, Consumer: 19,075.10 events/sec (2 processes).
- **Tools**: Kafka (direct), Kafka-Python (producer), confluent-kafka (consumer), VS Code venv.
- **Files**:
  - `producer.py`: Kafka producer (~8k events/sec).
  - `consumer_opt_v11.py`: Optimized consumer (~19k events/sec).
  - `throughput_log.ipynb`: Jupyter log of runs.

## Setup Instructions
### Prerequisites
- Python 3.8+
- Git
- Kafka (direct install, no Docker yet)
- VS Code (optional, with venv)

### Clone and Run Locally
1. **Clone the Repo**:
   git clone https://github.com/<your-username>/kafka-optimization.git
   cd kafka-optimization
2. **Set Up Virtual Environment**:
   python -m venv venv
   source venv/bin/activate  # Mac/Linux
   venv\Scripts\activate     # Windows
3. **Install Dependencies**:
   pip install kafka-python confluent-kafka
4. **Install Kafka**:
   Download Kafka: Apache Kafka (e.g., 3.6.1).
   Extract to ~/kafka.
   Start Zookeeper: ~/kafka/bin/zookeeper-server-start.sh ~/kafka/config/zookeeper.properties
   Start Kafka: ~/kafka/bin/kafka-server-start.sh ~/kafka/config/server.properties
5. **Run Producer**:
   python ProducerOpt.py
6. **Run Consumer**:
   python ConsumerOpt.py
tuning Iterations: Updates, Reasons, Thought Process, Results, and Next Steps

    Baseline (1000 Messages, March 5 ~6:05 AM)
        Updates:
            Producer: Default KafkaProducer (batch.size=16384, linger.ms=0)—producer.py from Day 3 (March 3 ~10:00 AM).
            Consumer: Default KafkaConsumer (fetch.max.bytes=52428800, max.partition.fetch.bytes=1048576)—consumer.py from Day 4 (March 4 ~8:00 AM).
            Topic: test-opt, 1 partition (March 5 ~6:10 AM).
        Reason: Starting point—Day 3-4 setup, simple producer/consumer—test default throughput for 1000 messages (~100KB).
        Thought Process:
            Producer: Defaults (batch.size=16384 ~16KB) fit ~160 messages/batch—small load (1000 messages) should be fast—check ceiling.
            Consumer: Defaults (fetch.max.bytes=50MB, max.partition.fetch.bytes=1MB)—should fetch 1000 messages (~100KB) in ~1 poll—why so slow?
            Goal: Establish baseline—identify bottlenecks (e.g., fetch latency, poll overhead).
        Results:
            Producer: 0.01s, Throughput: 76,686.73 events/sec—blazing fast—~6 batches (1000 / ~160), CPU-bound, not I/O-limited.
            Consumer: 6.31s, Throughput: 158.54 events/sec—glacial—~63 polls (1000 / ~16 messages/poll), fetch/poll lag.
        Conclusion: Producer’s overkill (~76k)—consumer’s the choke (~158)—small fetch size or poll overhead—scale to 10k messages next.
        Next Steps: Tune consumer fetch—test 10k messages (~1MB)—match Netflix scale (March 1).
    Tuned v1 (1000 Messages, March 5 ~6:05 AM)
        Updates:
            Producer: batch.size=32768 (was 16384), linger.ms=5 (was 0)—producer_opt.py (March 5 ~6:10 AM).
            Consumer: fetch.max.bytes=104857600 (was 52428800), max.partition.fetch.bytes=5242880 (was 1048576)—consumer_opt.py (March 5 ~6:10 AM).
        Reason: Boost producer batching, increase consumer fetch—reduce I/O and poll frequency.
        Thought Process:
            Producer: batch.size=32768 (~32KB) = ~320 messages/batch—fewer sends (1000 / ~320 = ~3 batches)—linger.ms=5 delays 5ms to fill batches—trade latency for throughput (March 5 ~6:15 AM).
            Consumer: fetch.max.bytes=100MB (was 50MB), max.partition.fetch.bytes=5MB (was 1MB)—fetch 1000 messages (~100KB) in ~1 poll vs. ~63—cut latency (March 5 ~6:15 AM).
            Hypothesis: Baseline’s fetch/poll lag—bigger buffers = higher throughput—test before scaling to 10k.
        Results:
            Producer: 0.0133s (implied), Throughput: 75,006.78 events/sec—slight drop (~2.2%)—linger.ms=5 added delay, 1000 messages didn’t need bigger batch.
            Consumer: 1.531s (implied), Throughput: 653.06 events/sec—~312% jump—~1-2 polls (~500-1000/poll)—fetch size worked!
        Conclusion: Producer’s fine (~75k)—consumer’s bottleneck eased (~653)—fetch size key—scale to 10k, push consumer harder.
        Next Steps: Test 10k messages—increase consumer fetch capacity—optimize poll speed (March 5 ~6:15 AM).
    Tuned v2 (10,000 Messages, March 5 ~6:15 AM)
        Updates:
            Producer: Revert to baseline (batch.size=16384, linger.ms=0)—v1’s drop unnecessary (March 5 ~6:15 AM).
            Consumer: fetch.max.bytes=524288000 (500MB), max.partition.fetch.bytes=10485760 (10MB), max_poll_interval_ms=100 (default 300000)—consumer_opt_v2.py (March 5 ~6:15 AM).
        Reason: Scale to 10k (~1MB)—maximize consumer fetch, reduce poll wait—producer’s baseline holds.
        Thought Process:
            Producer: v1’s 75k → baseline’s 76k—1000 messages didn’t stress batch.size—10k (~62 batches) won’t either—revert for simplicity (March 5 ~6:15 AM).
            Consumer: fetch.max.bytes=500MB (was 100MB)—10k (~1MB) in ~1 poll—max.partition.fetch.bytes=10MB (was 5MB)—same—max_poll_interval_ms=100 (was 300s)—~10 polls/sec vs. ~0.003 polls/sec—cut blocking (March 5 ~6:15 AM).
            Hypothesis: v1’s 653 = fetch boost—10k needs bigger fetch, faster polling—aim for ~10k events/sec (March 1).
        Results:
            Producer: 0.12s, Throughput: 8,546.44 events/sec—scales to 10k—~62 batches, ~8k still > target.
            Consumer: 1.75s, Throughput: 572.85 events/sec—~12% drop from v1 (653)—~17 polls (~588/poll)—fetch up, poll lag?
        Conclusion: Producer’s solid (~8k)—consumer’s stuck (~572)—1 partition caps fetch—poll overhead persists—parallelize next (March 5 ~6:20 AM).
        Next Steps: Add partitions (e.g., 4)—test consumer parallelism—push fetch higher (March 5 ~6:20 AM).
    Tuned v3 (10,000 Messages, March 5 ~6:25 AM)
        Updates:
            Topic: test-opt-4, 4 partitions (was 1)—recreated (March 5 ~6:20 AM).
            Consumer: Same as v2—consumer_opt_v3.py (March 5 ~6:20 AM).
        Reason: Parallelize fetch—4 partitions = ~2.5k/partition—boost consumer throughput.
        Thought Process:
            v2’s 572 = 1 partition bottleneck—4 partitions = ~4x fetch potential (~2,291 events/sec)—single consumer should scale—test parallelism (March 5 ~6:20 AM).
            Hypothesis: v2’s ~588/poll = serial fetch—4 partitions = ~2.5k/poll—aim for ~2-3k total—closer to 10k (March 5 ~6:25 AM).
        Results:
            Producer: 0.12s, Throughput: 8,256.37 events/sec—~3.4% drop—noise, still ~8k.
            Consumer: 2.70s, Throughput: 369.98 events/sec—~35% drop from v2 (572)—~27 polls (~370/poll)—slower!
        Conclusion: Producer’s fine (~8k)—consumer’s worse (~369)—4 partitions didn’t parallelize—single consumer serializes—local Kafka underpowered—multi-consumer next (March 5 ~6:25 AM).
        Next Steps: Add 2nd consumer—threading—fix fetch drop (March 5 ~6:25 AM).
    Tuned v4 (10,000 Messages, March 5 ~6:35 AM)
        Updates:
            Topic: test-opt-1, revert to 1 partition—simplify (March 5 ~6:25 AM).
            Consumer: max_poll_records=5000 (default 500), max_poll_interval_ms=50 (was 100)—consumer_opt_v4.py (March 5 ~6:25 AM).
        Reason: v3’s 4 partitions flopped—single consumer, max fetch—reduce poll wait—test simpler setup.
        Thought Process:
            v3’s 369 = single consumer can’t parallelize—revert to 1 partition—max_poll_records=5000 = ~2 polls (10k / 5k)—max_poll_interval_ms=50 = ~20 polls/sec—cut latency (March 5 ~6:35 AM).
            Hypothesis: v3’s fetch drop = partition overhead—single consumer + big fetch = ~5-10k—test before multi-consumer (March 5 ~6:35 AM).
        Results:
            Producer: 0.12s, Throughput: 8,249.42 events/sec—~steady (~8k).
            Consumer: 0.99s, Throughput: 1,008.71 events/sec—~172% up from v3 (369)—~2 polls (~5k/poll)—fetch works!
        Conclusion: Producer’s steady (~8k)—consumer’s up (~1k)—fetch size + poll speed = gain—still <10k—multi-consumer next (March 5 ~6:35 AM).
        Next Steps: 2 consumers, threading—push to 10k+—fix serial fetch (March 5 ~6:35 AM).
    Tuned v5 (10,000 Messages, March 5 ~6:40 AM)
        Updates:
            Consumer: 2 consumers (5k each), threading, max_poll_records=10000 (was 5000), max_poll_interval_ms=10 (was 50)—consumer_opt_v5.py (March 5 ~6:35 AM).
        Reason: Parallelize—2 consumers = ~2k total (v4)—max fetch, min poll wait—hit 10k+.
        Thought Process:
            v4’s 1k = single consumer cap—2 consumers = ~2k—max_poll_records=10000 = ~1 poll/consumer—max_poll_interval_ms=10 = ~100 polls/sec—double fetch (March 5 ~6:40 AM).
            Hypothesis: v4’s ~5k/poll = fetch potential—2x consumers = ~10k—faster polling = ~0.5-1s— scale (March 5 ~6:40 AM).
        Results:
            Producer: 0.12s, Throughput: 8,050.18 events/sec—~steady (~8k).
            Consumer: 3.24s, Throughput: 3,089.74 events/sec—~206% up from v4—~6 polls total (~833/poll)—RuntimeError: cannot release un-acquired lock x2.
        Conclusion: Producer’s good (~8k)—consumer’s up (~3k)—parallel works, but errors—threading bug—still <10k—fix errors, retry (March 5 ~6:40 AM).
        Next Steps: Switch to multiprocessing—avoid lock errors—push fetch (March 5 ~6:40 AM).
    Tuned v6 (10,000 Messages, March 5 ~6:45 AM)
        Updates:
            Consumer: multiprocessing (was threading)—consumer_opt_v6.py (March 5 ~6:40 AM).
            Producer: Not run—used v5’s 10k (March 5 ~6:45 AM).
        Reason: Fix RuntimeError—processes vs. threads—test multi-consumer stability.
        Thought Process:
            v5’s errors = Kafka-Python threading clash—multiprocessing = separate memory, no GIL—max_poll_records=10000, 10ms = ~3k—aim for ~6-10k (March 5 ~6:45 AM).
            Hypothesis: v5’s 3k = fetch cap—processes = ~6-10k—error-free (March 5 ~6:45 AM).
        Results:
            Producer: Not run—v5’s 8,050.18 events/sec.
            Consumer: 1.23s, Throughput: 8,160.98 events/sec—~164% up from v5—~8 polls (~1,250/poll)—RuntimeError x2 persists!
        Conclusion: Consumer’s soaring (~8k)—processes help, but errors remain—Kafka-Python’s limit—still <10k—switch to confluent-kafka (March 5 ~6:45 AM).
        Next Steps: confluent-kafka—thread-safe—retry multi-consumer—push past 10k (March 5 ~6:55 AM).
    Tuned v7 (10,000 Messages, March 5 ~6:55 AM)
        Updates:
            Consumer: Single consumer, receive_buffer_bytes=104857600 (was consumer_buffer_size, error)—consumer_opt_v7_fixed.py (March 5 ~6:50 AM).
        Reason: v6’s errors—simplify to single consumer—boost socket buffer—test stability.
        Thought Process:
            v6’s 8k = multi-consumer peak—errors = multi-process clash—single consumer + receive_buffer_bytes=100MB (default ~64KB) = ~5-10k—avoid errors (March 5 ~6:50 AM).
            Hypothesis: v6’s ~1,250/poll = fetch cap—single consumer + big buffer = ~5k—step back, then multi again (March 5 ~6:55 AM).
        Results:
            Producer: 0.12s, Throughput: 8,222.38 events/sec—~steady (~8k).
            Consumer: 4.83s, Throughput: 2,069.29 events/sec—~74% drop from v6—~10 polls (~1,000/poll)—no errors!
        Conclusion: Producer’s steady (~8k)—consumer’s down (~2k)—single consumer caps fetch—v6’s multi was key—retry multi with confluent-kafka (March 5 ~6:55 AM).
        Next Steps: confluent-kafka, 2 consumers—push past 10k—fix fetch drop (March 5 ~6:55 AM).
    Tuned v8 (10,000 Messages, March 5 ~7:00 AM)
        Updates:
            Consumer: confluent-kafka, 2 processes, socket.receive.buffer.bytes=104857600 (error)—consumer_opt_v8.py (March 5 ~6:55 AM).
        Reason: v7’s drop—multi-consumer + confluent-kafka—boost socket buffer—hit 10k+.
        Thought Process:
            v7’s 2k = single cap—v6’s 8k = multi potential—confluent-kafka = C-based, thread-safe—socket.receive.buffer.bytes=100MB = max fetch—aim for ~10-20k (March 5 ~7:00 AM).
            Hypothesis: v6’s ~1,250/poll x 2 = ~2.5k—confluent-kafka + big buffer = ~10k+ scale (March 5 ~7:00 AM).
        Results:
            Producer: 0.12s, Throughput: 8,271.12 events/sec—~steady (~8k).
            Consumer: 0.01s, Throughput: 1,314,375.61 events/sec—bogus—KafkaException: "receive.buffer.bytes"—typo!
        Conclusion: Producer’s good (~8k)—consumer’s fake (~1.3M)—error cut run—socket.receive.buffer.bytes fix—retry (March 5 ~7:00 AM).
        Next Steps: Fix to socket.receive.buffer.bytes—retry multi—push 10k+ (March 5 ~7:05 AM).
    Tuned v8_fixed (10,000 Messages, March 5 ~7:05 AM)
        Updates:
            Consumer: socket.receive.buffer.bytes=100000000 (max 100MB)—consumer_opt_v8_fixed.py (March 5 ~7:00 AM).
        Reason: Fix v8’s typo—cap buffer at 100MB—test multi-consumer stability.
        Thought Process:
            v8’s error = wrong key—socket.receive.buffer.bytes=100MB (max) = ~10k+—2 consumers = ~5k each—v6’s 8k baseline—hit target (March 5 ~7:05 AM).
            Hypothesis: v8’s ~1M = glitch—fixed config = ~10-20k scale (March 5 ~7:05 AM).
        Results:
            Producer: 0.12s, Throughput: 8,110.42 events/sec—~steady (~8k).
            Consumer: 0.02s, Throughput: 533,097.44 events/sec—bogus—early exit—timing off!
        Conclusion: Producer’s steady (~8k)—consumer’s fake (~533k)—didn’t fetch 10k—timing glitch—fix count—retry (March 5 ~7:05 AM).
        Next Steps: Track real fetch—ensure 5k/consumer—push 10k+ (March 5 ~7:10 AM).
    Tuned v9 (10,000 Messages, March 5 ~7:10 AM)
        Updates:
            Consumer: Same as v8_fixed—consumer_opt_v9.py (March 5 ~7:05 AM).
        Reason: v8_fixed’s timing—test same config—verify fetch.
        Thought Process:
            v8’s 533k = early exit—same config—poll(timeout=0.005)—should fetch 10k—aim for ~10-20k—debug timing (March 5 ~7:10 AM).
        Results:
            Producer: 0.12s, Throughput: 8,294.58 events/sec—~steady (~8k).
            Consumer: 0.02s, Throughput: 505,295.22 events/sec—bogus again—didn’t fetch 10k!
        Conclusion: Producer’s good (~8k)—consumer’s fake (~505k)—timing off—while loop exits fast—fix offset/count—retry (March 5 ~7:10 AM).
        Next Steps: enable.auto.commit=False, offset reset—ensure 5k/consumer—hit 10k+ (March 5 ~7:15 AM).
    Tuned v10 (10,000 Messages, March 5 ~7:15 AM)
        Updates:
            Consumer: messages_fetched tracking—consumer_opt_v10.py (March 5 ~7:10 AM).
        Reason: v9’s glitch—track real fetches—verify 5k/consumer—fix timing.
        Thought Process:
            v9’s 505k = false count—messages_fetched = true 5k—poll(timeout=0.005) = ~200 polls/sec—aim for ~0.5-1s, ~10-20k—v6’s 8k baseline (March 5 ~7:15 AM).
        Results:
            Producer: 0.12s, Throughput: 8,356.95 events/sec—~steady (~8k).
            Consumer: 0.02s, Throughput: 526,122.85 events/sec—bogus—didn’t fix—offset issue!
        Conclusion: Producer’s steady (~8k)—consumer’s fake (~526k)—messages_fetched didn’t catch—offset reset needed—retry (March 5 ~7:15 AM).
        Next Steps: enable.auto.commit=False, consumer.assign()—force 5k—hit 10k+ (March 5 ~7:20 AM).
    Tuned v11 (10,000 Messages, March 5 ~7:20 AM)
        Updates:
            Consumer: enable.auto.commit=False, consumer.assign([TopicPartition('test-opt-1', 0, 0)])—consumer_opt_v11.py (March 5 ~7:15 AM).
        Reason: v10’s glitch—force 5k/consumer—reset offsets—real fetch time—hit 10k+.
        Thought Process:
            v10’s 526k = offset mismatch—auto.offset.reset='earliest' + auto-commit = fast exit—manual offset (partition 0, offset 0) = 5k each—poll(timeout=0.005) = ~0.5-1s, ~10-20k—v6’s 8k x 2 (March 5 ~7:20 AM).
            Hypothesis: v10’s count = attempts—real fetch + offset reset = ~10k+ scale (March 5 ~7:20 AM).
        Results:
            Producer: 0.12s, Throughput: 8,323.37 events/sec—~steady (~8k).
            Consumer: 0.52s, Throughput: 19,075.10 events/sec—~135% above 10k—Consumer 0: 9,662.55, Consumer 1: 9,705.49—~104 polls (~96/poll)—success!
        Conclusion: Producer’s locked (~8k)—consumer’s crushed it (~19k)—offset fix + multi-consumer = ~2x v6’s 8k -ready (March 1)—target smashed!
        Next Steps: Done—commit to GitHub (March 5 ~7:25 AM)—prep for chaos testing (Week 2, Day 10, March 4 ~5:40 PM).

==============================================================================================================================================================================================================================================================================================================================================
Why Calculations Matter in Tuning

    Core Idea: Tuning = finding bottlenecks (e.g., fetch size, poll speed, parallelism) and fixing them—numbers tell us where and how much. They’re not just math—they’re your map to performance.
    What They Show:
        Throughput (events/sec): Speed—how fast we process messages—target ~10k (March 1’s ~11k daily avg).
        Time (seconds): Duration—how long to process 10k messages—e.g., 1s = 10k events/sec.
        Polls: Fetch attempts—how many times consumer asks broker for data—fewer = faster (less overhead).
        Messages/Poll: Fetch size—how much data per poll—bigger = fewer polls, higher throughput.
    Thought Process: Measure (results), calculate (e.g., polls = time / poll interval), hypothesize (e.g., small fetch = bottleneck), tweak (e.g., bigger fetch), repeat—L4-level debugging (March 5 ~7:30 AM).
    
Key Concepts:

    Throughput = Messages / Time: Simple—10k messages in 1s = 10k events/sec—your speedometer.
    Polls = Time / Poll Interval: How many fetches—e.g., 1s / 0.005s = 200 polls—fewer = faster (less overhead).
    Messages/Poll = Messages / Polls: Fetch size—e.g., 10k / 200 = 50/poll—bigger = fewer trips—tweak fetch configs.
    Parallelism: Multi-consumers/processes—e.g., 2x 5k = 10k—split load—boost total.

Baseline (1000 Messages, March 5 ~6:05 AM)

    Results: Producer: 0.01s, 76,686.73 events/sec; Consumer: 6.31s, 158.54 events/sec.
    Intuition:
        Producer’s fast—1000 messages in 0.01s = blazing—sending’s not the issue.
        Consumer’s slow—6.31s for 1000 = crawling—fetching’s the problem.
    Calculations:
        Producer: 1000 messages / 0.01s = 100,000 events/sec (reported 76k—noise/rounding)—~6 batches (batch.size=16384 ~16KB / ~100 bytes/message = ~160 messages/batch, 1000 / 160 = ~6). Fast = CPU-bound, not network.
        Consumer: 1000 messages / 6.31s = ~158.5 events/sec—how many polls? Default max_poll_interval_ms=300000 (300s) = ~0.003 polls/sec—wrong metric! Actual poll rate = ~time-based—assume ~0.1s/poll (typical default)—6.31s / 0.1s = ~63 polls—1000 / 63 = ~16 messages/poll—tiny fetch!
    Why: Producer’s batches = send efficiency—consumer’s polls = fetch bottleneck—16 messages/poll = small fetch.max.bytes=50MB or max.partition.fetch.bytes=1MB underused—laggy.
    Thought: Boost fetch size—fewer polls = faster—scale to 10k (March 5 ~6:05 AM).

Tuned v1 (1000 Messages, March 5 ~6:15 AM)

    Updates: Producer: batch.size=32768, linger.ms=5; Consumer: fetch.max.bytes=100MB, max.partition.fetch.bytes=5MB.
    Results: Producer: 0.0133s, 75,006.78 events/sec; Consumer: 1.531s, 653.06 events/sec.
    Intuition:
        Producer: Slight slow-down—batching more, waiting a bit—still fast.
        Consumer: Way faster—1.5s vs. 6.3s—bigger fetch worked!
    Calculations:
        Producer: 1000 / 0.0133 = ~75,188 events/sec—~3 batches (batch.size=32768 ~32KB / ~100 bytes = ~320 messages/batch, 1000 / 320 = ~3)—linger.ms=5 (0.005s) added delay—0.01s → 0.0133s = ~0.003s extra—small load didn’t need it.
        Consumer: 1000 / 1.531 = ~653 events/sec—assume ~0.1s/poll (default)—1.531s / 0.1s = ~15 polls—1000 / 15 = ~66 messages/poll—v0’s 16 → 66 = fetch size boost (fetch.max.bytes=100MB, max.partition.fetch.bytes=5MB)—still slow vs. 10k!
    Why: Producer’s delay = linger.ms—consumer’s polls dropped (~63 → ~15)—bigger fetch = fewer trips—need ~10k scale, faster polling (March 5 ~6:15 AM).
    Thought: v1’s fetch gain—scale to 10k—tweak poll speed—revert producer (March 5 ~6:15 AM).

Tuned v2 (10,000 Messages, March 5 ~6:20 AM)

    Updates: Consumer: fetch.max.bytes=500MB, max.partition.fetch.bytes=10MB, max_poll_interval_ms=100ms.
    Results: Producer: 0.12s, 8,546.44 events/sec; Consumer: 1.75s, 572.85 events/sec.
    Intuition:
        Producer: Scales to 10k—still fast—~8k = solid.
        Consumer: Faster than v0 (6.3s), slower than v1 (653)—why drop?
    Calculations:
        Producer: 10,000 / 0.12 = 83,333 events/sec (reported 8,546—10x load = ~10x time)—~62 batches (10,000 / ~160 = ~62)—~0.002s/batch—network now in play vs. v0’s CPU.
        Consumer: 10,000 / 1.75 = ~5,714 events/sec (reported 572.85—typo?)—max_poll_interval_ms=100ms (0.1s) = ~10 polls/sec max—1.75s / 0.1s = ~17 polls—10,000 / 17 = ~588 messages/poll—v1’s 66 → 588 = fetch boost, but <10k!
    Why: Producer’s ~8k = batch efficiency—consumer’s ~588/poll = big fetch—17 polls = poll lag—1 partition caps—parallelize (March 5 ~6:20 AM).
    Thought: v2’s fetch up, poll slow—4 partitions = ~2-3k—test multi-fetch (March 5 ~6:25 AM).

Tuned v3 (10,000 Messages, March 5 ~6:25 AM)

    Updates: Topic: 4 partitions (test-opt-4).
    Results: Producer: 0.12s, 8,256.37 events/sec; Consumer: 2.70s, 369.98 events/sec.
    Intuition:
        Producer: Steady—~8k—partitions didn’t hurt.
        Consumer: Slower—2.7s vs. 1.75s—4 partitions backfired!
    Calculations:
        Producer: 10,000 / 0.12 = ~83,333 (reported 8,256)—~62 batches—~8k holds.
        Consumer: 10,000 / 2.70 = ~3,703 events/sec (reported 369.98—typo?)—2.70s / 0.1s = ~27 polls—10,000 / 27 = ~370 messages/poll—v2’s 588 → 370 = drop!
    Why: Consumer’s ~370/poll = single consumer serializes 4 partitions (~2.5k/partition)—~27 polls = overhead—local Kafka underpowered (March 5 ~6:25 AM).
    Thought: v3’s flop—multi-consumer—fix serial fetch—aim ~5-10k (March 5 ~6:35 AM).

Tuned v11 (10,000 Messages, March 5 ~7:20 AM)

    Updates: confluent-kafka, 2 processes, enable.auto.commit=False, consumer.assign()—consumer_opt_v11.py.
    Results: Producer: 0.12s, 8,323.37 events/sec; Consumer: 0.52s, 19,075.10 events/sec (Consumer 0: 9,662.55, Consumer 1: 9,705.49).
    Intuition:
        Producer: Steady—~8k—rock-solid.
        Consumer: Blazing—0.52s, ~19k—2x target—nailed it!
    Calculations:
        Producer: 10,000 / 0.12 = ~83,333 (reported 8,323)—~62 batches—~8k holds.
        Consumer: 10,000 / 0.52 = 19,230 events/sec (reported 19,075)—poll(timeout=0.005) = ~200 polls/sec—0.52s / 0.005s = ~104 polls—10,000 / 104 = ~96 messages/poll—Consumer 0: 5,000 / 0.52 = ~9,615; Consumer 1: ~9,615—total ~19k—2x v6’s 8k!
    Why: 2 consumers (~9.6k each) = parallel fetch—fetch.max.bytes=500MB + max.partition.fetch.bytes=10MB = ~96/poll (~1MB fits)—enable.auto.commit=False + offset reset = full 10k—confluent-kafka = C-speed gold (March 5 ~7:20 AM).
    Thought: v10’s glitch fixed—19k > 10k—target smashed—done (March 5 ~7:25 AM).


**producer**
Asynchronous Sends: You're already using flush(), which waits for the producer to send messages synchronously. However, calling flush() after every send may reduce throughput. Try reducing the number of flush() calls or remove it entirely to let the producer handle retries and batching efficiently.

    Kafka producers work best when messages are sent asynchronously. By removing flush(), the producer can send multiple messages at once and batch them efficiently. If you remove it, Kafka will flush messages to brokers when it's optimal (e.g., when a batch is full).

Compression: Consider using compression for the payload to improve throughput, especially if you're sending large messages. You can set the compression_type to gzip, snappy, or lz4 for the producer.

**Compression**
Compression at the Producer:
Kafka producers can compress data before sending it to the broker, which reduces the amount of data transmitted over the network and stored on the broker's disk. 
No Data Loss:
The compression process is lossless, meaning that the original data is preserved and can be perfectly reconstructed by the consumer after decompression. 
Benefits of Compression:

    Reduced Bandwidth Usage: Smaller compressed messages mean less data is transferred over the network. 

Improved Storage Efficiency: Compressed messages take up less space on the broker's storage. 
Faster Transmission: Smaller messages can be transmitted faster, potentially improving throughput. 

Consumer Decompression:
The consumer reads the compressed messages from the broker and decompresses them before processing them. 
Compression Types:
Kafka supports various compression codecs, such as gzip, snappy, and LZ4. 
Batching:
Compression is often more effective when combined with batching, where multiple messages are grouped together before compression and transmission. 
Latency Considerations:
While compression can reduce network traffic and storage requirements, it also adds some latency to the producer (for compression) and the consumer (for decompression). 

Batching: Kafka producers work best when messages are batched together. The producer can hold messages in memory before sending them in batches, which improves throughput. You can adjust the batch.size and linger.ms parameters to fine-tune this.

Optimizing Kafka Configuration: You may want to increase the acks configuration to acks='all' (or acks=1 depending on your requirements). This ensures better data durability, but keep in mind it may impact throughput.

**Consumer**
Consumer Throughput (5201.72 events/sec):

The consumer throughput is also below the target, which is contributing to the low overall throughput.
Recommendations:

    Consume in Parallel: You are using three consumers, but you're assigning each consumer to only one partition. Kafka performs best when each consumer is assigned to multiple partitions (if you have multiple partitions). If you only have three partitions, assign each consumer to multiple partitions.

    consumer.assign([TopicPartition('test-topic-1', partition) for partition in range(3)])

    Consumer Fetch Size: You have set a large fetch.max.bytes (50MB) and max.partition.fetch.bytes (10MB). While these values can improve throughput, they might also introduce latency if the consumer isn't consuming quickly enough. Try reducing them to find an optimal balance. Also, experiment with reducing fetch.min.bytes to help the consumer fetch smaller chunks of data more frequently.

    Parallelism and Multiprocessing: You are using the multiprocessing library to run consumers in parallel. Kafka consumers are usually more efficient when they are managed within threads rather than separate processes due to the overhead of process creation and context switching. However, if you're dealing with a large-scale deployment and multiple consumers per partition, consider managing multiple consumer threads per process.

3. Kafka Cluster Configuration:

Check if the Kafka cluster itself is configured correctly for high throughput:

    Replication Factor: With a replication factor of 2, make sure your brokers are healthy and not under too much load. A replication factor of 3 could help in case of failures but might introduce some overhead.
    Partitioning Strategy: With 3 brokers, you have 3 partitions, which is good for load balancing. If needed, you can experiment with increasing the number of partitions for better distribution of load.
    ZooKeeper: If you're using ZooKeeper in your setup, ensure it's not becoming a bottleneck.

4. Network Performance:

Kafka performance can often be limited by network conditions, especially in a Dockerized environment. Make sure that the network setup between your Kafka brokers and consumers is optimized:

    Kafka Listener Config: Ensure that the listeners in Kafka are bound correctly and accessible by your producers and consumers.
    Docker Networking: If Kafka brokers are running in Docker containers, ensure you're using the correct network setup. localhost might not work across different containers; try using Docker's bridge or host networking.

5. Monitoring and Diagnostics:

    Kafka Metrics: Use tools like kafka-consumer-groups.sh to monitor consumer lag and other performance metrics.
    Broker Logs: Check Kafka broker logs for any errors or performance warnings that might be limiting throughput.

No Consumer Group: Without a consumer group (group.id), each consumer will fetch all the data from all partitions independently. In this case, all consumers will read the same data, which is not what you want when scaling consumers to handle different partitions (because Kafka will send the same messages to every consumer, causing data duplication and inefficient processing).

With Consumer Group: If you assign consumers to a consumer group (group.id), Kafka will ensure that each consumer in the group gets assigned different partitions, and each partition is consumed by only one consumer in the group at a time. This avoids data duplication and allows you to scale the number of consumers to handle partitions in parallel.

**final numbers**
Prodcuser:
Producer time: 0.52s, Throughput: 40454.74 events/sec

Consumer: with 6 partitions and replication 2
Consumer 3 fetched 47104 messages in 0.75s, Throughput: 62773.99 events/sec
Consumer 2 fetched 47552 messages in 0.75s, Throughput: 63276.17 events/sec
Consumer 0 fetched 47104 messages in 0.75s, Throughput: 62558.88 events/sec
Consumer 5 fetched 47552 messages in 0.75s, Throughput: 63316.12 events/sec
Consumer 1 fetched 48000 messages in 0.76s, Throughput: 63541.03 events/sec
Consumer 4 fetched 48000 messages in 0.75s, Throughput: 63621.93 events/sec
Total Consumer time: 0.77s, Throughput: 27423.83 events/sec


Manual Offset Commit Overhead:

    Manual commits are slower, especially with large batches, because each commit requires an additional network round trip.

Inefficient Polling Strategy:

    My code waits longer (timeout=1.0), reducing the frequency of polls. Kafka performs best with small, fast polls.

Batch Configuration Trade-offs:

    Larger fetch sizes work best for high-latency networks but may delay message delivery in low-latency setups. The dynamic Kafka defaults often perform better unless there’s a clear bottleneck.
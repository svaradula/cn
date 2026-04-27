from datetime import datetime, timedelta, timezone
from pathlib import Path

# =========================
# CONFIG
# =========================
TIMEZONE = "Asia/Kolkata"

# Study schedule
START_DATE = datetime(2026, 4, 24, 4, 0, 0)   # April 24, 2026, 4:00 AM
END_DATE   = datetime(2026, 10, 30, 6, 0, 0)  # 6 months inclusive
SESSION_HOURS = 2 

# Output settings
OUTPUT_DIR = Path("generated_calendars")
OUTPUT_FILE = OUTPUT_DIR / "dsa_system_design_6_month_plan.ics"

# Reminder settings
ENABLE_REMINDERS = True
REMINDER_MINUTES_BEFORE = 30   # popup reminder 30 mins before session

# =========================
# TOPICS
# =========================
week_topics = [
    # Month 1 — DSA foundations
    [
        "Orientation + how to study DSA & System Design effectively",
        "Big-O notation: time and space complexity",
        "Recursion basics + tracing recursive calls",
        "Arrays: basics, traversal, insertion, deletion",
        "Strings: fundamentals and common operations",
        "Hashing basics: hash maps and hash sets",
        "Practice day: arrays, strings, hashing basics",
    ],
    [
        "Two pointers technique",
        "Sliding window technique",
        "Prefix sums and difference arrays",
        "Binary search basics",
        "Binary search on answers",
        "Sorting fundamentals + stability + common algorithms",
        "Practice day: search, sorting, windows, pointers",
    ],
    [
        "Linked lists: singly linked list basics",
        "Linked lists: reversal, middle, cycle detection",
        "Stacks: fundamentals and use cases",
        "Queues and deque fundamentals",
        "Monotonic stack and monotonic queue",
        "Expression evaluation and balanced parentheses",
        "Practice day: linked list, stack, queue problems",
    ],
    [
        "Trees: terminology, traversals, recursion on trees",
        "Binary Search Trees: insert, search, delete",
        "Heaps / priority queues",
        "Trie basics and string lookup applications",
        "Tree patterns: depth, height, diameter, LCA",
        "Practice problems on trees and heaps",
        "Revision + Month 1 checkpoint",
    ],

    # Month 2 — Core DSA
    [
        "Graphs: representation, BFS, DFS",
        "Topological sort and DAG concepts",
        "Shortest path: Dijkstra basics",
        "Union Find / Disjoint Set Union",
        "Minimum spanning tree intuition",
        "Graph problem patterns",
        "Practice day: BFS/DFS/toposort/DSU",
    ],
    [
        "Dynamic Programming mindset and state design",
        "DP on 1D sequences",
        "DP on 2D grids",
        "Knapsack pattern and subset DP",
        "Longest Increasing Subsequence and sequence DP",
        "Backtracking: subsets, permutations, combinations",
        "Practice day: DP + backtracking",
    ],
    [
        "Greedy algorithms: when greedy works",
        "Intervals: merge, overlap, scheduling",
        "Bit manipulation fundamentals",
        "Math for coding interviews: gcd, primes, modular basics",
        "Advanced review: choosing the right data structure",
        "Mock coding interview 1",
        "DSA revision checkpoint + weak area analysis",
    ],
    [
        "Advanced trees: segment tree basics",
        "Fenwick tree / Binary Indexed Tree basics",
        "Advanced graph ideas: bipartite graphs",
        "Advanced graph ideas: Floyd Warshall intuition",
        "String algorithms: KMP intuition",
        "String algorithms: rolling hash basics",
        "Practice day: advanced DSA mixed set",
    ],

    # Month 3 — Deeper DSA + interview patterns
    [
        "Advanced DP: state transition practice",
        "Advanced DP: memoization vs tabulation",
        "DP on strings",
        "DP on trees intuition",
        "Graph shortest paths: Bellman-Ford intuition",
        "Strong interview patterns review",
        "Mixed DSA timed practice",
    ],
    [
        "Binary search patterns masterclass",
        "Monotonic data structure problems",
        "Heap-based interview patterns",
        "Trie + prefix-based problems",
        "Greedy proof intuition",
        "Mock coding interview 2",
        "Revision + problem log cleanup",
    ],
    [
        "Systematic debugging for coding rounds",
        "Communicating thought process in interviews",
        "Writing clean interview code",
        "Brute force to optimized transitions",
        "Recognizing hidden patterns in problems",
        "Mixed medium-level coding set",
        "Weekly assessment",
    ],
    [
        "Timed contest-style practice 1",
        "Timed contest-style practice 2",
        "Timed contest-style practice 3",
        "Weak area repair: DP",
        "Weak area repair: graphs",
        "Weak area repair: trees",
        "Month 3 revision checkpoint",
    ],

    # Month 4 — System Design foundations
    [
        "System Design foundations: what system design is",
        "Functional vs non-functional requirements",
        "Scalability, reliability, availability, maintainability",
        "Latency, throughput, CAP, consistency models",
        "Load balancing and reverse proxies",
        "Caching fundamentals and cache patterns",
        "Design exercise: URL shortener part 1",
    ],
    [
        "Databases: SQL vs NoSQL",
        "Indexing, partitioning, sharding basics",
        "Replication and consistency tradeoffs",
        "Messaging queues and event-driven architecture",
        "API design fundamentals and idempotency",
        "Rate limiting and throttling",
        "Design exercise: URL shortener part 2",
    ],
    [
        "Storage systems, blobs, CDN basics",
        "Authentication, authorization, sessions, tokens",
        "Observability: logging, metrics, tracing",
        "Fault tolerance, retries, timeouts, circuit breakers",
        "Microservices vs monoliths",
        "Design exercise: chat system part 1",
        "Revision + system design foundations checkpoint",
    ],
    [
        "Designing a chat system part 2",
        "Notification system design",
        "Feed / timeline system design basics",
        "Search system design fundamentals",
        "File storage / Dropbox-like system basics",
        "Practice: estimate scale and bottlenecks",
        "Mock system design interview 1",
    ],

    # Month 5 — Applied system design
    [
        "Designing an e-commerce backend",
        "Payment workflow basics and failure handling",
        "Booking / reservation system design",
        "Designing for multi-region deployment",
        "Data modeling and schema evolution",
        "Practice: tradeoff articulation and bottleneck fixes",
        "Mock system design interview 2",
    ],
    [
        "Advanced caching: eviction, invalidation, hot keys",
        "Advanced databases: read replicas and failover",
        "Distributed transactions and saga intuition",
        "ID generation strategies at scale",
        "Message ordering, deduplication, exactly-once myths",
        "Design deep dive: real-time notifications",
        "Practice day: distributed systems patterns",
    ],
    [
        "Low-level estimation: QPS, storage, bandwidth",
        "High-level architecture storytelling",
        "How to answer system design interview questions",
        "Common tradeoffs: consistency vs availability",
        "Common tradeoffs: latency vs cost",
        "Design review: improve a weak architecture",
        "Mock system design interview 3",
    ],
    [
        "Case study: social media feed",
        "Case study: ride-sharing system",
        "Case study: video streaming system",
        "Case study: file sync service",
        "Case study: notification fanout",
        "Mixed design round",
        "Month 5 revision checkpoint",
    ],

    # Month 6 — Mastery, mocks, capstone
    [
        "DSA mixed mock interview 3",
        "DSA mixed mock interview 4",
        "System design + coding combined round",
        "Behavioral storytelling for technical interviews",
        "Debugging and communicating under pressure",
        "Revision day: top 20 DSA patterns",
        "Revision day: top 20 system design patterns",
    ],
    [
        "Capstone design: scalable social app part 1",
        "Capstone design: scalable social app part 2",
        "Capstone design: scalable social app part 3",
        "Capstone design: architecture review and tradeoffs",
        "Capstone coding drill: arrays + hashing",
        "Capstone coding drill: trees + graphs",
        "Weekly assessment + reflection",
    ],
    [
        "Targeted weak area repair: dynamic programming",
        "Targeted weak area repair: graphs",
        "Targeted weak area repair: system design fundamentals",
        "Targeted weak area repair: databases and caching",
        "Targeted weak area repair: communication and clarity",
        "Mock coding interview 5",
        "Mock system design interview 4",
    ],
    [
        "LeetCode-style interview set 1",
        "LeetCode-style interview set 2",
        "LeetCode-style interview set 3",
        "Design a notification system from scratch",
        "Design a booking system from scratch",
        "Compare two architectures and justify one",
        "Weekly assessment + revision",
    ],
    [
        "Final review: DSA patterns recap",
        "Final review: system design building blocks recap",
        "Mixed interview drills: coding + design",
        "Resume-style project discussion and storytelling",
        "Final self-assessment + next 6 months roadmap",
        "Buffer / catch-up / reflection day",
        "Celebration + long-term consistency plan",
    ],
]

# Flatten weeks into a daily list
topics = [topic for week in week_topics for topic in week]

# Fill remaining days, if needed
days = (END_DATE.date() - START_DATE.date()).days + 1
extra_cycle = [
    "Extra revision: arrays, strings, hashing, pointers",
    "Extra revision: linked lists, stacks, queues, heaps",
    "Extra revision: trees, BST, trie, recursion",
    "Extra revision: graphs, union find, shortest paths",
    "Extra revision: dynamic programming, greedy, backtracking",
    "Extra revision: system design case study practice",
    "Mock interview / catch-up / reflection day",
]

while len(topics) < days:
    topics.append(extra_cycle[len(topics) % 7])

topics = topics[:days]

# =========================
# HELPERS
# =========================
def escape_ics_text(text: str) -> str:
    """Escape special characters for ICS format."""
    return (
        text.replace("\\", "\\\\")
            .replace(";", r"\;")
            .replace(",", r"\,")
            .replace("\n", r"\n")
    )

def get_track_and_prefix(day_index: int) -> tuple[str, str]:
    """
    Return track name and title prefix by timeline.
    Adjust boundaries if you want different phase splits.
    """
    if day_index < 84:
        return "DSA Foundations and Mastery", "[DSA]"
    elif day_index < 140:
        return "System Design Foundations and Applied Design", "[System Design]"
    else:
        return "Interview Mastery / Revision", "[Mixed]"

def is_weekend(dt: datetime) -> bool:
    # Python weekday(): Monday=0 ... Sunday=6
    return dt.weekday() >= 5

# =========================
# BUILD CALENDAR
# =========================
lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//OpenAI//DSA-System-Design-6-Month-Plan//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:DSA and System Design 6-Month Study Plan",
    f"X-WR-TIMEZONE:{TIMEZONE}",
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

for i, topic in enumerate(topics):
    dtstart = START_DATE + timedelta(days=i)
    dtend = dtstart + timedelta(hours=SESSION_HOURS)

    track, prefix = get_track_and_prefix(i)

    weekend_tag = " [Weekend]" if is_weekend(dtstart) else ""
    summary = f"{prefix}{weekend_tag} {topic}"

    description = (
        f"Day {i + 1} of {days}\n"
        f"Track: {track}\n"
        f"Topic: {topic}\n"
        f"Weekend Session: {'Yes' if is_weekend(dtstart) else 'No'}\n"
        f"Study block: {SESSION_HOURS * 60} minutes\n"
        f"Suggested split: 35 min theory, 60 min guided practice, 25 min revision/notes."
    )

    uid = f"dsa-sd-6m-{i+1:03d}-{dtstart.strftime('%Y%m%d')}@openai.local"

    lines.extend([
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART;TZID={TIMEZONE}:{dtstart.strftime('%Y%m%dT%H%M%S')}",
        f"DTEND;TZID={TIMEZONE}:{dtend.strftime('%Y%m%dT%H%M%S')}",
        f"SUMMARY:{escape_ics_text(summary)}",
        f"DESCRIPTION:{escape_ics_text(description)}",
        "STATUS:CONFIRMED",
        "TRANSP:OPAQUE",
    ])

    if ENABLE_REMINDERS:
        lines.extend([
            "BEGIN:VALARM",
            f"TRIGGER:-PT{REMINDER_MINUTES_BEFORE}M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{escape_ics_text(f'Reminder: {summary}')}",
            "END:VALARM",
        ])

    lines.append("END:VEVENT")

lines.append("END:VCALENDAR")

# =========================
# SAVE FILE
# =========================
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")

print(f"Calendar created successfully: {OUTPUT_FILE.resolve()}")
print(f"Total sessions: {len(topics)}")
print(f"Date range: {START_DATE.date()} to {END_DATE.date()}")
print(f"Daily time: 5:00 PM to 7:00 PM")
print(f"Reminders enabled: {ENABLE_REMINDERS}")
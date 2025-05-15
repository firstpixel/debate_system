from app.performance_logger import PerformanceLogger
import time
import os

def test_perf_logger_roundtrip():
    logger = PerformanceLogger("test_perf")
    logger.log_turn("Agent1", 1.234)
    logger.log_turn("Agent2", 0.876)
    logger.log_turn("Agent1", 1.100)

    logger.save()
    path = "sessions/test_perf/performance_log.json"
    assert os.path.exists(path)

    import json
    with open(path) as f:
        data = json.load(f)

    print("Summary:", data["summary"])
    assert "Agent1" in data["summary"]["per_agent_avg_time"]

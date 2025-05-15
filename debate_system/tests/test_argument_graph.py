from app.argument_graph import ArgumentGraph
import json

def test_argument_graph_flow():
    g = ArgumentGraph()

    id1 = g.add_argument("TechAdvocate", "AI reduces traffic accidents.")
    id2 = g.add_argument("SafeGuard", "Sensors fail in bad weather.", reply_to=id1, relation="attacks")
    id3 = g.add_argument("TechAdvocate", "Edge cases can be handled with redundancy.", reply_to=id2, relation="qualifies")

    markdown = g.export_markdown()
    data = g.export_json()
    metrics = g.get_metrics()

    print("\nMarkdown:\n", markdown)
    print("\nMetrics:\n", metrics)
    assert "ARG001" in markdown and "ARG002" in markdown
    assert isinstance(data, dict)

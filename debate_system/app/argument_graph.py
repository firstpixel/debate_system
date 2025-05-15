# app/argument_graph.py

from textwrap import indent
import networkx as nx
from typing import Optional, Dict, List
import json
from networkx.readwrite import json_graph

class ArgumentGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.arg_count = 0

    def _generate_id(self) -> str:
        self.arg_count += 1
        return f"ARG{self.arg_count:03d}"

    def add_argument(self, agent: str, text: str, reply_to: Optional[str] = None, relation: str = "supports") -> str:
        arg_id = self._generate_id()

        self.graph.add_node(arg_id, agent=agent, text=text)

        if reply_to:
            self.graph.add_edge(reply_to, arg_id, relation=relation)

        return arg_id

    def export_markdown(self) -> str:
        lines = []
        for node in nx.topological_sort(self.graph):
            agent = self.graph.nodes[node]['agent']
            content = self.graph.nodes[node]['text']
            lines.append(f"**{node}** – {agent}: {content}")

            for succ in self.graph.successors(node):
                rel = self.graph.edges[node, succ]['relation']
                lines.append(f"{indent}→ **{rel.upper()}** [{succ}] – {self.graph.nodes[succ]['agent']}: {self.graph.nodes[succ]['text']}")
                

        return "\n".join(lines)

    # def export_json(self) -> Dict:
    #     return nx.readwrite.json_graph.node_link_data(self.graph, edges="links")
    
    def export_json(self) -> Dict:
        return nx.readwrite.json_graph.node_link_data(self.graph)
    

    def get_metrics(self) -> Dict:
        contradiction_edges = [e for e in self.graph.edges(data=True) if e[2]["relation"] == "attacks"]
        supports_edges = [e for e in self.graph.edges(data=True) if e[2]["relation"] == "supports"]

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "contradiction_ratio": round(len(contradiction_edges) / max(1, self.graph.number_of_edges()), 2),
            "avg_branching": round(sum(dict(self.graph.out_degree()).values()) / max(1, self.graph.number_of_nodes()), 2),
            "depth": nx.dag_longest_path_length(self.graph) if self.graph else 0
        }

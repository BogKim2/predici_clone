from __future__ import annotations

from html import escape
from pathlib import Path

import networkx as nx

from predici_clone.kinetics.reaction import ReactionStep


def reaction_network(steps: list[ReactionStep] | tuple[ReactionStep, ...]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for index, step in enumerate(steps):
        reaction = f"reaction:{index}:{step.name}"
        graph.add_node(reaction, kind="reaction", label=step.name)
        for species in step.reactants:
            graph.add_node(species, kind="species", label=species)
            graph.add_edge(species, reaction)
        for species in step.products:
            graph.add_node(species, kind="species", label=species)
            graph.add_edge(reaction, species)
    return graph


def export_html(graph: nx.DiGraph, path: str | Path) -> Path:
    nodes = "".join(f"<li data-kind='{escape(str(data.get('kind', '')))}'>{escape(str(data.get('label', node)))}</li>" for node, data in graph.nodes(data=True))
    edges = "".join(f"<li>{escape(str(source))} &rarr; {escape(str(target))}</li>" for source, target in graph.edges())
    destination = Path(path)
    destination.write_text(f"<!doctype html><meta charset='utf-8'><h1>Reaction network</h1><ul>{nodes}</ul><h2>Edges</h2><ul>{edges}</ul>", encoding="utf-8")
    return destination

"""Graphviz DOT Exporter for Genealogical Graph System (GGS)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS

KOSEKI_NS = "https://example.org/ns/koseki#"
IMI_NS = "https://imi.go.jp/ns/core/rdf#"


class DotExporter:
    """Exports RDF graph to Graphviz DOT format."""

    def __init__(self, graph: Graph):
        self.graph = graph

    def export_dot(self, title: str = "Genealogical Graph") -> str:
        """Generate Graphviz DOT script."""
        lines = [
            "digraph GGS {",
            f'    graph [rankdir=TB, splines=ortho, label="{title}", fontname="sans-serif"];',
            '    node [shape=box, style="filled,rounded", fontname="sans-serif", fillcolor="#f0f4f8", color="#2c3e50"];',
            '    edge [fontname="sans-serif", fontsize=10, color="#34495e"];',
            "",
        ]

        def sanitize_id(val: Any) -> str:
            raw = str(val).split("#")[-1].split("/")[-1]
            return f"n_{abs(hash(str(val))):x}" if not raw.isalnum() else f"n_{raw}"

        # 1. Households (as subgraphs/clusters or nodes)
        household_uris = list(self.graph.subjects(RDF.type, URIRef(KOSEKI_NS + "戸")))
        for h_idx, h_uri in enumerate(household_uris, start=1):
            h_label = ""
            for lbl in self.graph.objects(h_uri, RDFS.label):
                h_label = str(lbl)
                break
            if not h_label:
                h_label = f"戸 {h_idx}"

            address = ""
            for addr_node in self.graph.objects(h_uri, URIRef(KOSEKI_NS + "本籍")):
                for h_text in self.graph.objects(addr_node, URIRef(IMI_NS + "表記")):
                    address = str(h_text)
                    break

            lines.append(f"    subgraph cluster_{h_idx} {{")
            lines.append(f'        label = "{h_label}\\n{address}";')
            lines.append('        style = "dashed,filled";')
            lines.append('        fillcolor = "#f9f9f9";')
            lines.append('        color = "#7f8c8d";')

            # Members inside household
            members = list(self.graph.objects(h_uri, URIRef(KOSEKI_NS + "構成員")))
            for m in members:
                lines.append(f"        {sanitize_id(m)};")
            lines.append("    }")
            lines.append("")

        # 2. People nodes
        people_uris = list(self.graph.subjects(RDF.type, URIRef(KOSEKI_NS + "人物")))
        for p_uri in people_uris:
            p_id = sanitize_id(p_uri)
            name = ""
            for name_node in self.graph.objects(p_uri, URIRef(IMI_NS + "氏名")):
                for n_text in self.graph.objects(name_node, URIRef(IMI_NS + "表記")):
                    name = str(n_text)
                    break
                if not name:
                    sur = list(self.graph.objects(name_node, URIRef(IMI_NS + "姓")))
                    first = list(self.graph.objects(name_node, URIRef(IMI_NS + "名")))
                    if sur or first:
                        s_str = str(sur[0]) if sur else ""
                        f_str = str(first[0]) if first else ""
                        name = f"{s_str} {f_str}".strip()

            if not name:
                name = str(p_uri).split("#")[-1]

            # Birth date
            birth = ""
            for b_node in self.graph.objects(p_uri, URIRef(IMI_NS + "生年月日")):
                for b_text in self.graph.objects(b_node, URIRef(IMI_NS + "表記")):
                    birth = str(b_text)
                    break
                if not birth:
                    for b_date in self.graph.objects(b_node, URIRef(IMI_NS + "標準型日時")):
                        birth = str(b_date)
                        break

            # Relation to household head
            rel = ""
            for r_val in self.graph.objects(p_uri, URIRef(KOSEKI_NS + "戸主との続柄")):
                rel = str(r_val)
                break

            label_parts = [f"<b>{name}</b>"]
            if rel:
                label_parts.append(f"[{rel}]")
            if birth:
                label_parts.append(f"生: {birth}")

            label_html = "<" + "<br/>".join(label_parts) + ">"
            lines.append(f'    {p_id} [label={label_html}];')

        lines.append("")

        # 3. Edges: Biological parents
        for child in people_uris:
            c_id = sanitize_id(child)
            for father in self.graph.objects(child, URIRef(KOSEKI_NS + "実父")):
                f_id = sanitize_id(father)
                lines.append(f'    {f_id} -> {c_id} [label="実父", color="#2980b9"];')
            for mother in self.graph.objects(child, URIRef(KOSEKI_NS + "実母")):
                m_id = sanitize_id(mother)
                lines.append(f'    {m_id} -> {c_id} [label="実母", color="#e74c3c"];')
            for a_father in self.graph.objects(child, URIRef(KOSEKI_NS + "養父")):
                af_id = sanitize_id(a_father)
                lines.append(f'    {af_id} -> {c_id} [label="養父", style="dashed", color="#8e44ad"];')
            for a_mother in self.graph.objects(child, URIRef(KOSEKI_NS + "養母")):
                am_id = sanitize_id(a_mother)
                lines.append(f'    {am_id} -> {c_id} [label="養母", style="dashed", color="#d35400"];')

        # 4. Edges: Household head succession
        for event in self.graph.subjects(RDF.type, URIRef(KOSEKI_NS + "家督相続イベント")):
            prev_heads = list(self.graph.objects(event, URIRef(KOSEKI_NS + "前戸主")))
            new_heads = list(self.graph.objects(event, URIRef(KOSEKI_NS + "新戸主")))
            if prev_heads and new_heads:
                p_id = sanitize_id(prev_heads[0])
                n_id = sanitize_id(new_heads[0])
                lines.append(f'    {p_id} -> {n_id} [label="家督相続", style="dotted", color="#16a085", penwidth=2];')

        lines.append("}")
        return "\n".join(lines) + "\n"

    def export_to_file(self, target_path: Path | str, title: str = "Genealogical Graph") -> Path:
        """Export DOT script to file."""
        p = Path(target_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        dot_content = self.export_dot(title=title)
        p.write_text(dot_content, encoding="utf-8")
        return p

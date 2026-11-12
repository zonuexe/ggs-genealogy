"""Gramps XML 1.7.1 Importer for Genealogical Graph System (GGS)."""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import Any

from lxml import etree
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

GRAMPS_NS = "http://gramps-project.org/xml/1.7.1/"
KOSEKI_NS = "https://example.org/ns/koseki#"
IMI_NS = "https://imi.go.jp/ns/core/rdf#"


class GrampsImporter:
    """Imports Gramps XML 1.7.1 into RDF Graph."""

    def __init__(self, xml_content: str | bytes):
        if isinstance(xml_content, str):
            self.xml_bytes = xml_content.encode("utf-8")
        else:
            self.xml_bytes = xml_content

    @classmethod
    def from_file(cls, path: Path | str) -> GrampsImporter:
        """Load Gramps XML from a file (.xml or .gramps gzip)."""
        p = Path(path)
        raw_bytes = p.read_bytes()
        # Check if gzip (magic 1f 8b)
        if raw_bytes[:2] == b"\x1f\x8b":
            decompressed = gzip.decompress(raw_bytes)
            return cls(decompressed)
        return cls(raw_bytes)

    def to_rdf_graph(self) -> Graph:
        """Convert Gramps XML into an RDF Graph."""
        root = etree.fromstring(self.xml_bytes)

        # 1. Check if SSOT note is embedded
        ns = {"g": GRAMPS_NS}
        ssot_notes = root.xpath("//g:note[@id='N_GGS_TURTLE_SSOT']/g:text/text()", namespaces=ns)
        if isinstance(ssot_notes, list) and ssot_notes:
            graph = Graph()
            graph.parse(data=str(ssot_notes[0]), format="turtle")
            return graph

        # 2. Reconstruct RDF graph from Gramps structure
        graph = Graph()
        k_ns = Namespace(KOSEKI_NS)
        ic_ns = Namespace(IMI_NS)

        graph.bind("k", k_ns)
        graph.bind("ic", ic_ns)

        # Parse people
        people_nodes = root.xpath("//g:people/g:person", namespaces=ns)
        people: list[Any] = people_nodes if isinstance(people_nodes, list) else []
        handle_to_uri: dict[str, URIRef] = {}

        for p in people:
            handle = p.get("handle") or ""
            # Check for URI anchor
            uri_attr = p.xpath("g:attribute[@type='ggs:uri']/@value", namespaces=ns)
            if isinstance(uri_attr, list) and uri_attr:
                person_uri = URIRef(str(uri_attr[0]))
            else:
                person_id = p.get("id") or handle or "person_unknown"
                person_uri = URIRef(f"https://example.org/koseki#{person_id}")

            handle_to_uri[handle] = person_uri
            graph.add((person_uri, RDF.type, k_ns["人物"]))

            # Extract name
            names = p.xpath("g:name", namespaces=ns)
            if isinstance(names, list) and names:
                name_elem = names[0]
                first_nodes = name_elem.xpath("g:first/text()", namespaces=ns)
                first_name = (
                    str(first_nodes[0]) if isinstance(first_nodes, list) and first_nodes else ""
                )
                sur_nodes = name_elem.xpath("g:surname/text()", namespaces=ns)
                surname = (
                    str(sur_nodes[0]) if isinstance(sur_nodes, list) and sur_nodes else ""
                )

                name_bnode = graph.value(person_uri, ic_ns["氏名"])
                if name_bnode is None:
                    name_bnode = BNode()
                    graph.add((person_uri, ic_ns["氏名"], name_bnode))
                    graph.add((name_bnode, RDF.type, ic_ns["氏名型"]))

                if first_name:
                    graph.add((name_bnode, ic_ns["名"], Literal(first_name)))
                if surname:
                    graph.add((name_bnode, ic_ns["姓"], Literal(surname)))
                full = f"{surname} {first_name}".strip()
                if full:
                    graph.add((name_bnode, ic_ns["表記"], Literal(full)))

        # Parse families
        families_nodes = root.xpath("//g:families/g:family", namespaces=ns)
        families: list[Any] = families_nodes if isinstance(families_nodes, list) else []
        for f in families:
            f_uri_attr = f.xpath("g:attribute[@type='ggs:uri']/@value", namespaces=ns)
            if isinstance(f_uri_attr, list) and f_uri_attr:
                f_uri = URIRef(str(f_uri_attr[0]))
            else:
                f_id = f.get("id") or "household_unknown"
                f_uri = URIRef(f"https://example.org/koseki#{f_id}")

            graph.add((f_uri, RDF.type, k_ns["戸"]))

            father_handles = f.xpath("g:father/@hlink", namespaces=ns)
            if (
                isinstance(father_handles, list)
                and father_handles
                and str(father_handles[0]) in handle_to_uri
            ):
                father_uri = handle_to_uri[str(father_handles[0])]
                graph.add((f_uri, k_ns["戸主"], father_uri))
                graph.add((f_uri, k_ns["構成員"], father_uri))

            child_handles = f.xpath("g:childref/@hlink", namespaces=ns)
            if isinstance(child_handles, list):
                for c_handle in child_handles:
                    if str(c_handle) in handle_to_uri:
                        child_uri = handle_to_uri[str(c_handle)]
                        graph.add((f_uri, k_ns["構成員"], child_uri))

        return graph

    @classmethod
    def merge(
        cls,
        base_graph: Graph,
        gramps_path: Path | str,
    ) -> Graph:
        """Merge data from Gramps file into an existing base graph."""
        importer = cls.from_file(gramps_path)
        imported_graph = importer.to_rdf_graph()

        merged = Graph()
        for triple in base_graph:
            merged.add(triple)
        for triple in imported_graph:
            merged.add(triple)
        return merged

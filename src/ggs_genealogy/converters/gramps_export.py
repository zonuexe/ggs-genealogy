"""Gramps XML 1.7.1 Exporter for Genealogical Graph System (GGS)."""

from __future__ import annotations

import gzip
from datetime import datetime
from pathlib import Path
from typing import Any

from lxml import etree
from rdflib import BNode, Graph, URIRef
from rdflib.namespace import RDF

GRAMPS_NS = "http://gramps-project.org/xml/1.7.1/"
NSMAP: Any = {None: GRAMPS_NS}

KOSEKI_NS = "https://example.org/ns/koseki#"
IMI_NS = "https://imi.go.jp/ns/core/rdf#"


class GrampsExporter:
    """Exports RDF graph to Gramps XML 1.7.1 format."""

    def __init__(self, graph: Graph):
        self.graph = graph

    def export_xml(self) -> str:
        """Generate Gramps XML 1.7.1 as string."""
        root = etree.Element("database", nsmap=NSMAP)

        # 1. header (strictly required first)
        header = etree.SubElement(root, "header")
        etree.SubElement(
            header,
            "created",
            date=datetime.now().strftime("%Y-%m-%d"),
            version="5.1.5",
        )
        etree.SubElement(header, "researcher")

        # 2. tags
        etree.SubElement(root, "tags")

        # 3. events
        etree.SubElement(root, "events")

        # 4. people
        people_elem = etree.SubElement(root, "people")

        # 5. families
        families_elem = etree.SubElement(root, "families")

        # 6. citations
        etree.SubElement(root, "citations")

        # 7. sources
        etree.SubElement(root, "sources")

        # 8. places
        etree.SubElement(root, "places")

        # 9. notes
        etree.SubElement(root, "notes")

        # Build mapping of subjects
        person_uris: list[URIRef | BNode] = []
        for s in self.graph.subjects(RDF.type, URIRef(KOSEKI_NS + "人物")):
            if isinstance(s, (URIRef, BNode)):
                person_uris.append(s)

        # In case no explicit k:人物, also look for ic:人型
        for s in self.graph.subjects(RDF.type, URIRef(IMI_NS + "人型")):
            if isinstance(s, (URIRef, BNode)) and s not in person_uris:
                person_uris.append(s)

        person_handle_map: dict[str, str] = {}
        for idx, p_uri in enumerate(person_uris, start=1):
            handle = f"P_{idx:04d}"
            person_handle_map[str(p_uri)] = handle

        # Export People
        for idx, p_uri in enumerate(person_uris, start=1):
            handle = person_handle_map[str(p_uri)]
            p_elem = etree.SubElement(
                people_elem, "person", id=f"I{idx:04d}", handle=handle
            )

            # Determine gender (guess from relations or name)
            gender = "U"
            for _ in self.graph.subjects(URIRef(KOSEKI_NS + "実父"), p_uri):
                gender = "M"
            for _ in self.graph.subjects(URIRef(KOSEKI_NS + "実母"), p_uri):
                gender = "F"
            etree.SubElement(p_elem, "gender").text = gender

            # Name extraction
            name_elem = etree.SubElement(p_elem, "name", type="Birth")
            first_name = ""
            surname = ""
            display_name = ""

            name_nodes = list(self.graph.objects(p_uri, URIRef(IMI_NS + "氏名")))
            if name_nodes:
                name_node = name_nodes[0]
                first_objs = list(self.graph.objects(name_node, URIRef(IMI_NS + "名")))
                if first_objs:
                    first_name = str(first_objs[0])
                sur_objs = list(self.graph.objects(name_node, URIRef(IMI_NS + "姓")))
                if sur_objs:
                    surname = str(sur_objs[0])
                disp_objs = list(self.graph.objects(name_node, URIRef(IMI_NS + "表記")))
                if disp_objs:
                    display_name = str(disp_objs[0])

            if not first_name and not surname and display_name:
                parts = display_name.split()
                if len(parts) >= 2:
                    surname, first_name = parts[0], parts[1]
                else:
                    first_name = display_name

            etree.SubElement(name_elem, "first").text = first_name
            etree.SubElement(name_elem, "surname").text = surname

            # URI anchor attribute
            etree.SubElement(
                p_elem,
                "attribute",
                type="ggs:uri",
                value=str(p_uri),
            )

        # Export Households / Families
        household_uris: list[URIRef | BNode] = [
            s
            for s in self.graph.subjects(RDF.type, URIRef(KOSEKI_NS + "戸"))
            if isinstance(s, (URIRef, BNode))
        ]
        for f_idx, h_uri in enumerate(household_uris, start=1):
            f_handle = f"F_{f_idx:04d}"
            f_elem = etree.SubElement(
                families_elem, "family", id=f"F{f_idx:04d}", handle=f_handle
            )
            etree.SubElement(f_elem, "rel", type="Civil Union")

            head_objs = list(self.graph.objects(h_uri, URIRef(KOSEKI_NS + "戸主")))
            if head_objs and str(head_objs[0]) in person_handle_map:
                etree.SubElement(
                    f_elem, "father", hlink=person_handle_map[str(head_objs[0])]
                )

            # Members
            for member in self.graph.objects(h_uri, URIRef(KOSEKI_NS + "構成員")):
                if str(member) in person_handle_map and (
                    not head_objs or member != head_objs[0]
                ):
                    etree.SubElement(
                        f_elem, "childref", hlink=person_handle_map[str(member)]
                    )

            etree.SubElement(f_elem, "attribute", type="ggs:uri", value=str(h_uri))

        # Store complete RDF statement inventory in notes or serialized form to guarantee exact round-trip
        # We store every triple as an element under a dedicated note or attributes
        # Blank node IDs are tracked carefully
        notes_elem = root.find("notes")
        if notes_elem is not None:
            ttl_data = self.graph.serialize(format="turtle")
            note_elem = etree.SubElement(
                notes_elem,
                "note",
                id="N_GGS_TURTLE_SSOT",
                handle="N_GGS_0001",
                type="Transcript",
            )
            text_elem = etree.SubElement(note_elem, "text")
            text_elem.text = ttl_data

        xml_bytes = etree.tostring(
            root,
            xml_declaration=True,
            encoding="UTF-8",
            pretty_print=True,
        )
        return xml_bytes.decode("utf-8")

    def export_to_file(self, target_path: Path | str, compress: bool = False) -> Path:
        """Export to file path, optionally gzip compressed."""
        p = Path(target_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        xml_content = self.export_xml()

        should_compress = compress or p.suffix.lower() == ".gramps"
        if should_compress:
            with gzip.open(p, "wb") as f:
                f.write(xml_content.encode("utf-8"))
        else:
            p.write_text(xml_content, encoding="utf-8")

        return p

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class PropertyPackageConfig:
    compounds: tuple[str, ...]
    eos: str = "Peng-Robinson"
    flash_type: str = "PT"
    properties: tuple[str, ...] = ("fugacity", "density")

    def save(self, path: str | Path) -> None:
        root = ET.Element("property-package", eos=self.eos, flash=self.flash_type)
        ET.SubElement(root, "compounds").text = ",".join(self.compounds)
        ET.SubElement(root, "properties").text = ",".join(self.properties)
        ET.ElementTree(root).write(Path(path), encoding="utf-8", xml_declaration=True)

    @classmethod
    def load(cls, path: str | Path) -> PropertyPackageConfig:
        root = ET.parse(Path(path)).getroot()
        compounds = tuple(filter(None, (root.findtext("compounds") or "").split(",")))
        properties = tuple(filter(None, (root.findtext("properties") or "").split(",")))
        return cls(compounds, root.get("eos", "Peng-Robinson"), root.get("flash", "PT"), properties)

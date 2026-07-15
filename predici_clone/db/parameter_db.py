from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import xml.etree.ElementTree as ET


_UNIT_FACTORS = {
    "": (1.0, 0.0),
    "1": (1.0, 0.0),
    "Pa": (1.0, 0.0),
    "kPa": (1e3, 0.0),
    "bar": (1e5, 0.0),
    "K": (1.0, 0.0),
    "C": (1.0, 273.15),
    "kg/mol": (1.0, 0.0),
    "g/mol": (1e-3, 0.0),
    "J/mol": (1.0, 0.0),
    "kJ/mol": (1e3, 0.0),
}


@dataclass(frozen=True)
class DBParameter:
    set_name: str
    name: str
    value: float
    unit: str = ""
    description: str = ""
    source: str = ""
    rating: str = ""


@dataclass(frozen=True)
class DBFunction:
    set_name: str
    name: str
    expression: str
    unit: str = ""
    minimum: float | None = None
    maximum: float | None = None
    coefficients: dict[str, float] = field(default_factory=dict)

    def evaluate(self, temperature: float, pressure: float = 0.0) -> float:
        if self.minimum is not None and temperature < self.minimum or self.maximum is not None and temperature > self.maximum:
            raise ValueError(f"Temperature outside range for {self.set_name}/{self.name}")
        scope = {"T": float(temperature), "P": float(pressure), **{key.upper(): float(value) for key, value in self.coefficients.items()}}
        return float(eval(self.expression, {"__builtins__": {}}, scope))


@dataclass
class ParameterDatabase:
    parameters: dict[tuple[str, str], DBParameter] = field(default_factory=dict)
    functions: dict[tuple[str, str], DBFunction] = field(default_factory=dict)
    custom_units: dict[str, tuple[float, float]] = field(default_factory=dict)

    def add_parameter(self, parameter: DBParameter) -> None:
        self.parameters[(parameter.set_name, parameter.name)] = parameter

    def add_function(self, function: DBFunction) -> None:
        self.functions[(function.set_name, function.name)] = function

    def dbpar(self, set_name: str, property_name: str, unit: str | None = None) -> float:
        parameter = self.parameters[(set_name, property_name)]
        return convert_unit(parameter.value, parameter.unit, unit or parameter.unit, self.custom_units)

    def dbfunc(self, set_name: str, property_name: str, temperature: float, unit: str | None = None, pressure: float = 0.0) -> float:
        function = self.functions[(set_name, property_name)]
        return convert_unit(function.evaluate(temperature, pressure), function.unit, unit or function.unit, self.custom_units)

    def register_unit(self, name: str, factor: float, offset: float = 0.0) -> None:
        if not name or factor <= 0:
            raise ValueError("custom unit name and positive factor are required")
        self.custom_units[name] = (float(factor), float(offset))

    def import_clipboard(self, text: str) -> int:
        imported = 0
        for line in text.splitlines():
            if not line.strip():
                continue
            fields = line.split("\t")
            if fields[0].casefold() == "set":
                continue
            if len(fields) < 5:
                raise ValueError("clipboard rows require Set, Name, Desc, Value, and Unit")
            set_name, name, description, value, unit = fields[:5]
            self.add_parameter(DBParameter(set_name, name, float(value), unit, description))
            imported += 1
        return imported

    def export_excel(self, path: str | Path) -> Path:
        from openpyxl import Workbook

        workbook = Workbook()
        workbook.remove(workbook.active)
        for set_name in sorted({item.set_name for item in self.parameters.values()}):
            sheet = workbook.create_sheet(set_name[:31])
            sheet.append(["Name", "Description", "Value", "Unit", "Source", "Rating"])
            for item in self.parameters.values():
                if item.set_name == set_name:
                    sheet.append([item.name, item.description, item.value, item.unit, item.source, item.rating])
        destination = Path(path)
        workbook.save(destination)
        return destination

    def save(self, path: str | Path) -> None:
        root = ET.Element("parameter-database")
        units = ET.SubElement(root, "units")
        for name, (factor, offset) in self.custom_units.items():
            ET.SubElement(units, "unit", name=name, factor=str(factor), offset=str(offset))
        parameters = ET.SubElement(root, "parameters")
        for item in self.parameters.values():
            ET.SubElement(parameters, "parameter", set=item.set_name, name=item.name, value=str(item.value), unit=item.unit, description=item.description)
        functions = ET.SubElement(root, "functions")
        for item in self.functions.values():
            node = ET.SubElement(functions, "function", set=item.set_name, name=item.name, expression=item.expression, unit=item.unit)
            if item.minimum is not None:
                node.set("minimum", str(item.minimum))
            if item.maximum is not None:
                node.set("maximum", str(item.maximum))
            for name, value in item.coefficients.items():
                ET.SubElement(node, "coefficient", name=name, value=str(value))
        ET.ElementTree(root).write(Path(path), encoding="utf-8", xml_declaration=True)

    @classmethod
    def load(cls, path: str | Path) -> ParameterDatabase:
        root = ET.parse(Path(path)).getroot()
        database = cls()
        for node in root.findall("./units/unit"):
            database.register_unit(node.get("name", ""), float(node.get("factor", "1")), float(node.get("offset", "0")))
        for node in root.findall("./parameters/parameter"):
            database.add_parameter(DBParameter(node.get("set", ""), node.get("name", ""), float(node.get("value", "0")), node.get("unit", ""), node.get("description", "")))
        for node in root.findall("./functions/function"):
            coefficients = {item.get("name", ""): float(item.get("value", "0")) for item in node.findall("coefficient")}
            database.add_function(DBFunction(node.get("set", ""), node.get("name", ""), node.get("expression", "0"), node.get("unit", ""), _optional_float(node.get("minimum")), _optional_float(node.get("maximum")), coefficients))
        return database


def convert_unit(value: float, source: str, target: str, custom_units: dict[str, tuple[float, float]] | None = None) -> float:
    units = {**_UNIT_FACTORS, **(custom_units or {})}
    if source not in units or target not in units:
        raise ValueError(f"Unsupported unit conversion: {source} to {target}")
    source_factor, source_offset = units[source]
    target_factor, target_offset = units[target]
    base = float(value) * source_factor + source_offset
    return (base - target_offset) / target_factor


def _optional_float(value: str | None) -> float | None:
    return None if value is None else float(value)

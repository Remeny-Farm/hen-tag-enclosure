# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""Bambu Studio project (3MF) writer with no dependency on the Bambu CLI.

Mirrors the package the CLI writes (see out/cap_67_P1S.3mf): one assembly
object per cap in 3D/3dmodel.model, its three mesh bodies in
3D/Objects/object_<k>.model, per-part extruders in
Metadata/model_settings.config, and a full project_settings.config copied
from bambu/project_settings.json (the P1S 0.4 / 0.16 mm / PETG Basic project
Bambu Studio itself exported, with the three settings DESIGN.md asks for)
with the scheme's filament colours patched in.

Deterministic: fixed zip timestamps, uuid5 ids, sorted keys -- the same batch
produces a byte-identical plate.
"""

import json
import struct
import uuid
import zipfile
import zlib
from pathlib import Path

HERE = Path(__file__).parent
APP = Path("/Applications/BambuStudio.app/Contents/MacOS/BambuStudio")
TEMPLATE = HERE / "bambu" / "project_settings.json"
P1S_PRINTABLE_AREA = ["0x0", "256x0", "256x256", "0x256"]
P1S_EXCLUDE = ["0x0", "18x0", "18x28", "0x28"]
PLATE_MAX = 36
GRID_ORIGIN = 38.0      # first cap centre, both axes: clear of the 18 x 28 exclusion
GRID_PITCH = 36.0       # 31.94 mm cap + 4 mm
GRID_COLS = 6
STAMP = (2026, 1, 1, 0, 0, 0)
NS = uuid.UUID("6f1c2b7e-9c1e-4b2a-8f0e-2d5f7a1c3e44")
XML_HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n'
MODEL_NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
            'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
            'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
            'requiredextensions="p"')
BODY_EXTRUDER = {"shell": 1, "marking": 2, "core": 3}   # AMS slots
CLEAR_DISPLAY_HEX = "#F4F4F0"   # slot 1 is clear PETG; shown as near-white in the slicer
RECOMMENDED = {"wall_loops": "3", "wall_generator": "arachne", "reduce_crossing_wall": "1"}


def grid_positions(n: int) -> list[tuple[float, float]]:
    """Row-major centres for n caps, front row first."""
    if not 1 <= n <= PLATE_MAX:
        raise SystemExit(f"a plate holds 1..{PLATE_MAX} caps, got {n}")
    return [(GRID_ORIGIN + GRID_PITCH * (i % GRID_COLS), GRID_ORIGIN + GRID_PITCH * (i // GRID_COLS))
            for i in range(n)]


def grid_label(pos: tuple[float, float]) -> str:
    """'1A'..'6F': column number, row letter, for the manifest."""
    col = int(round((pos[0] - GRID_ORIGIN) / GRID_PITCH)) + 1
    row = int(round((pos[1] - GRID_ORIGIN) / GRID_PITCH))
    return f"{col}{chr(65 + row)}"


def _uid(*parts: str) -> str:
    return str(uuid.uuid5(NS, ":".join(parts)))


def _png_1x1() -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\xe9\xee\xf2"))
            + chunk(b"IEND", b""))


def _mesh_xml(oid: int, name: str, verts, tris) -> str:
    vx = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in verts)
    tx = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
    return (f'<object id="{oid}" p:UUID="{_uid("mesh", name)}" type="model">'
            f'<mesh><vertices>{vx}</vertices><triangles>{tx}</triangles></mesh></object>')


def write_plate(path: Path, caps: list[dict], scheme: dict, batch_id: str) -> None:
    """caps: [{"name", "position": (x, y), "bodies": {"shell"|"marking"|"core": (verts, tris)}}]
    Meshes are in world coordinates: cap bottom at z 0, centred on the xy
    origin, already in print orientation; the build item moves each cap to
    its plate position."""
    if len(caps) > PLATE_MAX:
        raise SystemExit(f"{len(caps)} caps exceed the plate ({PLATE_MAX})")
    entries: list[tuple[str, bytes]] = []
    assemblies, items, settings_objects, instances = [], [], [], []
    for k, cap in enumerate(caps):
        base = 4 * k
        meshes, comps, parts = [], [], []
        for bi, body in enumerate(("shell", "marking", "core")):
            oid = base + 1 + bi
            verts, tris = cap["bodies"][body]
            meshes.append(_mesh_xml(oid, f'{cap["name"]}:{body}', verts, tris))
            comps.append(f'<component p:path="/3D/Objects/object_{k + 1}.model" objectid="{oid}" '
                         f'p:UUID="{_uid("comp", cap["name"], body)}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>')
            parts.append(f'<part id="{oid}" subtype="normal_part" uuid="{_uid("part", cap["name"], body)}">'
                         f'<metadata key="name" value="{cap["name"]}_{body}"/>'
                         f'<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>'
                         f'<metadata key="extruder" value="{BODY_EXTRUDER[body]}"/></part>')
        entries.append((f"3D/Objects/object_{k + 1}.model",
                        (XML_HEAD + f'<model unit="millimeter" xml:lang="en-US" {MODEL_NS}>'
                         '<metadata name="BambuStudio:3mfVersion">1</metadata>'
                         f'<resources>{"".join(meshes)}</resources><build/></model>').encode()))
        aid = base + 4
        x, y = cap["position"]
        assemblies.append(f'<object id="{aid}" p:UUID="{_uid("asm", cap["name"])}" type="model">'
                          f'<components>{"".join(comps)}</components></object>')
        items.append(f'<item objectid="{aid}" p:UUID="{_uid("item", cap["name"])}" '
                     f'transform="1 0 0 0 1 0 0 0 1 {x:g} {y:g} 0" printable="1"/>')
        settings_objects.append(f'<object id="{aid}"><metadata key="name" value="{cap["name"]}"/>'
                                f'{"".join(parts)}</object>')
        instances.append(f'<model_instance><metadata key="object_id" value="{aid}"/>'
                         f'<metadata key="instance_id" value="0"/>'
                         f'<metadata key="identify_id" value="{100 + k}"/></model_instance>')
    model = (XML_HEAD + f'<model unit="millimeter" xml:lang="en-US" {MODEL_NS}>'
             '<metadata name="Application">hen-tag cap_batch</metadata>'
             '<metadata name="BambuStudio:3mfVersion">1</metadata>'
             f'<metadata name="Title">{batch_id}</metadata>'
             f'<resources>{"".join(assemblies)}</resources>'
             f'<build p:UUID="{_uid("build", batch_id)}">{"".join(items)}</build></model>')
    model_settings = (
        XML_HEAD + '<config>' + "".join(settings_objects)
        + '<plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value=""/>'
        '<metadata key="locked" value="false"/><metadata key="filament_map_mode" value="Auto For Flush"/>'
        '<metadata key="gcode_file" value=""/><metadata key="thumbnail_file" value="Metadata/plate_1.png"/>'
        '<metadata key="thumbnail_no_light_file" value="Metadata/plate_no_light_1.png"/>'
        '<metadata key="top_file" value="Metadata/top_1.png"/><metadata key="pick_file" value="Metadata/pick_1.png"/>'
        + "".join(instances) + '</plate><assemble></assemble></config>')
    cfg = json.loads(TEMPLATE.read_text())
    cfg["printable_area"], cfg["bed_exclude_area"] = P1S_PRINTABLE_AREA, P1S_EXCLUDE
    cfg["filament_colour"] = [CLEAR_DISPLAY_HEX, scheme["text"]["hex"], scheme["accent"]["hex"]]
    cfg.update(RECOMMENDED)
    ctypes = (XML_HEAD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
              '<Default Extension="png" ContentType="image/png"/></Types>')
    rels = (XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            '<Relationship Target="/Metadata/plate_1.png" Id="rel-2" '
            'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>'
            '</Relationships>')
    model_rels = (XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                  + "".join(f'<Relationship Target="/3D/Objects/object_{k + 1}.model" Id="rel-{k + 1}" '
                            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
                            for k in range(len(caps)))
                  + '</Relationships>')
    slice_info = (XML_HEAD + '<config><header><header_item key="X-BBL-Client-Type" value="slicer"/>'
                  '</header></config>')
    png = _png_1x1()
    head = [("[Content_Types].xml", ctypes.encode()), ("_rels/.rels", rels.encode()),
            ("3D/3dmodel.model", model.encode()), ("3D/_rels/3dmodel.model.rels", model_rels.encode())]
    tail = [("Metadata/project_settings.config", json.dumps(cfg, indent=4, sort_keys=True).encode()),
            ("Metadata/model_settings.config", model_settings.encode()),
            ("Metadata/slice_info.config", slice_info.encode()),
            ("Metadata/plate_1.png", png), ("Metadata/plate_no_light_1.png", png),
            ("Metadata/top_1.png", png), ("Metadata/pick_1.png", png)]
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, payload in head + entries + tail:
            info = zipfile.ZipInfo(name, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, payload)

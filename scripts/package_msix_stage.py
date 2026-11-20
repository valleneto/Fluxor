"""OS025-C: package FLUXOR executable as unsigned DEVELOPMENT MSIX only."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
from xml.etree import ElementTree as ET
import zipfile

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter

PKG = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
UAP = "http://schemas.microsoft.com/appx/manifest/uap/windows10"
UAP10 = "http://schemas.microsoft.com/appx/manifest/uap/windows10/10"
RESCAP = "http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
NAME = "Fluxor.InternalDevelopment"
PUBLISHER = "CN=FLUXOR Internal Staging"


def icon(source, target, size):
    image = QImage(str(source))
    if image.isNull():
        raise RuntimeError("Invalid logo")
    image = image.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
    canvas = QImage(size, size, QImage.Format.Format_ARGB32)
    canvas.fill(0xFF111318)
    painter = QPainter(canvas)
    painter.drawImage((size-image.width()) // 2,
                      (size-image.height()) // 2, image)
    painter.end()
    if not canvas.save(str(target), "PNG"):
        raise RuntimeError("Could not write logo")


def manifest():
    return f'''<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="{PKG}" xmlns:uap="{UAP}" xmlns:uap10="{UAP10}"
         xmlns:rescap="{RESCAP}" IgnorableNamespaces="uap uap10 rescap">
  <Identity Name="{NAME}" Publisher="{PUBLISHER}"
            Version="0.25.3.0" ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>FLUXOR Internal Beta</DisplayName>
    <PublisherDisplayName>FLUXOR Development Only</PublisherDisplayName>
    <Description>Internal packaging validation, not for distribution</Description>
    <Logo>Assets\StoreLogo.png</Logo>
  </Properties>
  <Resources><Resource Language="pt-BR" /></Resources>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop"
                        MinVersion="10.0.19041.0" MaxVersionTested="10.0.22621.0" />
  </Dependencies>
  <Capabilities><rescap:Capability Name="runFullTrust" /></Capabilities>
  <Applications>
    <Application Id="FLUXOR" Executable="FLUXOR.exe"
                 uap10:RuntimeBehavior="packagedClassicApp"
                 uap10:TrustLevel="mediumIL">
      <uap:VisualElements DisplayName="FLUXOR Internal Beta"
                          Description="File organization prototype, not certified"
                          Square150x150Logo="Assets\Square150x150Logo.png"
                          Square44x44Logo="Assets\Square44x44Logo.png"
                          BackgroundColor="transparent" />
    </Application>
  </Applications>
</Package>
'''


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def main():
    arg = argparse.ArgumentParser()
    for field in ("dist", "staging", "output", "makeappx"):
        arg.add_argument("--" + field, required=True)
    p = arg.parse_args()
    if os.name != "nt":
        raise RuntimeError("Windows-only staging")
    source = Path(p.dist).resolve(strict=True)
    if source.name != "FLUXOR" or not (source / "FLUXOR.exe").is_file():
        raise RuntimeError("PyInstaller FLUXOR.exe missing")
    stage = Path(p.staging).absolute()
    output = Path(p.output).absolute()
    if stage.exists() or output.exists():
        raise RuntimeError("Refusing to overwrite preexisting staging/output")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, stage)
    assets = stage / "Assets"
    assets.mkdir()
    logo = Path("assets/fluxor_logo.png").resolve(strict=True)
    for name, size in (("StoreLogo", 50), ("Square150x150Logo", 150),
                       ("Square44x44Logo", 44)):
        icon(logo, assets / (name + ".png"), size)
    xml = manifest()
    ET.fromstring(xml)
    (stage / "AppxManifest.xml").write_text(xml, encoding="utf-8")
    subprocess.run([p.makeappx, "pack", "/o", "/d", str(stage), "/p",
                    str(output)], check=True, timeout=240)
    with zipfile.ZipFile(output) as zipped:
        assert zipped.testzip() is None
        names = set(zipped.namelist())
        assert {"AppxManifest.xml", "FLUXOR.exe",
                "Assets/StoreLogo.png", "Assets/Square150x150Logo.png",
                "Assets/Square44x44Logo.png"}.issubset(names), names
        node = ET.fromstring(zipped.read("AppxManifest.xml"))
        identity = node.find("{" + PKG + "}Identity")
        assert identity is not None
        assert identity.attrib["Name"] == NAME
        assert identity.attrib["Publisher"] == PUBLISHER
    sha = digest(output)
    (output.parent / "SHA256_INTERNAL.txt").write_text(
        sha + " *" + output.name + "\n", encoding="ascii")
    print("MSIX_STRUCTURE_PASS", output)
    print("SHA256", sha)
    print("STAGING ONLY - unsigned, non-Store identity, never publish")


if __name__ == "__main__":
    main()

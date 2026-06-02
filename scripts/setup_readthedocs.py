"""Build-Skript für Read the Docs Dokumentation.

Dieses Skript erstellt die Sphinx-Dokumentation für das GMCounter-Projekt
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, cwd=None):
    """Führt einen Shell-Befehl aus und gibt das Ergebnis zurück."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Fehler beim Ausführen von: {cmd}")
            print(f"Fehlerausgabe: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Fehler: {e}")
        return False


def setup_sphinx_docs():
    """Erstellt die Sphinx-Dokumentation."""
    print("🚀 Erstelle Read the Docs Dokumentation...")

    # Aktuelles Verzeichnis ermitteln
    project_root = Path(__file__).parent.absolute()
    docs_dir = project_root / "docs"

    print(f"📁 Projektverzeichnis: {project_root}")
    print(f"📁 Dokumentationsverzeichnis: {docs_dir}")

    # Ins Dokumentationsverzeichnis wechseln
    os.chdir(docs_dir)

    # Prüfen ob conf.py existiert
    if not (docs_dir / "conf.py").exists():
        print("❌ conf.py nicht gefunden! Bitte führen Sie erst das Setup aus.")
        return False

    # Build-Verzeichnis löschen falls vorhanden
    build_dir = docs_dir / "_build"
    if build_dir.exists():
        print("🧹 Lösche altes Build-Verzeichnis...")
        shutil.rmtree(build_dir)

    # Sphinx-Build ausführen
    print("🔨 Baue Sphinx-Dokumentation...")
    cmd = "sphinx-build -b html . _build/html"
    if not run_command(cmd):
        return False

    print("✅ Dokumentation erfolgreich erstellt!")
    print(f"📖 Dokumentation verfügbar unter: {build_dir / 'html' / 'index.html'}")

    return True


def install_requirements():
    """Installiert die benötigten Pakete."""
    print("📦 Installiere Abhängigkeiten...")

    requirements_files = ["docs/requirements.txt", "requirements.txt"]

    for req_file in requirements_files:
        if os.path.exists(req_file):
            print(f"📥 Installiere Pakete aus {req_file}...")
            if not run_command(f"pip install -r {req_file}"):
                print(f"❌ Fehler beim Installieren von {req_file}")
                return False

    return True


def check_readthedocs_config():
    """Prüft die Read the Docs Konfiguration."""
    print("🔍 Prüfe Read the Docs Konfiguration...")

    config_file = Path(".readthedocs.yaml")
    if not config_file.exists():
        print("❌ .readthedocs.yaml nicht gefunden!")
        return False

    print("✅ .readthedocs.yaml gefunden")

    # Prüfe docs/conf.py
    conf_file = Path("docs/conf.py")
    if not conf_file.exists():
        print("❌ docs/conf.py nicht gefunden!")
        return False

    print("✅ docs/conf.py gefunden")

    # Prüfe docs/requirements.txt
    docs_req_file = Path("docs/requirements.txt")
    if not docs_req_file.exists():
        print("❌ docs/requirements.txt nicht gefunden!")
        return False

    print("✅ docs/requirements.txt gefunden")

    return True


def main():
    """Hauptfunktion."""
    print("🎯 Read the Docs Setup für GMCounter")
    print("=" * 50)

    # Argument parsing
    if len(sys.argv) > 1:
        if sys.argv[1] == "install":
            if install_requirements():
                print("✅ Installation abgeschlossen!")
            else:
                print("❌ Installation fehlgeschlagen!")
                sys.exit(1)
            return
        elif sys.argv[1] == "build":
            if setup_sphinx_docs():
                print("✅ Build abgeschlossen!")
            else:
                print("❌ Build fehlgeschlagen!")
                sys.exit(1)
            return
        elif sys.argv[1] == "check":
            if check_readthedocs_config():
                print("✅ Konfiguration ist korrekt!")
            else:
                print("❌ Konfigurationsprobleme gefunden!")
                sys.exit(1)
            return

    # Vollständiger Workflow
    print("🚀 Führe vollständigen Setup-Workflow aus...")

    # 1. Konfiguration prüfen
    if not check_readthedocs_config():
        sys.exit(1)

    # 2. Abhängigkeiten installieren
    if not install_requirements():
        sys.exit(1)

    # 3. Dokumentation erstellen
    if not setup_sphinx_docs():
        sys.exit(1)

    print("\n" + "=" * 50)
    print("🎉 Read the Docs Setup erfolgreich abgeschlossen!")
    print("\nNächste Schritte:")
    print("1. Verbinden Sie Ihr Repository mit Read the Docs")
    print("2. Importieren Sie das Projekt auf https://readthedocs.org")
    print("3. Die Dokumentation wird automatisch bei jedem Push aktualisiert")
    print("\n📚 Lokale Dokumentation: docs/_build/html/index.html")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SSH Remote Manager für Symfony Parameters.yml
Verwaltet parameters.yml Dateien über SSH-Verbindungen basierend auf Konfigurationsdatei.
"""

import os
import sys
import yaml
import json
import argparse
import logging
import tempfile
import secrets
import string
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

try:
    import paramiko
    from scp import SCPClient
except ImportError:
    print("❌ Fehlende Dependencies! Installieren Sie:")
    print("pip install paramiko scp")
    sys.exit(1)

from parameter_updater import ParameterUpdater


class SSHManager:
    def __init__(self, config_file: str = "ssh_config.yml", log_level: str = "INFO"):
        """Initialize SSH Manager with configuration."""
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self.config = self.load_config()
        self.updater = ParameterUpdater(log_level)
        self.ssh_connections = {}

    def load_config(self) -> Dict[str, Any]:
        """Lädt die SSH-Konfiguration."""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                self.logger.info(f"Konfiguration geladen: {self.config_file}")
                return config
        except FileNotFoundError:
            self.logger.error(f"Konfigurationsdatei nicht gefunden: {self.config_file}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"Fehler beim Laden der Konfiguration: {e}")
            raise

    def get_ssh_connection(self, server_name: str) -> paramiko.SSHClient:
        """Erstellt oder gibt bestehende SSH-Verbindung zurück."""
        if server_name in self.ssh_connections:
            # Teste ob Verbindung noch aktiv ist
            try:
                transport = self.ssh_connections[server_name].get_transport()
                if transport and transport.is_active():
                    return self.ssh_connections[server_name]
            except:
                pass

        # Neue Verbindung erstellen
        server_config = self.config["servers"][server_name]
        ssh_settings = self.config.get("ssh_settings", {})

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # SSH Verbindungsparameter
            connect_params = {
                "hostname": server_config["host"],
                "port": server_config.get("port", 22),
                "username": server_config["username"],
                "timeout": ssh_settings.get("timeout", 30),
            }

            # SSH Key oder Passwort
            if "ssh_key" in server_config:
                key_path = os.path.expanduser(server_config["ssh_key"])
                if os.path.exists(key_path):
                    connect_params["key_filename"] = key_path
                else:
                    self.logger.warning(f"SSH Key nicht gefunden: {key_path}")

            if "password" in server_config:
                connect_params["password"] = server_config["password"]

            ssh.connect(**connect_params)
            self.ssh_connections[server_name] = ssh
            self.logger.info(
                f"SSH-Verbindung hergestellt: {server_name} ({server_config['host']})"
            )

            return ssh

        except Exception as e:
            self.logger.error(f"SSH-Verbindung fehlgeschlagen für {server_name}: {e}")
            raise

    def close_all_connections(self):
        """Schließt alle SSH-Verbindungen."""
        for server_name, ssh in self.ssh_connections.items():
            try:
                ssh.close()
                self.logger.info(f"SSH-Verbindung geschlossen: {server_name}")
            except:
                pass
        self.ssh_connections.clear()

    def execute_remote_command(
        self, server_name: str, command: str
    ) -> Tuple[str, str, int]:
        """Führt einen Befehl auf dem Remote-Server aus."""
        ssh = self.get_ssh_connection(server_name)

        try:
            stdin, stdout, stderr = ssh.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()

            stdout_data = stdout.read().decode("utf-8")
            stderr_data = stderr.read().decode("utf-8")

            return stdout_data, stderr_data, exit_code

        except Exception as e:
            self.logger.error(
                f"Fehler beim Ausführen des Befehls auf {server_name}: {e}"
            )
            raise

    def download_file(
        self, server_name: str, remote_path: str, local_path: str
    ) -> bool:
        """Lädt eine Datei vom Remote-Server herunter."""
        ssh = self.get_ssh_connection(server_name)

        try:
            with SCPClient(ssh.get_transport()) as scp:
                scp.get(remote_path, local_path)
                self.logger.info(
                    f"Datei heruntergeladen: {remote_path} -> {local_path}"
                )
                return True

        except Exception as e:
            self.logger.error(f"Fehler beim Herunterladen von {remote_path}: {e}")
            return False

    def upload_file(self, server_name: str, local_path: str, remote_path: str) -> bool:
        """Lädt eine Datei auf den Remote-Server hoch."""
        ssh = self.get_ssh_connection(server_name)

        try:
            with SCPClient(ssh.get_transport()) as scp:
                scp.put(local_path, remote_path)
                self.logger.info(f"Datei hochgeladen: {local_path} -> {remote_path}")
                return True

        except Exception as e:
            self.logger.error(f"Fehler beim Hochladen nach {remote_path}: {e}")
            return False

    def get_file_permissions(
        self, server_name: str, file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Ermittelt Dateiberechtigungen auf Remote-Server."""
        command = f"stat -c '%a %U %G' '{file_path}'"
        stdout, stderr, exit_code = self.execute_remote_command(server_name, command)

        if exit_code == 0:
            parts = stdout.strip().split()
            if len(parts) >= 3:
                return {"permissions": parts[0], "owner": parts[1], "group": parts[2]}

        self.logger.error(
            f"Konnte Berechtigungen nicht ermitteln für {file_path}: {stderr}"
        )
        return None

    def restore_file_permissions(
        self, server_name: str, file_path: str, permissions: Dict[str, Any]
    ) -> bool:
        """Stellt Dateiberechtigungen auf Remote-Server wieder her."""
        try:
            # Besitzer und Gruppe wiederherstellen
            chown_cmd = (
                f"chown {permissions['owner']}:{permissions['group']} '{file_path}'"
            )
            stdout, stderr, exit_code = self.execute_remote_command(
                server_name, chown_cmd
            )

            if exit_code != 0:
                self.logger.warning(f"chown fehlgeschlagen: {stderr}")

            # Berechtigungen wiederherstellen
            chmod_cmd = f"chmod {permissions['permissions']} '{file_path}'"
            stdout, stderr, exit_code = self.execute_remote_command(
                server_name, chmod_cmd
            )

            if exit_code != 0:
                self.logger.warning(f"chmod fehlgeschlagen: {stderr}")
                return False

            self.logger.info(f"Berechtigungen wiederhergestellt für {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Wiederherstellen der Berechtigungen: {e}")
            return False

    def create_remote_backup(self, server_name: str, file_path: str) -> Optional[str]:
        """Erstellt ein Backup auf dem Remote-Server."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.config.get("ssh_settings", {}).get(
            "backup_dir", "/tmp/symfony_backups"
        )
        backup_filename = f"{os.path.basename(file_path)}.backup_{timestamp}"
        backup_path = f"{backup_dir}/{backup_filename}"

        # Backup-Verzeichnis erstellen
        mkdir_cmd = f"mkdir -p '{backup_dir}'"
        self.execute_remote_command(server_name, mkdir_cmd)

        # Backup erstellen
        cp_cmd = f"cp '{file_path}' '{backup_path}'"
        stdout, stderr, exit_code = self.execute_remote_command(server_name, cp_cmd)

        if exit_code == 0:
            self.logger.info(f"Remote-Backup erstellt: {backup_path}")
            return backup_path
        else:
            self.logger.error(f"Backup-Erstellung fehlgeschlagen: {stderr}")
            return None

    def update_remote_parameters(
        self, server_name: str, customer_name: str, new_parameters: Dict[str, Any]
    ) -> bool:
        """Aktualisiert Parameter auf Remote-Server."""
        try:
            server_config = self.config["servers"][server_name]
            customer_config = server_config["customers"][customer_name]
            remote_path = customer_config["parameters_path"]

            self.logger.info(
                f"Aktualisiere {customer_name} auf {server_name}: {remote_path}"
            )

            # 1. Aktuelle Berechtigungen speichern
            permissions = self.get_file_permissions(server_name, remote_path)
            if not permissions:
                self.logger.warning(
                    "Konnte Berechtigungen nicht ermitteln, fahre trotzdem fort..."
                )

            # 2. Remote-Backup erstellen
            backup_path = self.create_remote_backup(server_name, remote_path)

            # 3. Datei herunterladen
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".yml", delete=False
            ) as temp_file:
                temp_path = temp_file.name

            if not self.download_file(server_name, remote_path, temp_path):
                return False

            # 4. Lokal bearbeiten
            success = self.updater.update_parameters(
                temp_path, new_parameters, create_backup=False
            )
            if not success:
                os.unlink(temp_path)
                return False

            # 5. Zurück hochladen
            if not self.upload_file(server_name, temp_path, remote_path):
                os.unlink(temp_path)
                return False

            # 6. Berechtigungen wiederherstellen
            if permissions:
                self.restore_file_permissions(server_name, remote_path, permissions)

            # 7. Temporäre Datei löschen
            os.unlink(temp_path)

            self.logger.info(
                f"Parameter erfolgreich aktualisiert: {customer_name} auf {server_name}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren von {customer_name}: {e}")
            return False

    def list_all_customers(self) -> Dict[str, Dict[str, Any]]:
        """Listet alle Kunden aus der Konfiguration auf."""
        all_customers = {}

        for server_name, server_config in self.config["servers"].items():
            for customer_name, customer_config in server_config["customers"].items():
                full_name = f"{server_name}:{customer_name}"
                all_customers[full_name] = {
                    "server": server_name,
                    "customer": customer_name,
                    "path": customer_config["parameters_path"],
                    "description": customer_config.get("description", ""),
                    "host": server_config["host"],
                }

        return all_customers

    def bulk_update_parameter(
        self, targets: List[str], parameter_name: str, parameter_value: Any
    ) -> Dict[str, bool]:
        """Führt Bulk-Update für mehrere Kunden durch."""
        results = {}

        # Spezialbehandlung für Secret-Generierung
        if parameter_value == "GENERATE_NEW" and parameter_name == "secret":
            # Für jeden Kunden einen eigenen Secret generieren
            for target in targets:
                if ":" in target:
                    server_name, customer_name = target.split(":", 1)
                    new_secret = self.generate_secret()
                    results[target] = self.update_remote_parameters(
                        server_name, customer_name, {parameter_name: new_secret}
                    )
                else:
                    results[target] = False
        else:
            # Normales Bulk-Update
            for target in targets:
                if ":" in target:
                    server_name, customer_name = target.split(":", 1)
                    results[target] = self.update_remote_parameters(
                        server_name, customer_name, {parameter_name: parameter_value}
                    )
                else:
                    results[target] = False

        return results

    def generate_secret(self, length: int = 32) -> str:
        """Generiert einen zufälligen Secret-Key."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def apply_bulk_template(
        self, template_name: str, targets: List[str]
    ) -> Dict[str, bool]:
        """Wendet eine Bulk-Template auf Ziele an."""
        if template_name not in self.config.get("bulk_templates", {}):
            self.logger.error(f"Template nicht gefunden: {template_name}")
            return {}

        template = self.config["bulk_templates"][template_name]
        parameters = template["parameters"].copy()

        # Spezialbehandlung für GENERATE_NEW
        for key, value in parameters.items():
            if value == "GENERATE_NEW" and key == "secret":
                # Wird in bulk_update_parameter behandelt
                pass

        results = {}
        for target in targets:
            if ":" in target:
                server_name, customer_name = target.split(":", 1)

                # Für jeden Kunden separate Parameter-Kopie (für individuelle Secrets)
                target_params = parameters.copy()
                for key, value in target_params.items():
                    if value == "GENERATE_NEW" and key == "secret":
                        target_params[key] = self.generate_secret()

                results[target] = self.update_remote_parameters(
                    server_name, customer_name, target_params
                )
            else:
                results[target] = False

        return results

    def download_all_configs(
        self, output_dir: str = "downloaded_configs"
    ) -> Dict[str, bool]:
        """Lädt alle Parameter-Dateien herunter."""
        os.makedirs(output_dir, exist_ok=True)
        results = {}

        for server_name, server_config in self.config["servers"].items():
            for customer_name, customer_config in server_config["customers"].items():
                remote_path = customer_config["parameters_path"]
                local_filename = f"{server_name}_{customer_name}_parameters.yml"
                local_path = os.path.join(output_dir, local_filename)

                target = f"{server_name}:{customer_name}"
                results[target] = self.download_file(
                    server_name, remote_path, local_path
                )

        return results

    def generate_web_config(self) -> str:
        """Generiert JSON-Konfiguration für Web-Interface."""
        web_config = {}

        for server_name, server_config in self.config["servers"].items():
            for customer_name, customer_config in server_config["customers"].items():
                full_name = f"{server_name}:{customer_name}"
                web_config[full_name] = {
                    "server": server_name,
                    "customer": customer_name,
                    "file_path": customer_config["parameters_path"],
                    "description": customer_config.get("description", ""),
                    "host": server_config["host"],
                    "parameters": {},  # Wird beim Laden gefüllt
                }

        return json.dumps(web_config, indent=2, ensure_ascii=False)

    def test_connection(self, server_name: str) -> bool:
        """Test SSH connection to a server."""
        try:
            if server_name not in self.config["servers"]:
                self.logger.error(f"Server {server_name} not found in configuration")
                return False

            server_config = self.config["servers"][server_name]

            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connection parameters
            connect_params = {
                "hostname": server_config["host"],
                "port": server_config.get("port", 22),
                "username": server_config["username"],
                "timeout": self.config.get("ssh_settings", {}).get("timeout", 30),
            }

            # Add authentication
            if "password" in server_config:
                connect_params["password"] = server_config["password"]
            elif "ssh_key" in server_config:
                key_path = os.path.expanduser(server_config["ssh_key"])
                if os.path.exists(key_path):
                    connect_params["key_filename"] = key_path

            # Test connection
            ssh.connect(**connect_params)

            # Test with a simple command
            stdin, stdout, stderr = ssh.exec_command("echo 'test'")
            result = stdout.read().decode().strip()

            ssh.close()

            return result == "test"

        except Exception as e:
            self.logger.error(f"Connection test failed for {server_name}: {e}")
            return False


def main():
    """Hauptfunktion für Command-Line Interface."""
    parser = argparse.ArgumentParser(
        description="SSH Remote Manager für Symfony Parameters.yml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Alle Kunden auflisten
  python ssh_manager.py --list
  
  # Parameter bei spezifischen Kunden ändern
  python ssh_manager.py --update production:kunde1 staging:kunde1_staging --param database_host=new-db.example.com
  
  # Bulk-Template anwenden
  python ssh_manager.py --template database_migration --targets production:kunde1 production:kunde2
  
  # Alle Konfigurationen herunterladen
  python ssh_manager.py --download-all
  
  # Web-Konfiguration generieren
  python ssh_manager.py --generate-web-config
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        default="ssh_config.yml",
        help="SSH-Konfigurationsdatei (default: ssh_config.yml)",
    )
    parser.add_argument(
        "--list", action="store_true", help="Alle verfügbaren Kunden auflisten"
    )
    parser.add_argument(
        "--update", nargs="+", help="Kunden aktualisieren (Format: server:kunde)"
    )
    parser.add_argument(
        "--param",
        action="append",
        help="Parameter im Format key=value (kann mehrfach verwendet werden)",
    )
    parser.add_argument("--template", help="Bulk-Template anwenden")
    parser.add_argument(
        "--targets", nargs="+", help="Ziel-Kunden für Template (Format: server:kunde)"
    )
    parser.add_argument(
        "--download-all",
        action="store_true",
        help="Alle Parameter-Dateien herunterladen",
    )
    parser.add_argument(
        "--generate-web-config",
        action="store_true",
        help="Web-Konfiguration generieren",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log-Level (default: INFO)",
    )

    args = parser.parse_args()

    try:
        manager = SSHManager(args.config, args.log_level)

        # Alle Kunden auflisten
        if args.list:
            customers = manager.list_all_customers()
            print(f"\n📋 Verfügbare Kunden ({len(customers)}):")
            print("-" * 80)
            for full_name, info in customers.items():
                print(f"🖥️  {full_name}")
                print(f"    Host: {info['host']}")
                print(f"    Pfad: {info['path']}")
                print(f"    Beschreibung: {info['description']}")
                print()

        # Parameter aktualisieren
        if args.update and args.param:
            parameters = {}
            for param in args.param:
                if "=" not in param:
                    print(
                        f"❌ Ungültiges Parameter-Format: {param} (erwartet: key=value)"
                    )
                    sys.exit(1)
                key, value = param.split("=", 1)
                parameters[key.strip()] = value.strip()

            print(f"\n🔄 Aktualisiere Parameter für {len(args.update)} Kunden...")
            results = {}

            for target in args.update:
                if ":" not in target:
                    print(
                        f"❌ Ungültiges Ziel-Format: {target} (erwartet: server:kunde)"
                    )
                    continue

                server_name, customer_name = target.split(":", 1)
                results[target] = manager.update_remote_parameters(
                    server_name, customer_name, parameters
                )

            print("\n📊 Ergebnisse:")
            for target, success in results.items():
                status = "✅ Erfolgreich" if success else "❌ Fehler"
                print(f"  {target}: {status}")

        # Template anwenden
        if args.template and args.targets:
            print(
                f"\n🔄 Wende Template '{args.template}' auf {len(args.targets)} Kunden an..."
            )
            results = manager.apply_bulk_template(args.template, args.targets)

            print("\n📊 Ergebnisse:")
            for target, success in results.items():
                status = "✅ Erfolgreich" if success else "❌ Fehler"
                print(f"  {target}: {status}")

        # Alle Konfigurationen herunterladen
        if args.download_all:
            print("\n💾 Lade alle Konfigurationen herunter...")
            results = manager.download_all_configs()

            print("\n📊 Download-Ergebnisse:")
            for target, success in results.items():
                status = "✅ Erfolgreich" if success else "❌ Fehler"
                print(f"  {target}: {status}")

        # Web-Konfiguration generieren
        if args.generate_web_config:
            print("\n🌐 Generiere Web-Konfiguration...")
            web_config = manager.generate_web_config()

            with open("ssh_web_config.json", "w", encoding="utf-8") as f:
                f.write(web_config)

            print("✅ Web-Konfiguration gespeichert in: ssh_web_config.json")
            print("💡 Diese Datei können Sie im Web-Interface laden!")

        # Hilfe anzeigen wenn keine Argumente
        if not any(
            [
                args.list,
                args.update,
                args.template,
                args.download_all,
                args.generate_web_config,
            ]
        ):
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        sys.exit(1)
    finally:
        try:
            manager.close_all_connections()
        except:
            pass


if __name__ == "__main__":
    main()

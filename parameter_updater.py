#!/usr/bin/env python3
"""
Symfony Parameters.yml Updater
Aktualisiert parameters.yml Dateien während Berechtigungen und Besitzverhältnisse erhalten bleiben.
"""

import os
import sys
import stat
import pwd
import grp
import shutil
import yaml
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

class ParameterUpdater:
    def __init__(self, log_level: str = 'INFO'):
        """Initialize the parameter updater with logging."""
        self.setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self, level: str):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('parameter_updater.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def get_file_permissions(self, file_path: str) -> Tuple[int, int, int]:
        """
        Ermittelt die aktuellen Berechtigungen, UID und GID einer Datei.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Tuple mit (permissions, uid, gid)
        """
        try:
            stat_info = os.stat(file_path)
            permissions = stat.S_IMODE(stat_info.st_mode)
            uid = stat_info.st_uid
            gid = stat_info.st_gid
            
            # Log current permissions for debugging
            user_name = pwd.getpwuid(uid).pw_name
            group_name = grp.getgrgid(gid).gr_name
            perm_str = oct(permissions)
            
            self.logger.info(f"Aktuelle Berechtigungen für {file_path}:")
            self.logger.info(f"  Berechtigungen: {perm_str}")
            self.logger.info(f"  Besitzer: {user_name} (UID: {uid})")
            self.logger.info(f"  Gruppe: {group_name} (GID: {gid})")
            
            return permissions, uid, gid
            
        except (OSError, KeyError) as e:
            self.logger.error(f"Fehler beim Ermitteln der Berechtigungen für {file_path}: {e}")
            raise
    
    def restore_file_permissions(self, file_path: str, permissions: int, uid: int, gid: int):
        """
        Stellt die ursprünglichen Berechtigungen und Besitzverhältnisse wieder her.
        
        Args:
            file_path: Pfad zur Datei
            permissions: Berechtigungen (oktal)
            uid: User ID
            gid: Group ID
        """
        try:
            # Besitzverhältnisse wiederherstellen
            os.chown(file_path, uid, gid)
            self.logger.info(f"Besitzverhältnisse wiederhergestellt: UID={uid}, GID={gid}")
            
            # Berechtigungen wiederherstellen
            os.chmod(file_path, permissions)
            self.logger.info(f"Berechtigungen wiederhergestellt: {oct(permissions)}")
            
        except OSError as e:
            self.logger.error(f"Fehler beim Wiederherstellen der Berechtigungen für {file_path}: {e}")
            raise
    
    def create_backup(self, file_path: str) -> str:
        """
        Erstellt ein Backup der ursprünglichen Datei.
        
        Args:
            file_path: Pfad zur ursprünglichen Datei
            
        Returns:
            Pfad zur Backup-Datei
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        
        try:
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Backup erstellt: {backup_path}")
            return backup_path
            
        except IOError as e:
            self.logger.error(f"Fehler beim Erstellen des Backups: {e}")
            raise
    
    def load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """
        Lädt eine YAML-Datei und gibt den Inhalt zurück.
        
        Args:
            file_path: Pfad zur YAML-Datei
            
        Returns:
            Dictionary mit dem YAML-Inhalt
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = yaml.safe_load(file)
                self.logger.info(f"YAML-Datei geladen: {file_path}")
                return content or {}
                
        except (IOError, yaml.YAMLError) as e:
            self.logger.error(f"Fehler beim Laden der YAML-Datei {file_path}: {e}")
            raise
    
    def save_yaml_file(self, file_path: str, content: Dict[str, Any]):
        """
        Speichert Inhalt in eine YAML-Datei mit korrekten Einrückungen.
        
        Args:
            file_path: Pfad zur YAML-Datei
            content: Dictionary mit dem Inhalt
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                # Symfony-spezifische YAML-Formatierung
                file.write("# This file is auto-generated during the composer install\n")
                yaml.dump(content, file, 
                         default_flow_style=False,
                         allow_unicode=True,
                         indent=4,
                         sort_keys=False)
                
            self.logger.info(f"YAML-Datei gespeichert: {file_path}")
            
        except IOError as e:
            self.logger.error(f"Fehler beim Speichern der YAML-Datei {file_path}: {e}")
            raise
    
    def update_parameters(self, file_path: str, new_parameters: Dict[str, Any], 
                         create_backup: bool = True) -> bool:
        """
        Aktualisiert eine parameters.yml Datei mit neuen Parametern.
        
        Args:
            file_path: Pfad zur parameters.yml Datei
            new_parameters: Dictionary mit neuen Parametern
            create_backup: Ob ein Backup erstellt werden soll
            
        Returns:
            True wenn erfolgreich, False bei Fehlern
        """
        try:
            # Prüfen ob Datei existiert
            if not os.path.exists(file_path):
                self.logger.error(f"Datei nicht gefunden: {file_path}")
                return False
            
            # Aktuelle Berechtigungen speichern
            permissions, uid, gid = self.get_file_permissions(file_path)
            
            # Backup erstellen
            if create_backup:
                self.create_backup(file_path)
            
            # Aktuelle Parameter laden
            current_content = self.load_yaml_file(file_path)
            
            # Parameter aktualisieren
            if 'parameters' not in current_content:
                current_content['parameters'] = {}
            
            # Neue Parameter hinzufügen/aktualisieren
            current_content['parameters'].update(new_parameters)
            
            # Datei speichern
            self.save_yaml_file(file_path, current_content)
            
            # Berechtigungen wiederherstellen
            self.restore_file_permissions(file_path, permissions, uid, gid)
            
            self.logger.info(f"Parameter erfolgreich aktualisiert in: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Parameter: {e}")
            return False
    
    def update_multiple_servers(self, server_configs: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Aktualisiert Parameter auf mehreren Servern.
        
        Args:
            server_configs: Dictionary mit Server-Konfigurationen
                Format: {
                    'server_name': {
                        'file_path': '/path/to/parameters.yml',
                        'parameters': {'param1': 'value1', ...}
                    }
                }
                
        Returns:
            Dictionary mit Ergebnissen pro Server
        """
        results = {}
        
        for server_name, config in server_configs.items():
            self.logger.info(f"Aktualisiere Server: {server_name}")
            
            file_path = config.get('file_path')
            parameters = config.get('parameters', {})
            
            if not file_path:
                self.logger.error(f"Kein file_path für Server {server_name} angegeben")
                results[server_name] = False
                continue
            
            results[server_name] = self.update_parameters(file_path, parameters)
        
        return results
    
    def validate_yaml_syntax(self, file_path: str) -> bool:
        """
        Validiert die YAML-Syntax einer Datei.
        
        Args:
            file_path: Pfad zur YAML-Datei
            
        Returns:
            True wenn gültig, False bei Syntax-Fehlern
        """
        try:
            self.load_yaml_file(file_path)
            self.logger.info(f"YAML-Syntax gültig: {file_path}")
            return True
            
        except yaml.YAMLError as e:
            self.logger.error(f"YAML-Syntax-Fehler in {file_path}: {e}")
            return False
    
    def generate_sample_config(self) -> Dict[str, Any]:
        """
        Generiert eine Beispiel-Konfiguration für Server-Updates.
        
        Returns:
            Dictionary mit Beispiel-Konfiguration
        """
        return {
            'production': {
                'file_path': '/var/www/symfony/app/config/parameters.yml',
                'parameters': {
                    'database_host': 'prod-db.example.com',
                    'database_port': 3306,
                    'database_name': 'symfony_prod',
                    'database_user': 'symfony_user',
                    'database_password': 'secure_password',
                    'mailer_transport': 'smtp',
                    'mailer_host': 'smtp.example.com',
                    'mailer_user': 'noreply@example.com',
                    'mailer_password': 'mail_password',
                    'secret': 'ThisTokenIsNotSoSecretChangeIt'
                }
            },
            'staging': {
                'file_path': '/var/www/symfony-staging/app/config/parameters.yml',
                'parameters': {
                    'database_host': 'staging-db.example.com',
                    'database_port': 3306,
                    'database_name': 'symfony_staging',
                    'database_user': 'symfony_staging',
                    'database_password': 'staging_password',
                    'mailer_transport': 'smtp',
                    'mailer_host': 'smtp.example.com',
                    'mailer_user': 'staging@example.com',
                    'mailer_password': 'staging_mail_password',
                    'secret': 'StagingSecretKey123'
                }
            }
        }


def main():
    """Hauptfunktion für Command-Line Interface."""
    parser = argparse.ArgumentParser(
        description='Symfony Parameters.yml Updater',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Einzelne Datei aktualisieren
  python parameter_updater.py --file /path/to/parameters.yml --param database_host=localhost --param database_port=3306
  
  # Konfigurationsdatei verwenden
  python parameter_updater.py --config server_config.yml
  
  # Beispiel-Konfiguration generieren
  python parameter_updater.py --generate-config
        """
    )
    
    parser.add_argument('--file', '-f', 
                       help='Pfad zur parameters.yml Datei')
    parser.add_argument('--param', '-p', action='append', 
                       help='Parameter im Format key=value (kann mehrfach verwendet werden)')
    parser.add_argument('--config', '-c', 
                       help='Pfad zur Konfigurationsdatei mit Server-Definitionen')
    parser.add_argument('--generate-config', action='store_true',
                       help='Generiert eine Beispiel-Konfigurationsdatei')
    parser.add_argument('--no-backup', action='store_true',
                       help='Kein Backup erstellen')
    parser.add_argument('--validate', '-v',
                       help='Validiert nur die YAML-Syntax einer Datei')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Log-Level (default: INFO)')
    
    args = parser.parse_args()
    
    updater = ParameterUpdater(args.log_level)
    
    # Beispiel-Konfiguration generieren
    if args.generate_config:
        config = updater.generate_sample_config()
        with open('server_config_example.yml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        print("Beispiel-Konfiguration wurde in 'server_config_example.yml' gespeichert.")
        return
    
    # YAML-Syntax validieren
    if args.validate:
        if updater.validate_yaml_syntax(args.validate):
            print(f"✅ YAML-Syntax ist gültig: {args.validate}")
            sys.exit(0)
        else:
            print(f"❌ YAML-Syntax-Fehler in: {args.validate}")
            sys.exit(1)
    
    # Konfigurationsdatei verwenden
    if args.config:
        try:
            with open(args.config, 'r') as f:
                server_configs = yaml.safe_load(f)
            
            results = updater.update_multiple_servers(server_configs)
            
            print("\n📊 Ergebnisse:")
            for server, success in results.items():
                status = "✅ Erfolgreich" if success else "❌ Fehler"
                print(f"  {server}: {status}")
                
        except Exception as e:
            print(f"❌ Fehler beim Laden der Konfigurationsdatei: {e}")
            sys.exit(1)
        return
    
    # Einzelne Datei aktualisieren
    if args.file and args.param:
        parameters = {}
        for param in args.param:
            if '=' not in param:
                print(f"❌ Ungültiges Parameter-Format: {param} (erwartet: key=value)")
                sys.exit(1)
            key, value = param.split('=', 1)
            parameters[key.strip()] = value.strip()
        
        success = updater.update_parameters(
            args.file, 
            parameters, 
            create_backup=not args.no_backup
        )
        
        if success:
            print(f"✅ Parameter erfolgreich aktualisiert: {args.file}")
        else:
            print(f"❌ Fehler beim Aktualisieren der Parameter: {args.file}")
            sys.exit(1)
        return
    
    # Hilfe anzeigen wenn keine gültigen Argumente
    parser.print_help()


if __name__ == '__main__':
    main() 
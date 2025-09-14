#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import tempfile
import re
import subprocess
import shutil
from pathlib import Path
from epg_config import epg_sources, EPG_OUTPUT_PATH

class EPGProcessor:
    def __init__(self):
        self.epg_sources = epg_sources
        # Obtener el directorio actual del script
        self.script_dir = Path(__file__).parent
        self.output_path = self.script_dir / EPG_OUTPUT_PATH
        self.github_url = f"https://raw.githubusercontent.com/frank1x/Pruebas1/main/{EPG_OUTPUT_PATH}"

    def download_epg(self, url: str) -> str:
        """Descargar archivo EPG comprimido"""
        print(f"Descargando EPG desde: {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.xml.gz') as temp_file:
                temp_file.write(response.content)
                return temp_file.name
        except Exception as e:
            print(f"Error descargando {url}: {e}")
            return None

    def decompress_epg(self, gz_file_path: str) -> str:
        """Descomprimir archivo EPG"""
        print("Descomprimiendo EPG...")
        try:
            with gzip.open(gz_file_path, 'rb') as f:
                xml_content = f.read().decode('utf-8')
            os.unlink(gz_file_path)
            return xml_content
        except Exception as e:
            print(f"Error descomprimiendo: {e}")
            return None

    def adjust_timeoffset(self, time_str: str, new_timeoffset: str) -> str:
        """Cambiar el timeoffset manteniendo la hora local"""
        try:
            match = re.match(r'(\d{14})\s+([+-]\d{4})', time_str)
            if match:
                dt_str, old_timeoffset = match.groups()
                return f"{dt_str} {new_timeoffset}"
            return f"{time_str} {new_timeoffset}"
        except Exception as e:
            print(f"Error ajustando timeoffset {time_str}: {e}")
            return time_str

    def process_single_epg(self, xml_content: str, new_timeoffset: str, selected_channels: list):
        """Procesar un solo EPG y extraer canales y programas filtrados"""
        print(f"Ajustando timeoffset a: {new_timeoffset}")

        if selected_channels:
            print(f"Filtrando {len(selected_channels)} canales seleccionados")
        else:
            print("Procesando TODOS los canales")

        channels = []
        programmes = []
        selected_channel_ids = set(selected_channels)

        try:
            root = ET.fromstring(xml_content)

            # Extraer canales filtrados
            for channel in root.findall('.//channel'):
                channel_id = channel.get('id')
                if not selected_channels or channel_id in selected_channel_ids:
                    channels.append(channel)

            # Extraer programas filtrados
            existing_channel_ids = {channel.get('id') for channel in channels}
            for programme in root.findall('.//programme'):
                channel_id = programme.get('channel')

                if not selected_channels or (channel_id in selected_channel_ids and channel_id in existing_channel_ids):
                    # Ajustar timeoffsets
                    for attr in ['start', 'stop']:
                        if programme.get(attr):
                            programme.set(attr, self.adjust_timeoffset(programme.get(attr), new_timeoffset))
                    programmes.append(programme)

            print(f"Extraídos: {len(channels)} canales, {len(programmes)} programas")
            return channels, programmes

        except Exception as e:
            print(f"Error procesando XML: {e}")
            return [], []

    def element_to_clean_string(self, element):
        """Convertir elemento XML a string limpio pero legible"""
        xml_str = ET.tostring(element, encoding='unicode')
        # Limpiar formato manteniendo estructura
        xml_str = re.sub(r'>\s+<', '><', xml_str)
        xml_str = re.sub(r'\s+', ' ', xml_str)
        return xml_str.strip()

    def save_epg(self, all_channels: list, all_programmes: list):
        """Guardar EPG procesado"""
        print(f"Guardando EPG procesado en: {self.output_path}")

        try:
            # Crear directorio si no existe
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<tv generator-info-name="EPG Processor">\n')

                # Escribir canales y programas
                for element in all_channels + all_programmes:
                    f.write(f"  {self.element_to_clean_string(element)}\n")

                f.write('</tv>')

            file_size = self.output_path.stat().st_size / (1024 * 1024)
            print(f"Guardado exitoso - Tamaño: {file_size:.2f} MB")

        except Exception as e:
            print(f"Error guardando archivo: {e}")
            raise

    def upload_to_github(self):
        """Subir el archivo generado a GitHub"""
        print("\n" + "=" * 60)
        print("SUBIR A GITHUB")
        print("=" * 60)

        try:
            if not shutil.which("git"):
                print("Git no está instalado")
                return False

            # Verificar que estamos en el directorio correcto del repositorio
            if not (self.script_dir / ".git").exists():
                print(f"Error: No se encuentra repositorio git en {self.script_dir}")
                return False

            # Cambiar al directorio del script (que es el repositorio)
            original_cwd = os.getcwd()
            os.chdir(self.script_dir)

            # Verificar si el archivo ha cambiado usando git diff
            diff_result = subprocess.run(["git", "diff", "--quiet", EPG_OUTPUT_PATH],
                                       capture_output=True, text=True)

            # git diff --quiet devuelve 0 si no hay cambios, 1 si hay cambios
            if diff_result.returncode == 0:
                print("No hay cambios en el archivo EPG - omitiendo commit")
                os.chdir(original_cwd)
                return True

            # Proceder con el commit y push
            commit_message = f"Actualizar EPG - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            commands = [
                ["git", "add", EPG_OUTPUT_PATH],
                ["git", "commit", "-m", commit_message],
                ["git", "push", "origin", "main"]
            ]

            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Error ejecutando {' '.join(cmd)}: {result.stderr}")
                    os.chdir(original_cwd)
                    return False

            print("✓ Archivo subido exitosamente a GitHub")
            print(f"✓ URL disponible: {self.github_url}")

            os.chdir(original_cwd)
            return True

        except Exception as e:
            print(f"Error subiendo a GitHub: {e}")
            return False

    def process_all(self):
        """Procesar todos los EPG configurados"""
        print("=" * 60)
        print("INICIANDO PROCESAMIENTO DE EPG")
        print("=" * 60)
        print(f"Directorio del script: {self.script_dir}")
        print(f"Archivo salida: {self.output_path}")
        print("=" * 60)

        all_channels = []
        all_programmes = []
        processed_sources = 0
        channel_ids = set()

        for epg_config in self.epg_sources:
            try:
                epg_url, timeoffset = epg_config[0], epg_config[1]
                selected_channels = epg_config[2] if len(epg_config) > 2 else []

                print(f"\n● Procesando: {epg_url}")
                print(f"  Timeoffset: {timeoffset}")

                # Descargar y procesar EPG
                gz_file = self.download_epg(epg_url)
                if not gz_file:
                    continue

                xml_content = self.decompress_epg(gz_file)
                if not xml_content:
                    continue

                channels, programmes = self.process_single_epg(xml_content, timeoffset, selected_channels)

                # Añadir canales únicos
                for channel in channels:
                    channel_id = channel.get('id')
                    if channel_id and channel_id not in channel_ids:
                        all_channels.append(channel)
                        channel_ids.add(channel_id)

                all_programmes.extend(programmes)
                processed_sources += 1
                print("  ✓ Procesado correctamente")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue

        if processed_sources > 0:
            self.save_epg(all_channels, all_programmes)

            print("\n" + "=" * 60)
            print("PROCESAMIENTO COMPLETADO")
            print("=" * 60)
            print(f"Fuentes procesadas: {processed_sources}")
            print(f"Canales únicos: {len(all_channels)}")
            print(f"Programas: {len(all_programmes)}")

            # Mostrar resumen
            print("\nResumen de ajustes aplicados:")
            for epg_config in self.epg_sources:
                epg_url, timeoffset = epg_config[0], epg_config[1]
                selected_channels = epg_config[2] if len(epg_config) > 2 else []
                status = f"Filtrado: {len(selected_channels)} canales" if selected_channels else "Todos los canales"
                print(f"  • {epg_url}: {timeoffset} ({status})")

            # Subir a GitHub
            self.upload_to_github()
            print("=" * 60)

        else:
            print("\n✗ Error: No se pudo procesar ninguna fuente EPG")

def main():
    processor = EPGProcessor()
    processor.process_all()

if __name__ == "__main__":
    main()

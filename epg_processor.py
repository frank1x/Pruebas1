#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
import tempfile
import re
import subprocess
import shutil
from epg_config import epg_sources, OUTPUT_FILENAME  # Importar configuración

class EPGProcessor:
    def __init__(self):
        # CONFIGURACIÓN DESDE ARCHIVO EXTERNO
        self.epg_sources = epg_sources
        self.output_filename = OUTPUT_FILENAME

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
            else:
                return f"{time_str} {new_timeoffset}"
        except Exception as e:
            print(f"Error ajustando timeoffset {time_str}: {e}")
            return time_str

    def process_single_epg(self, xml_content: str, new_timeoffset: str, selected_channels: list):
        """Procesar un solo EPG y extraer canales y programas filtrados"""
        print(f"Ajustando timeoffset a: {new_timeoffset}")

        if selected_channels:
            print(f"Filtrando canales: {len(selected_channels)} canales seleccionados")
        else:
            print("Procesando TODOS los canales")

        channels = []
        programmes = []
        selected_channel_ids = set(selected_channels)

        try:
            # Parsear el XML
            root = ET.fromstring(xml_content)

            # Extraer canales (solo los seleccionados si hay filtro)
            for channel in root.findall('.//channel'):
                channel_id = channel.get('id')
                if not selected_channels or channel_id in selected_channel_ids:
                    channels.append(channel)

            # Crear set de IDs de canales que realmente existen en el EPG
            existing_channel_ids = {channel.get('id') for channel in channels}

            # Extraer y ajustar programas (solo de los canales seleccionados)
            for programme in root.findall('.//programme'):
                channel_id = programme.get('channel')

                # Si no hay filtro o el canal está en los seleccionados Y existe
                if not selected_channels or (channel_id in selected_channel_ids and channel_id in existing_channel_ids):
                    # Ajustar timeoffsets
                    start = programme.get('start')
                    stop = programme.get('stop')

                    if start:
                        programme.set('start', self.adjust_timeoffset(start, new_timeoffset))
                    if stop:
                        programme.set('stop', self.adjust_timeoffset(stop, new_timeoffset))

                    programmes.append(programme)

            print(f"Extraídos: {len(channels)} canales, {len(programmes)} programas")

        except Exception as e:
            print(f"Error procesando XML: {e}")

        return channels, programmes

    def element_to_clean_string(self, element):
        """Convertir elemento XML a string limpio pero legible"""
        # Convertir a string
        xml_str = ET.tostring(element, encoding='unicode')

        # Eliminar solo saltos de línea y tabs dentro del elemento, pero mantener la estructura
        xml_str = xml_str.replace('\n', ' ')
        xml_str = xml_str.replace('\t', ' ')

        # Limpiar espacios múltiples
        xml_str = re.sub(r'\s+', ' ', xml_str)

        # Asegurar que no haya espacios antes de >
        xml_str = re.sub(r'\s+>', '>', xml_str)

        return xml_str.strip()

    def save_epg(self, all_channels: list, all_programmes: list, output_file: str):
        """Guardar EPG procesado con estructura correcta"""
        print(f"Guardando EPG procesado en: {output_file}")

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<tv generator-info-name="EPG Processor" generator-info-url="none">\n')

                # Escribir todos los canales primero
                for channel in all_channels:
                    channel_str = self.element_to_clean_string(channel)
                    f.write(f"  {channel_str}\n")

                # Escribir todos los programas
                for programme in all_programmes:
                    programme_str = self.element_to_clean_string(programme)
                    f.write(f"  {programme_str}\n")

                f.write('</tv>')

            print("Guardado exitoso")
            file_size = os.path.getsize(output_file) / (1024 * 1024)
            print(f"Tamaño del archivo: {file_size:.2f} MB")

        except Exception as e:
            print(f"Error guardando archivo: {e}")

    def upload_to_github(self):
        """Subir el archivo generado a GitHub"""
        print("\n" + "=" * 60)
        print("SUBIR A GITHUB")
        print("=" * 60)

        try:
            # Verificar si git está instalado
            if not shutil.which("git"):
                print("Git no está instalado. No se puede subir a GitHub.")
                return False

            # Comandos para subir a GitHub
            commands = [
                ["git", "add", self.output_filename],
                ["git", "commit", "-m", f"Actualizar EPG automático - {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
                ["git", "push", "origin", "main"]
            ]

            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Error ejecutando {' '.join(cmd)}: {result.stderr}")
                    return False

            print("✓ Archivo subido exitosamente a GitHub")
            print(f"✓ URL disponible en: https://raw.githubusercontent.com/frank1x/Pruebas1/refs/heads/main/{self.output_filename}")
            return True

        except Exception as e:
            print(f"Error subiendo a GitHub: {e}")
            return False

    def process_all(self):
        """Procesar todos los EPG configurados"""
        print("=" * 60)
        print("INICIANDO PROCESAMIENTO DE EPG")
        print("=" * 60)
        print("NOTA: Se mantienen las horas locales, solo se cambia el timeoffset")
        print("=" * 60)

        all_channels = []
        all_programmes = []
        processed_sources = 0
        channel_ids = set()  # Para evitar duplicados

        for epg_config in self.epg_sources:
            try:
                epg_url = epg_config[0]
                timeoffset = epg_config[1]
                selected_channels = epg_config[2] if len(epg_config) > 2 else []

                print(f"\n● Procesando: {epg_url}")
                print(f"  Nuevo timeoffset: {timeoffset}")

                # Descargar EPG
                gz_file = self.download_epg(epg_url)
                if not gz_file:
                    continue

                # Descomprimir
                xml_content = self.decompress_epg(gz_file)
                if not xml_content:
                    continue

                # Procesar este EPG individualmente con filtrado
                channels, programmes = self.process_single_epg(xml_content, timeoffset, selected_channels)

                # Añadir canales únicos
                for channel in channels:
                    channel_id = channel.get('id')
                    if channel_id and channel_id not in channel_ids:
                        all_channels.append(channel)
                        channel_ids.add(channel_id)

                # Añadir todos los programas
                all_programmes.extend(programmes)

                processed_sources += 1
                print(f"  ✓ Fuente procesada correctamente")

            except Exception as e:
                print(f"  ✗ Error procesando EPG: {e}")
                continue

        if processed_sources > 0:
            # Guardar el EPG combinado final
            self.save_epg(all_channels, all_programmes, self.output_filename)

            print("\n" + "=" * 60)
            print("PROCESAMIENTO COMPLETADO")
            print("=" * 60)
            print(f"✓ {processed_sources} fuentes procesadas")
            print(f"✓ {len(all_channels)} canales únicos")
            print(f"✓ {len(all_programmes)} programas")

            # Mostrar resumen de ajustes aplicados
            print("\nResumen de timeoffsets y filtros aplicados:")
            for epg_config in self.epg_sources:
                epg_url = epg_config[0]
                timeoffset = epg_config[1]
                selected_channels = epg_config[2] if len(epg_config) > 2 else []

                if selected_channels:
                    print(f"  • {epg_url}: {timeoffset} (Filtrado: {len(selected_channels)} canales)")
                else:
                    print(f"  • {epg_url}: {timeoffset} (Todos los canales)")

            print(f"\n✓ Archivo final: {self.output_filename}")

            # Subir a GitHub
            self.upload_to_github()

            print("=" * 60)

        else:
            print("\n✗ Error: No se pudo procesar ninguna fuente EPG")
            print("Verifica las URLs y tu conexión a internet")

def main():
    processor = EPGProcessor()
    processor.process_all()

if __name__ == "__main__":
    main()

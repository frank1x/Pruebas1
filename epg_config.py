# epg_config.py
# CONFIGURACIÓN DE FUENTES EPG Y CANALES A PROCESAR

# Ruta del archivo EPG (relativa al repositorio)
EPG_OUTPUT_PATH = "epg/epg_all.xml"

# Formato: [url, nuevo_timeoffset, [lista_de_ids_de_canales]]
# Si la lista de canales está vacía [], se procesan TODOS los canales
epg_sources = [
    [
        "https://epgshare01.online/epgshare01/epg_ripper_DIRECTVSPORTS1.xml.gz",
        "+0000",
        ["DSPORTS.(ARG).dtvsp"]  # Solo procesar este canal
    ],
    [
        "https://epg.jesmann.com/iptv/Colombia.xml.gz",
        "+0000",
        ["SonyMovies(SONYML).co", "CaracolTVCanal1HD(CARAHD).co"]  # Solo procesar este canal
    ],
    [
        "https://epg.jesmann.com/iptv/Chile.xml.gz",
        "+0000",
        ["ETCTV(ETCHILE).cl"]  # Solo procesar este canal
    ],
    [
        "https://epgshare01.online/epgshare01/epg_ripper_PE1.xml.gz",
        "+0000",
        ["DISCOVERY.HD.(DiscoveryHD).pe"]  # Solo procesar este canal
    ],
]

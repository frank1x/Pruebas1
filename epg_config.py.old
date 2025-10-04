# epg_config.py
# CONFIGURACIÓN DE FUENTES EPG Y CANALES A PROCESAR

# Ruta del archivo EPG (relativa al repositorio)
EPG_OUTPUT_PATH = "epg/epg_all.xml"

# Formato: [url, nuevo_timeoffset, [lista_de_ids_de_canales]]
# Si la lista de canales está vacía [], se procesan TODOS los canales
epg_sources = [
    [
        "https://epgshare01.online/epgshare01/epg_ripper_AR1.xml.gz", 
        "-0600",
        ["Canal.Warner.TV.(Argentina).ar", "Canal.Sony.(Argentina).ar"]  # Solo procesar este canal
    ],
    [
        "https://epgshare01.online/epgshare01/epg_ripper_DIRECTVSPORTS1.xml.gz",
        "+0000",
        ["DSPORTS.(ARG).dtvsp"]  # Solo procesar este canal
    ],
    [
        "https://www.open-epg.com/files/argentina3.xml.gz",
        "+0000",
        ["SONY MOVIES.ar"]  # Solo procesar este canal
    ],
    [
        "https://www.open-epg.com/files/peru1.xml.gz",
        "+0000",
        ["TyC Sports.pe"]  # Solo procesar este canal
    ],
    [
        "https://www.open-epg.com/files/peru2.xml.gz",
        "+0000",
        ["PANAMERICANA TELEVISION HD.pe", "TV PERU HD.pe", "ATV HD.pe", "GLOBAL TV.pe", "M DEPORTES.pe"]  # Solo procesar este canal
    ],
]

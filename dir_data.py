# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace, no-name-in-module, unused-import

"""Save & update directories data
"""

import sys, os, configparser
import minecraft_manager as mm


LAUNCHER_DIRS = {
    "launcher":        mm.MC_DIR + "/.mglauncher/",
    "player_data":     mm.MC_DIR + "/.mglauncher/player_data.ini",
    "vlaunchers_data": mm.MC_DIR + "/.mglauncher/vlaunchers_data.json",
    "vlaunchers":      mm.MC_DIR + "/.mglauncher/vlaunchers/",           # Папка с сохраненными сборками
    "mc_mods":         mm.MC_DIR + "/mods/",
    "mc_old_mods":     mm.MC_DIR + "/mods/old/",
    "mc_versions":     mm.MC_DIR + "/versions/"
}

print(sys.path)
PATH_NUM = 2

if os.path.exists(LAUNCHER_DIRS["player_data"]):
    config = configparser.ConfigParser()
    config.read(LAUNCHER_DIRS["player_data"])
    
    try: 
        PATH_NUM = int(config["Player"]["PATH_NUM"])
    except KeyError:
        PATH_NUM = 0


CSS_STYLESHEET = sys.path[PATH_NUM] + "/assets/main_style.css"

INITAL_DIRS = {      # Если директории нет в папке mc то отсюда будут брать данные
    "player_data":     sys.path[PATH_NUM] + "/inital/player_data.ini",
    "vlaunchers_data": sys.path[PATH_NUM] + "/inital/vlaunchers_data.json"
}


if not os.path.exists(INITAL_DIRS["player_data"]):
    PATH_NUM = -1
    while not os.path.exists(INITAL_DIRS["player_data"]): # перебираем PATH индефикаторы пока не найдем нужный
        PATH_NUM += 1
        
        print(f"PATH ERROR. RECALCULATING. PATH_NUM: {PATH_NUM}")
        
        CSS_STYLESHEET = sys.path[PATH_NUM] + "/assets/main_style.css"
        INITAL_DIRS = {      # Если директории нет в папке mc то отсюда будут брать данные
            "player_data":     sys.path[PATH_NUM] + "/inital/player_data.ini",
            "vlaunchers_data": sys.path[PATH_NUM] + "/inital/vlaunchers_data.json"
        }


ASSETS_DIRS = {
    "microsoft_icon": sys.path[PATH_NUM] + "/assets/microsoft.png"
}

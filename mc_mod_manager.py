# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace

import io
import re
from shutil import Error
import zipfile, tomli, json

MODS_DATA_PATH = {      # расположение инфы о моде (имени) внутри .jar файла
    "forge": "META-INF/mods.toml",
    "fabric": "fabric.mod.json"
}

MODS_DATA_STRUCT = {
    "forge": {
        "id":           "modId",
        "version":      "version",
        "name":         "displayName",
        "url":          "displayURL",
        "logo":         "logoFile",
        "credits":      "credits",
        "authors":      "authors",
        "description":  "description"
    },
    
    "fabric": {
        "id":           "id",
        "version":      "version",
        "name":         "name",
        "url":          "contact",  # ["homepage"]
        "logo":         "icon",
        "credits":      "contributors",
        "authors":      "authors",  # ", ".join
        "description":  "description"
    }
}



class ModData:
    """Class that contains data of mod.
    
    Possible values: id, launcher_type, version, name, url, authors, description
    """
    
    def __init__(self, path:str, _id:str, launcher_type:str, version:str, name:str, url:str, authors:str, description:str):
        self.path = path
        self.id = _id
        self.launcher_type = launcher_type
        self.version = version
        self.name = name
        self.url = url
        self.authors = authors
        self.description = description



def get_mod_data(path:str) -> ModData|None:
    """Reading mod data from file.

    Returns:
        ModData|None
    """    
    
    with zipfile.ZipFile(path, 'r') as mod: # распаковываем файл
        try:
            try:
                mod_info = mod.read(MODS_DATA_PATH["forge"])

                mod_info_file = io.BytesIO(mod_info)

                toml = tomli.load(mod_info_file)  # чтение .toml файла

                non_structured_data = toml["mods"][0]
                
                data = ModData(path, \
                                non_structured_data.get(MODS_DATA_STRUCT['forge']['id'], "id"), \
                                "forge", \
                                non_structured_data.get(MODS_DATA_STRUCT['forge']['version'], "1.0"), \
                                non_structured_data.get(MODS_DATA_STRUCT['forge']['name'], "name"), \
                                non_structured_data.get(MODS_DATA_STRUCT['forge']['url'], ""), \
                                non_structured_data.get(MODS_DATA_STRUCT['forge']['authors'], "me"), \
                                non_structured_data.get(MODS_DATA_STRUCT['forge']['description'], ""))
            except KeyError:
                with mod.open(MODS_DATA_PATH["fabric"]) as mod_json:
                    data = json.load(mod_json)
                    non_structured_data = data
                    
                    authors = non_structured_data.get(MODS_DATA_STRUCT['fabric']['authors'], ["me"])
                    
                    if len(authors) > 0:
                        if isinstance(authors[0], dict):
                            authors = authors[0]['name']
                        
                    data = ModData(path, \
                                non_structured_data.get(MODS_DATA_STRUCT['fabric']['id'], "id"), \
                                "fabric", \
                                non_structured_data.get(MODS_DATA_STRUCT['fabric']['version'], "1.0"), \
                                non_structured_data.get(MODS_DATA_STRUCT['fabric']['name'], "name"), \
                                non_structured_data.get(MODS_DATA_STRUCT['fabric']['url'], {"homepage":"no url :("})["homepage"], \
                                ", ".join(authors), \
                                non_structured_data.get(MODS_DATA_STRUCT['fabric']['description'], ""))
            
            return data
        except Error as err:
            print(f"Could not load mod [ {path} ] configuration file. Error: {err.args}")
            return None

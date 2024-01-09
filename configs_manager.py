# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace, no-name-in-module, unused-import

import configparser, json


#=========================================================           =========================================================
#========================================================= Constants =========================================================
#=========================================================           =========================================================

CONFIGS_STRUCTURES = {
    "vlaunchers": { 
        "vlaunchers": []
    },
    
    "player": {
        "Player": {
            "username": "player",
            "PATH_NUM": 2
        },
        "Mojang": {
            "have_licence": 0,
            "access_code": "",
            "uuid": ""
        },
        "Java": {
            "args": ""
        }
    }
}

""" files structures 

vlaunchers_data.json:
    "name" {
        "name" : "vlauncher name",       # имя в папке vlaunchers
        "version": "version to start",   # если при fabric обычная версия, то парсит список установленных
        "type: "forge/fabric"            
    }

player_data.ini:
    [Player]
    username = player
    PATH_NUM = 2      # автоматически обновляется при возникновении ошибки

    [Mojang]
    have_licence = 0 
    access_code =     # при запуске если have_licence == 1 обновляется

    [Java]
    args =            # аргументы запуска mc

"""


#=========================================================           =========================================================
#========================================================= Functions =========================================================
#=========================================================           =========================================================

def read_config(path):
    type = path.split('.')[-1]
    
    if type == 'ini':
        config = configparser.ConfigParser()
        config.read(path)
        
        return config
    if type == 'json':
        with open(path, 'r') as file:
            try:
                file_data = json.load(file)

                return file_data
            except json.decoder.JSONDecodeError: # если файл пустой
                return {}
            
def write_config(config_path:str, data_path:str, data, write_method="change"):
    config = read_config(config_path)
    type = config_path.split('.')[-1]
    
    path = data_path.split('.')
    
    
    current_part = config
    for i in path:
        if i == path[-1]: 
            break
        
        if isinstance(current_part, list):
            current_part = current_part[int(i)]
            
            continue
        
        if i in current_part: # type: ignore
            current_part = current_part[i] # type: ignore
        else:
            print(f"Invalid config path: {i} in {path}") 
            return
    
    if write_method == "change" or type == 'ini':
        current_part[path[-1]] = data # type: ignore
    
    if type == 'ini':
        if isinstance(config, configparser.ConfigParser):
            with open(config_path, 'w') as configfile:    # save
                config.write(configfile)
        else:
            print(f"Invalid config class: {config.__class__.__name__} must be a configparser.ConfigParser()")
    if type == 'json':
        if write_method != "change":
            if write_method == "append.list":
                current_part[path[-1]].append(data) # type: ignore
            elif write_method == "append.dict":
                current_part[path[-1]] = data # type: ignore
            else:
                print("Unknown write method")
                return

        with open(config_path, 'w') as file:
            file.seek(0)
            json.dump(config, file, indent = 4)
                

#=========================================================               =========================================================
#========================================================= ConfigManager =========================================================
#=========================================================               =========================================================

class ConfigManager():
    def __init__(self, **dirs):
        self.config_dirs = {
            "player":     dirs["player"],
            "vlaunchers": dirs["vlaunchers"]
        }
        
        self.loaded_configs = {}
        
        self.update_configs()
    
    
    
    def get_config(self, _path:str):
        self.update_configs()
        
        path = _path.split('.')
        
        current_part = self.loaded_configs
        for i in path:
            if i in current_part: # type: ignore
                current_part = current_part[i] # type: ignore
            else:
                print(f"Invalid config path: {i} in {path}") 
                return None
        
        return current_part
    
    def update_configs(self):
        self.loaded_configs = {
            "player":     read_config(self.config_dirs["player"]),
            "vlaunchers": read_config(self.config_dirs["vlaunchers"])
        }
    
    def update_config_data(self, path, data, write_type="change", update_save=False):
        write_config(self.config_dirs[path.split(".")[0]], path[path.find(".")+1:], data, write_type) # type: ignore
        
        if update_save:
            self.update_configs()

if __name__ == "__main__":
    write_config("C:\\Users\\MakarTs\\Documents\\Makar\\Programmming\\Python\\Minecraft Launcher\\inital\\player_data.ini", "Mojang.uuid", "")
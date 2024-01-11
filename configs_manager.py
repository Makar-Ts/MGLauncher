# pylint: disable=line-too-long, consider-using-dict-items, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace, no-name-in-module, unused-import
"""Module for easily reading, writing and configuring configs
"""

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


#=========================================================                      =========================================================
#========================================================= Data Storage Classes =========================================================
#=========================================================                      =========================================================

class Config:
    """Storage class for configuration file.
    """    
    
    def __init__(self, path:str, check_paths:dict):
        self.path = path
        self.check_paths = check_paths


#=========================================================           =========================================================
#========================================================= Functions =========================================================
#=========================================================           =========================================================

def read_config(path):
    """Read in a config file and return it as a dict .

    Args:
        path (str): [path to config file]

    Returns:
        ConfigParser | dict
    """    
    
    type = path.split('.')[-1]
    
    match type:
        case 'ini':
            config = configparser.ConfigParser()
            config.read(path)
            
            return config
        case 'json':
            with open(path, 'r') as file:
                try:
                    file_data = json.load(file)

                    return file_data
                except json.decoder.JSONDecodeError: # если файл пустой
                    return {}
            
def write_config(config_path:str, data_path:str, data, write_method="change"):
    """Write data to the config.

    Args:
        config_path (str): [path to config file]
        data_path (str): [path to data in config file]
        data (Any): [data to write to config file]
        write_method (str, optional): [change for ini and json
                                       append.list (json only) add data to path list
                                       append.dict (json only) add data to dict]. Defaults to "change".
    """    
    
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
    
    match type:
        case 'ini':
            if isinstance(config, configparser.ConfigParser):
                with open(config_path, 'w') as configfile:    # save
                    config.write(configfile)
            else:
                print(f"Invalid config class: {config.__class__.__name__} must be a configparser.ConfigParser()")
        case 'json':
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
        case _:
            print(f"Invalid config type: {type}")
                

#=========================================================               =========================================================
#========================================================= ConfigManager =========================================================
#=========================================================               =========================================================

class ConfigManager():
    """Class for confruge configs easily.
    """    
    
    def __init__(self, **dirs):
        self.configs = dirs.copy()
        
        self.loaded_configs = {}
        
        self.update_configs()
    
    def get_config(self, _path:str, update_configs=True):
        """Get a config value from a path.

        Args:
            _path (str): [path to value]
            update_configs (bool, optional): [auto-update loaded configs before get value]. Defaults to True.

        Returns:
            [Any]: [value]
        """        
        
        if update_configs:
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
        """Update loaded configs
        """        
        
        for i in self.configs.keys():
            self.loaded_configs[i] = read_config(self.configs[i].path)
    
    def update_config_data(self, path, data, write_type="change", update_save=False):
        """Update config data

        Args:
            path (str): [path to value]
            data (Any): [value data]
            write_type (str, optional): [change for ini and json
                                         append.list (json only) add data to path list
                                         append.dict (json only) add data to dict]. Defaults to "change".
            update_save (bool, optional): [description]. Defaults to False.
        """        
        
        if isinstance(data, int) or isinstance(data, float):
            data = str(data)
        
        write_config(self.configs[path.split(".")[0]].path, path[path.find(".")+1:], data, write_type) # type: ignore
        
        if update_save:
            self.update_configs()
    
    def check_config_struct(self, config):
        """Check struct of the config (ini only).

        Args:
            config (str): [config's name]
        """        
        
        _type = self.configs[config].path.split(".")[-1]
        
        if _type == "ini":
            for i in self.configs[config].check_paths.keys():
                path = f"{config}.{i}"
                
                result = self.get_config(path, False)
                
                if result is None:
                    if self.configs[config].check_paths[i] == "__dir__":
                        self.update_config_data(path, {})
                    else:
                        self.update_config_data(path, self.configs[config].check_paths[i])
        
                
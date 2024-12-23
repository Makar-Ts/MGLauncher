# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace

"""This module is used to create a version object that can be used to recreate the versions of the Minecraft .
"""

from uuid import uuid1
from typing import Callable
import subprocess
import minecraft_launcher_lib as mllib


MC_DIR = mllib.utils.get_minecraft_directory()
FABRIC_EARLIEST_VERSION = "1.14"
# директория с которой не будет показываться версии mc при выборке Fabric версий

def get_installed_versions() -> list[list[str]]:
    """Returns a list of installed versions .

    Returns:
        list[list[str, str]]: [id, type]
    """
    
    unsorted_list = mllib.utils.get_installed_versions(MC_DIR)
    return list(map(lambda x: [x['id'], x['type']], unsorted_list)) 
    # id - версия mc, а type - vanilla или modded (пока что не нужно)

def get_all_versions(_type = 0.0):
    """Return a list of all versions of minecraft

    Args:
        _type (int, optional): [0 for vanilla, 1 for forge, 2 for fabric]. Defaults to 0.

    Returns:
        list[list[str, str]]: [id, type]
    """    
    
    match _type:
        case 0:
            unsorted_list = mllib.utils.get_version_list()
            return list(map(lambda x: [x['id'], x['type']], unsorted_list))
        case 1:
            unsorted_list = mllib.forge.list_forge_versions()
            return list(map(lambda x: [x, ''], unsorted_list))
        case 1.1:
            unsorted_list = mllib.forge.list_forge_versions()
            output = list()
            
            data = unsorted_list[0].split('-')
            output.append({"major": data[0], "minor": [data[1]]})
            current_index = 0
            
            for i in unsorted_list:
                data = i.split('-')
                
                if output[current_index]["major"] != data[0]:
                    output.append({"major": data[0], "minor": [data[1]]})
                    
                    current_index += 1
                    
                    continue
                
                output[current_index]["minor"].append(data[1])
            
            return output
        case 2:
            unsorted_list = mllib.utils.get_version_list()
            output = []
            
            for i in unsorted_list:
                if i['id'].find('-') != -1:
                    continue                    # если пре версия - 1.20.4-pre3 и т.д.
                if i['id'][2] == 'w' and i['id'][5].isalpha():
                    continue                    # если снапшот 23w07a и т.д.
                
                output.append([i['id'], i['type']])
                
                if i['id'] == FABRIC_EARLIEST_VERSION:
                    return output
            
            return output
    


class MinecraftVersionLauncher:
    """Class method that creates a new Minecraft versionLauncher .
    """
    
    def __init__(self, username: str, version: str, _type="vanilla", access_token="", uuid=""):
        self.username = username
        self.version = version
        self.type = _type
        self.access_token = access_token
        self.uuid = uuid
        
        self.download_progress = {
            'status': "not started",
            'current_max': 0,
            'progress': 0
        }
        
        print(f"Minecraft version launcher set. Version: {version}")
        
    def check_minecraft_version(self):
        """Check if the mc version is valid.

        Returns:
            [bool]: []
        """        
        
        match self.type:
            case "vanilla":
                installed_versions = get_all_versions()
                
                for i in installed_versions:
                    if i[0] == self.version:
                        break
                else:         
                    return False
                
                return True
            case "forge":
                if mllib.forge.is_forge_version_valid(self.version):
                    return True
                
                forge_version = mllib.forge.find_forge_version(self.version)
                if forge_version is not None:
                    self.version = forge_version
                    return True
                
                return False
            case "fabric":
                return mllib.fabric.is_minecraft_version_supported(self.version)
        
    def install_minecraft_version(self, callback:dict[str, Callable], _type=0):
        """Install the Minecraft version.

        Args:
            callback (dict[str, Callable]): [download progress callback]
                struct: "setStatus":   function(str),
                        "setProgress": function(int),
                        "setMax":      function(int)
            _type (int, optional): [0 for vanilla, 1 for forge, 2 for fabric]. Defaults to 0.
        """
        
        if callback is None:
            callback = {
                "setStatus": self.set_download_status,
                "setProgress": self.set_download_progress,
                "setMax": self.set_download_max
            }
        
        match _type:
            case 0:
                mllib.install.install_minecraft_version(versionid=self.version, \
                                                minecraft_directory=MC_DIR, \
                                                callback=callback)
            case 1:
                if mllib.forge.supports_automatic_install(self.version):
                    mllib.forge.install_forge_version(versionid=self.version, \
                                                    path=MC_DIR, \
                                                    callback=callback)
                else:
                    mllib.forge.run_forge_installer(self.version)
            case 2:
                mllib.fabric.install_fabric(minecraft_version=self.version, \
                                            minecraft_directory=MC_DIR, \
                                            callback=callback)
    
    def start_minecraft_version(self, jvm_args: str=""):
        """Starting the mc version
        Recommend run the check_minecraft_version function before starting
        
        Args:
            jvm_args (str|list[str], optional): [jvmArguments]. Defaults to "".
        """
        
        args_splitted = jvm_args.split(" ")
        
        print("args:"+str(args_splitted))
        
        args_accepted = list()
        for i in args_splitted:
            if i != "" and i != " ": 
                args_accepted.append(i)
        
        options = {
            'username': self.username,
            'uuid': (self.uuid == "")*str(uuid1())+self.uuid,
            'token': self.access_token,                # оставлять пустым (при пиратке)
            "jvmArguments": args_accepted
        }

        subprocess.call(mllib.command.get_minecraft_command(version=self.version, \
                                                            minecraft_directory=MC_DIR, \
                                                            options=options))
    
    
    def set_download_status(self, status: str):
        """Set the download progress status.

        Args:
            status (str)
        """ 
        self.download_progress['status'] = status
        
    def set_download_progress(self, progress: int):
        """Set the download progress.

        Args:
            progress (int)
        """
        if self.download_progress['current_max'] != 0:
            self.download_progress['progress'] = progress
            
    def set_download_max(self, new_max: int):
        """Set the download progress maximum.

        Args:
            new_max (int)
        """
        self.download_progress['current_max'] = new_max
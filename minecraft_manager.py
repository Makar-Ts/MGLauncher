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

def get_all_versions(_type = 0):
    """Return a list of all versions of minecraft

    Args:
        _type (int, optional): [0 for vanilla, 1 for forge, 2 for fabric]. Defaults to 0.

    Returns:
        list[list[str, str]]: [id, type]
    """    
    
    if _type == 1:
        unsorted_list = mllib.forge.list_forge_versions()
        return list(map(lambda x: [x, ''], unsorted_list))
    elif _type == 2:
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
    else:
        unsorted_list = mllib.utils.get_version_list()
        return list(map(lambda x: [x['id'], x['type']], unsorted_list))
    


class MinecraftVersionLauncher:
    """Class method that creates a new Minecraft versionLauncher .
    """
    
    def __init__(self, username: str, version: str, _type="vanilla"):
        self.username = username
        self.version = version
        self.type = _type
        
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
        
        if self.type == "vanilla":
            installed_versions = get_all_versions()
            
            for i in installed_versions:
                if i[0] == self.version:
                    break
            else:         
                return False
            
            return True
        if self.type == "forge":
            if mllib.forge.is_forge_version_valid(self.version):
                return True
            
            forge_version = mllib.forge.find_forge_version(self.version)
            if forge_version is not None:
                self.version = forge_version
                return True
            
            return False
        if self.type == "fabric":
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
        
        if _type == 0:
            mllib.install.install_minecraft_version(versionid=self.version, \
                                            minecraft_directory=MC_DIR, \
                                            callback=callback)
        elif _type == 1:
            if mllib.forge.supports_automatic_install(self.version):
                mllib.forge.install_forge_version(versionid=self.version, \
                                                  path=MC_DIR, \
                                                  callback=callback)
            else:
                mllib.forge.run_forge_installer(self.version)
        elif _type == 2:
            mllib.fabric.install_fabric(minecraft_version=self.version, \
                                        minecraft_directory=MC_DIR, \
                                        callback=callback)
    
    def start_minecraft_version(self):
        """Starting the mc version
        Recommend run the check_minecraft_version function before starting
        """
        
        options = {
            'username': self.username,
            'uuid': str(uuid1()),
            'token': ''                 # оставлять пустым (при пиратке)
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
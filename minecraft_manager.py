import minecraft_launcher_lib as mllib
import subprocess
from uuid import uuid1


current_max = 0
MC_DIR = mllib.utils.get_minecraft_directory()
FABRIC_EARLIEST_VERSION = "1.14"
    
def get_installed_versions() -> list[list[str]]:
    unsorted_list = mllib.utils.get_installed_versions(MC_DIR)
    
    return list(map(lambda x: [x['id'], x['type']], unsorted_list))

def get_all_versions(_type = 0):
    if (_type == 1):
        unsorted_list = mllib.forge.list_forge_versions()
        return list(map(lambda x: [x, ''], unsorted_list))
    elif (_type == 2):
        unsorted_list = mllib.utils.get_version_list()
        output = []
        
        for i in unsorted_list:
            if (i['id'].find('-') != -1): continue
            if (i['id'][2] == 'w' and i['id'][5].isalpha()): continue
            
            output.append([i['id'], i['type']])
            
            if (i['id'] == FABRIC_EARLIEST_VERSION): return output
        
        return output
    else:
        unsorted_list = mllib.utils.get_version_list()
        return list(map(lambda x: [x['id'], x['type']], unsorted_list))
    


class MinecraftVersionLauncher:
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
        if (self.type == "vanilla"):
            installed_versions = get_all_versions()
            
            for i in installed_versions:
                if (i[0] == self.version):
                    break
            else:                
                return False
            
            return True
        if (self.type == "forge"):
            if (mllib.forge.is_forge_version_valid(self.version)):
                return True
            
            forge_version = mllib.forge.find_forge_version(self.version)
            if (forge_version != None):
                self.version = forge_version
                return True
            
            return False
        if (self.type == "fabric"):
            return mllib.fabric.is_minecraft_version_supported(self.version)
        
    def install_minecraft_version(self, callback={}, _type=0):
        if (callback == {}): 
            callback = {
                "setStatus": self.set_download_status,
                "setProgress": self.set_download_progress,
                "setMax": self.set_download_max
            }
        
        if (_type == 0):
            mllib.install.install_minecraft_version(versionid=self.version, \
                                            minecraft_directory=MC_DIR, \
                                            callback=callback)
        elif (_type == 1):
            if (mllib.forge.supports_automatic_install(self.version)):
                mllib.forge.install_forge_version(versionid=self.version, \
                                                  path=MC_DIR, \
                                                  callback=callback)
            else:
                mllib.forge.run_forge_installer(self.version)
        elif (_type == 2):
            mllib.fabric.install_fabric(minecraft_version=self.version, \
                                        minecraft_directory=MC_DIR, \
                                        callback=callback)
    
    def start_minecraft_version(self):
        options = {
            'username': self.username,
            'uuid': str(uuid1()),
            'token': ''
        }

        subprocess.call(mllib.command.get_minecraft_command(version=self.version, \
                                                            minecraft_directory=MC_DIR, \
                                                            options=options))
    
    
    def set_download_status(self, status: str):
        self.download_progress['status'] = status
        
    def set_download_progress(self, progress: int):
        if self.download_progress['current_max'] != 0:
            self.download_progress['progress'] = progress
            
    def set_download_max(self, new_max: int):
        self.download_progress['current_max'] = new_max
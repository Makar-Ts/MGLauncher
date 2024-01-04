import io
from math import e

from exceptiongroup import catch
import minecraft_manager as mm
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt
from assets.main_ui import Ui_MainWindow
from assets.download_menu_ui import Ui_DownloadWindow
from assets.create_menu_ui import Ui_CreateWindow
from tkinter import W, filedialog
import sys, os, shutil, zipfile, tomli, json
import configparser

print(sys.path)
PATH_NUM = 2

CSS_STYLESHEET = sys.path[PATH_NUM] + "/assets/main_style.css"
INITAL_DIRS = {
    "player_data":     sys.path[PATH_NUM] + "/inital/player_data.ini",
    "vlaunchers_data": sys.path[PATH_NUM] + "/inital/vlaunchers_data.json"
}
LAUNCHER_DIRS = {
    "launcher":        mm.MC_DIR + "/.mglauncher/",
    "player_data":     mm.MC_DIR + "/.mglauncher/player_data.ini",
    "vlaunchers_data": mm.MC_DIR + "/.mglauncher/vlaunchers_data.json",
    "vlaunchers":      mm.MC_DIR + "/.mglauncher/vlaunchers/",
    "mc_mods":         mm.MC_DIR + "/mods/",
    "mc_old_mods":     mm.MC_DIR + "/mods/old/",
    "mc_versions":     mm.MC_DIR + "/versions/"
}

""" vlaunchers_data.json structure

"name" {
    "name" : "vlauncher name",
    "version": "any mc version",
    "type: "forge/fabric"
}

"""

MODS_DATA_PATH = {
    "forge": "META-INF/mods.toml",
    "fabric": "fabric.mod.json"
}

class SelectedMod:
    def __init__(self, path, name):
        self.path = path
        self.name = name


class LaunchThread(QThread):
    launch_setup_signal = pyqtSignal(str, str, int)
    progress_update_signal = pyqtSignal(int, int, str) 
    run_complete_callback = pyqtSignal(int) # exit code

    version_id = ''
    username = ''
    run_type = 0

    progress = 0
    progress_max = 0
    progress_label = ''
    
    def __init__(self):
        super().__init__()
        self.launch_setup_signal.connect(self.launch_setup)

    def launch_setup(self, version_id, username, _type):
        self.version_id = version_id
        self.username = username
        self.run_type = _type
    
    def retranslate_download_status(self, status: str):
        self.progress_label = status
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)
        
    def retranslate_download_progress(self, progress: int):
        self.progress = progress
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)
            
    def retranslate_download_max(self, new_max: int):
        self.progress_max = new_max
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)
    
    def run(self):
        if (self.run_type == 1 or self.run_type == 2 or self.run_type == 3):
            try:
                _type = "vanilla"
                if (self.run_type == 2): _type = "forge"
                elif (self.run_type == 3): _type = "fabric" 
                
                mlauncher = mm.MinecraftVersionLauncher(self.username, self.version_id, _type)

                callback = {
                    "setStatus": self.retranslate_download_status,
                    "setProgress": self.retranslate_download_progress,
                    "setMax": self.retranslate_download_max
                }
                
                if (not mlauncher.check_minecraft_version()):
                    print(f"Minecraft version {self.version_id} not available for type {self.run_type}")
                    self.run_complete_callback.emit(-2)
                    return -2
            
                print(f"==========================Downloading Minecraft [ {self.version_id} ]================")
                mlauncher.install_minecraft_version(callback, self.run_type-1)
                self.run_complete_callback.emit(1)
            except Exception as err:
                print(f"Failed to install Minecraft version [ {self.version_id} ] because [ {err} ]")
                return -2
                self.run_complete_callback.emit(-2)
        elif (self.run_type == 0):
            mlauncher = mm.MinecraftVersionLauncher(self.username, self.version_id)
        
            mlauncher.start_minecraft_version()
            
            self.run_complete_callback.emit(0)


#===============================Windows============================

class DownloadWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(DownloadWindow, self).__init__()
        self.ui = Ui_DownloadWindow()
        self.ui.setupUi(self)
        
        self.current_max = 1
        self.set_download_progress(0)
    
    def set_download_status(self, status: str):
        self.ui.label.setText(status)
        
    def set_download_progress(self, progress: int):
        if self.current_max != 0:
            self.ui.progressBar.setValue(int(progress/self.current_max*100))
            
    def set_download_max(self, new_max: int):
        self.current_max = new_max

class CreateWindow(QtWidgets.QMainWindow):
    onClick_create = pyqtSignal(str, int, str, list)
    mods_selected = []
    
    def __init__(self):
        super(CreateWindow, self).__init__()
        self.ui = Ui_CreateWindow()
        self.ui.setupUi(self)

        
        versions = mm.get_all_versions()
        
        for i in versions:
            self.ui.comboBox_avalableTypes.addItem(i[0])
        
        self.ui.comboBox_avalableVersions.addItem("Vanilla")
        self.ui.comboBox_avalableVersions.addItem("Forge")
        self.ui.comboBox_avalableVersions.addItem("Fabric")
        self.ui.comboBox_avalableVersions.currentIndexChanged.connect(self.onChanged_avalableVersions)

        self.ui.button_mod_add.setEnabled(False)
        self.ui.button_mod_remove.setEnabled(False)
        self.ui.line_launcherName.setEnabled(False)
        
        self.ui.button_create.clicked.connect(self.onClicked_create)

        self.ui.button_mod_add.clicked.connect(self.onClicked_mod_add)
        self.ui.button_mod_remove.clicked.connect(self.onClicked_mod_remove)
        
    def onClicked_create(self):
        
        self.ui.button_mod_add.setEnabled(False)
        self.ui.button_mod_remove.setEnabled(False)
        self.ui.line_launcherName.setEnabled(False)
        self.ui.button_create.setEnabled(False)
        self.ui.comboBox_avalableTypes.setEnabled(False)
        self.ui.comboBox_avalableVersions.setEnabled(False)
        self.onClick_create.emit(self.ui.comboBox_avalableTypes.currentText(), self.ui.comboBox_avalableVersions.currentIndex(), self.ui.line_launcherName.text(), self.mods_selected)
    
    def onClicked_mod_add(self):
        mods = filedialog.askopenfilenames(filetypes=[('JAR files', '*.jar')])
        
        for i in mods:
            with zipfile.ZipFile(i, 'r') as mod:
                name = ''
                
                try:
                    if (self.ui.comboBox_avalableVersions.currentIndex() == 1):
                        mod_info = mod.read(MODS_DATA_PATH["forge"])
                        
                        mod_info_file = io.BytesIO(mod_info)
                    
                        toml = tomli.load(mod_info_file)
                        
                        name = toml["mods"][0]["displayName"]
                    elif (self.ui.comboBox_avalableVersions.currentIndex() == 2):
                        with mod.open(MODS_DATA_PATH["fabric"]) as mod_json:
                            data = json.load(mod_json)
                            name = data["name"]
                except Exception as err:
                    print(f"Could not load mod [ {i} ] configuration file. Error: {err}")
                    continue
                
                if (name != ''):
                    mod = SelectedMod(i, name)
                    
                    self.mods_selected.append(mod)
                    self.ui.list_mods.addItem(name)
                    
                    print(f"Mod [ {name} ] added succesfully")
    
    def onClicked_mod_remove(self):
        selected_items = self.ui.list_mods.selectedItems()
        if (len(selected_items) != 0):
            for item in reversed(selected_items):
                row = self.ui.list_mods.row(item)

                self.ui.list_mods.takeItem(row)
                self.mods_selected.remove(self.mods_selected[row])
                
                print(f"Mod [ row:{row} ] removed")

    def onChanged_avalableVersions(self):
        self.mods_selected.clear()
        self.ui.list_mods.clear()
        
        if (self.ui.comboBox_avalableVersions.currentIndex() == 0):
            versions = mm.get_all_versions()
            self.ui.comboBox_avalableTypes.clear()
        
            for i in versions:
                self.ui.comboBox_avalableTypes.addItem(i[0])
            
            self.ui.button_mod_add.setEnabled(False)
            self.ui.button_mod_remove.setEnabled(False)
            self.ui.line_launcherName.setEnabled(False)
        else:
            self.ui.button_mod_add.setEnabled(True)
            self.ui.button_mod_remove.setEnabled(True)
            self.ui.line_launcherName.setEnabled(True)
            
            index = self.ui.comboBox_avalableVersions.currentIndex()
            versions = mm.get_all_versions(index)
            self.ui.comboBox_avalableTypes.clear()
        
            for i in versions:
                self.ui.comboBox_avalableTypes.addItem(i[0])
    
    def reset(self):
        self.mods_selected = []
        self.ui.list_mods.clear()
        
        self.ui.button_create.setEnabled(True)
        self.ui.comboBox_avalableTypes.setEnabled(True)
        self.ui.comboBox_avalableVersions.setEnabled(True)
        
        self.ui.comboBox_avalableVersions.setCurrentIndex(0)
        self.ui.line_launcherName.setText("")
        
        
 
class MainWindow(QtWidgets.QMainWindow):
    username = ""
    current_mods = []
    
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.setWindowTitle("MGLauncher")
        
        
        
        self.ui.button_start.clicked.connect(self.onClick_start)
        self.ui.button_check.clicked.connect(self.onClick_check)
        self.ui.button_createNew.clicked.connect(self.onClick_new)
        self.ui.button_delete.clicked.connect(self.onClick_delete)
        
        
        installed_versions = mm.get_installed_versions()
        
        for i in installed_versions:
            self.ui.comboBox_avalableVersions.addItem(f"{i[0]}{(i[1] != 'release')*(' - '+i[1])}")
        
        self.ui.comboBox_avalableTypes.addItem("Installed")
        self.ui.comboBox_avalableTypes.addItem("VLaunchers")
        self.ui.comboBox_avalableTypes.currentTextChanged.connect(self.onChanged_type)
        
        self.config = configparser.ConfigParser()
        self.config.read(LAUNCHER_DIRS["player_data"])
        self.username = self.config["Player"]["username"]
        
        self.ui.lineEdit.setText(self.username)
        self.ui.lineEdit.editingFinished.connect(self.saveUsername)
        
        self.downloadWindow = DownloadWindow()
        self.downloadWindow.setWindowTitle("Downloading")
        
        self.createWindow = CreateWindow()
        self.createWindow.setWindowTitle("Create new")
        self.createWindow.onClick_create.connect(self.install)
        
        with open(CSS_STYLESHEET, "r") as f:
            css = f.read()
            
            self.setStyleSheet(css)
            self.downloadWindow.setStyleSheet(css)
            self.createWindow.setStyleSheet(css)
        
        self.launch_thread = LaunchThread()
        self.launch_thread.progress_update_signal.connect(self.update_progress)
        self.launch_thread.run_complete_callback.connect(self.runCallback)
    
    def install(self, version, _type, name="", mods=[]):
        self.downloadWindow.show()
        
        if (_type != 0 and len(mods) != 0 and name != ""):
            data_version = version
            if (_type == 1):
                splitted = version.split("-")
                
                data_version = splitted[0] + "-forge-" + splitted[1]        
            elif (_type == 2):
                data_version = version
            
            new_VLauncher = {
                "name": name,
                "version": data_version,
                "type": (_type == 1)*"forge"+(_type == 2)*"fabric"
            }
            
            os.mkdir(LAUNCHER_DIRS["vlaunchers"]+"/"+name)
            
            for i in mods: 
                mod_name = i.path.split("/")[-1]
                
                shutil.copyfile(i.path, LAUNCHER_DIRS["vlaunchers"]+name+"/"+mod_name)
            
            try:
                with open(LAUNCHER_DIRS["vlaunchers_data"], 'r+') as file:
                    file_data = json.load(file)
                    
                    file_data["vlaunchers"].append(new_VLauncher)
                    
                    file.seek(0)
                    json.dump(file_data, file, indent = 4)
            except json.decoder.JSONDecodeError:
                with open(LAUNCHER_DIRS["vlaunchers_data"], 'w') as file:
                    json.dump(new_VLauncher, file, indent = 4)
                
        
        self.launch_thread.launch_setup_signal.emit(version, self.username, _type+1)
        self.launch_thread.start()
        
    def saveUsername(self):
        self.username = self.ui.lineEdit.text()
        self.config["Player"]["username"] = self.ui.lineEdit.text()
        
        with open(LAUNCHER_DIRS["player_data"], 'w') as configfile:    # save
            self.config.write(configfile)
        
    
    def runCallback(self, code):
        if (code == 0):
            if (self.current_mods != []):
                deleted_mods = os.listdir(LAUNCHER_DIRS["mc_mods"])
                
                for i in deleted_mods:
                    if (i.split(".")[-1] == "jar"):
                        os.remove(LAUNCHER_DIRS["mc_mods"]+i)
                self.current_mods = []
            
            self.show()
        elif (code == 1):
            self.update_versions_comboBox()
            
            self.downloadWindow.hide()
            self.createWindow.hide()
        elif (code == -2):
            self.downloadWindow.hide()
            self.createWindow.hide()
    
    def onClick_start(self):
        self.hide()
        
        if (self.ui.comboBox_avalableTypes.currentIndex() == 0):
            self.launch_thread.launch_setup_signal.emit(mm.get_installed_versions()[self.ui.comboBox_avalableVersions.currentIndex()][0], self.username, 0)
            self.launch_thread.start()
        elif (self.ui.comboBox_avalableTypes.currentIndex() == 1):
            version = self.get_vlaunchers()[self.ui.comboBox_avalableVersions.currentIndex()]
            
            if (version['type'] == "fabric"):
                if (version['version'][0].isdigit()):
                    ver_to_parse = mm.get_installed_versions()
                    
                    for i in ver_to_parse:
                        if (version['version'] in i[0] and "fabric-loader-" in i[0]):
                            with open(LAUNCHER_DIRS["vlaunchers_data"], 'r+') as file:
                                file_data = json.load(file)
                                
                                file_data["vlaunchers"][self.ui.comboBox_avalableVersions.currentIndex()]["version"] = i[0]
                                
                                file.seek(0)
                                json.dump(file_data, file, indent = 4)
                                
                                version['version'] = i[0]

                                break
                
            old_mods = os.listdir(LAUNCHER_DIRS["mc_mods"])
            
            for i in old_mods:
                if (i.split(".")[-1] == "jar"):
                    shutil.move(LAUNCHER_DIRS["mc_mods"]+"/"+i, LAUNCHER_DIRS["mc_old_mods"]+i.split("/")[-1])
            
            self.current_mods = os.listdir(LAUNCHER_DIRS["vlaunchers"]+version['name'])
            
            for i in self.current_mods:
                shutil.copyfile(LAUNCHER_DIRS["vlaunchers"]+version['name']+"/"+i, LAUNCHER_DIRS["mc_mods"]+i.split("/")[-1])
                
            self.launch_thread.launch_setup_signal.emit(version['version'], self.username, 0)
            self.launch_thread.start()
            
    def onClick_check(self):
        self.downloadWindow.show()
        
        self.launch_thread.launch_setup_signal.emit(mm.get_installed_versions()[self.ui.comboBox_avalableVersions.currentIndex()][0], self.username, 1)
        self.launch_thread.start()
     
    def onClick_new(self):
        self.createWindow.reset()
        self.createWindow.show()
    
    def onClick_delete(self):
        if (self.ui.comboBox_avalableTypes.currentIndex() == 0):
            shutil.rmtree(LAUNCHER_DIRS["mc_versions"]+mm.get_installed_versions()[self.ui.comboBox_avalableVersions.currentIndex()][0])
            
            self.update_versions_comboBox()
        elif (self.ui.comboBox_avalableTypes.currentIndex() == 1):
            vlauncher_name = ""
            with open(LAUNCHER_DIRS["vlaunchers_data"], 'r+') as file:
                data = json.load(file)
                
                vlauncher_name = data["vlaunchers"][self.ui.comboBox_avalableVersions.currentIndex()]["name"]
                
                del data['vlaunchers'][self.ui.comboBox_avalableVersions.currentIndex()]
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()
            
            shutil.rmtree(LAUNCHER_DIRS["vlaunchers"]+vlauncher_name)
            self.update_versions_comboBox()
    
    def onChanged_type(self):
        self.update_versions_comboBox()
        
    def update_progress(self, progress, max_progress, label):
        print(f"[ {label} ] - {progress}/{max_progress}")
        
        self.downloadWindow.set_download_status(label)
        self.downloadWindow.set_download_max(max_progress)
        self.downloadWindow.set_download_progress(progress)
    
    def update_versions_comboBox(self):
        if (self.ui.comboBox_avalableTypes.currentIndex() == 0):
            installed_versions = mm.get_installed_versions()
            self.ui.comboBox_avalableVersions.clear()
            
            for i in installed_versions:
                self.ui.comboBox_avalableVersions.addItem(f"{i[0]}{(i[1] != 'release')*(' - '+i[1])}")
        elif (self.ui.comboBox_avalableTypes.currentIndex() == 1):
            installed_versions = self.get_vlaunchers()
            self.ui.comboBox_avalableVersions.clear()
            
            for i in installed_versions:
                self.ui.comboBox_avalableVersions.addItem(f"{i['name']} - {i['type']}")
    
    def get_vlaunchers(self):
        with open(LAUNCHER_DIRS["vlaunchers_data"], 'r') as file:
            try:
                file_data = json.load(file)
                
                return file_data["vlaunchers"]
            except json.decoder.JSONDecodeError:
                return []
        
 
if (__name__ == "__main__"):
    if (not os.path.exists(LAUNCHER_DIRS["launcher"])):
        os.mkdir(LAUNCHER_DIRS["launcher"])
    if (not os.path.exists(LAUNCHER_DIRS["player_data"])):
        shutil.copyfile(INITAL_DIRS["player_data"], LAUNCHER_DIRS["player_data"])
    if (not os.path.exists(LAUNCHER_DIRS["vlaunchers_data"])):
        shutil.copyfile(INITAL_DIRS["vlaunchers_data"], LAUNCHER_DIRS["vlaunchers_data"])
    if (not os.path.exists(LAUNCHER_DIRS["vlaunchers"])):
        os.mkdir(LAUNCHER_DIRS["vlaunchers"])
    if (not os.path.exists(LAUNCHER_DIRS["mc_mods"])):
        os.mkdir(LAUNCHER_DIRS["mc_mods"])
    if (not os.path.exists(LAUNCHER_DIRS["mc_old_mods"])):
        os.mkdir(LAUNCHER_DIRS["mc_old_mods"])
    
    app = QtWidgets.QApplication([])
    application = MainWindow()
    application.show()

    sys.exit(app.exec())
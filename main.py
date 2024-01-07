# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace, no-name-in-module, unused-import

"""Main script
"""

import configparser
import io, sys, os
import shutil, zipfile, json
from tkinter import filedialog
import tomli
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from assets.main_ui import Ui_MainWindow
from assets.download_menu_ui import Ui_DownloadWindow
from assets.create_menu_ui import Ui_CreateWindow
from assets.edit_menu_ui import Ui_EditWindow
from assets.animated_ui import CustomWidgetItem
import minecraft_manager as mm
import mc_mod_manager as mcmm


LAUNCHER_DIRS = {
    "launcher":        mm.MC_DIR + "/.mglauncher/",
    "player_data":     mm.MC_DIR + "/.mglauncher/player_data.ini",
    "vlaunchers_data": mm.MC_DIR + "/.mglauncher/vlaunchers_data.json",
    "vlaunchers":      mm.MC_DIR + "/.mglauncher/vlaunchers/",           # Папка с сохраненными сборками
    "mc_mods":         mm.MC_DIR + "/mods/",
    "mc_old_mods":     mm.MC_DIR + "/mods/old/",
    "mc_versions":     mm.MC_DIR + "/versions/"
}

""" vlaunchers_data.json structure

"name" {
    "name" : "vlauncher name",       # имя в папке vlaunchers
    "version": "version to start",   # если при fabric обычная версия, то парсит список установленных
    "type: "forge/fabric"            
}

"""

MODS_DATA_PATH = {      # расположение инфы о моде (имени) внутри .jar файла
    "forge": "META-INF/mods.toml",
    "fabric": "fabric.mod.json"
}

print(sys.path)
PATH_NUM = 2

if os.path.exists(LAUNCHER_DIRS["player_data"]):
    config = configparser.ConfigParser()
    config.read(LAUNCHER_DIRS["player_data"])
    
    PATH_NUM = int(config["Player"]["PATH_NUM"])

CSS_STYLESHEET = sys.path[PATH_NUM] + "/assets/main_style.css"
INITAL_DIRS = {      # Если директории нет в папке mc то отсюда будут брать данные
    "player_data":     sys.path[PATH_NUM] + "/inital/player_data.ini",
    "vlaunchers_data": sys.path[PATH_NUM] + "/inital/vlaunchers_data.json"
}

while not os.path.exists(INITAL_DIRS["player_data"]):
    print("!!!!!!!!!!!!!!!!! [ PATH ERROR ] !!!!!!!!!!!!!!!!!")
    corrected_path_num = input("""Please enter the correct PATH identifier 
(see the very first line, the path should be C:\\Users\\username\\AppData\\Local\\Temp\\MEI(some nums) and enter its sequence number).""")
    
    PATH_NUM = int(corrected_path_num)-1
    
    CSS_STYLESHEET = sys.path[PATH_NUM] + "/assets/main_style.css"
    INITAL_DIRS = {      # Если директории нет в папке mc то отсюда будут брать данные
        "player_data":     sys.path[PATH_NUM] + "/inital/player_data.ini",
        "vlaunchers_data": sys.path[PATH_NUM] + "/inital/vlaunchers_data.json"
    }

def get_vlaunchers():
    """Get vaunchers from the file

    Returns:
        [list]: [check the vlauncher_data structure]
    """

    with open(LAUNCHER_DIRS["vlaunchers_data"], 'r') as file:
        try:
            file_data = json.load(file)

            return file_data["vlaunchers"]
        except json.decoder.JSONDecodeError:
            return []

class SelectedMod:
    """Store information about selected mod.
    """

    def __init__(self, path, name):
        self.path = path
        self.name = name


class LaunchThread(QThread):
    """Creating separate stream for downloading and running mc.
    """

    launch_setup_signal = pyqtSignal(str, str, int, str)
    progress_update_signal = pyqtSignal(int, int, str)
    run_complete_callback = pyqtSignal(int) # exit code

    version_id = ''
    username = ''
    run_type = 0
    jvm_args = ""

    progress = 0
    progress_max = 0
    progress_label = ''

    def __init__(self):
        super().__init__()
        self.launch_setup_signal.connect(self.launch_setup)

    def launch_setup(self, version_id:str, username:str, _type:int, args:str):
        """Setup the thread.

        Args:
            version_id [str]: [mc version id (or forge version)]
            username [str]: [player's name]
            _type [int]: [0 to start mc version, 
                          1 for install vanilla, 
                          2 for install forge, 
                          3 for install fabric]
            args [str]: [JVM startup arguments]
        """

        self.version_id = version_id
        self.username = username
        self.run_type = _type
        self.jvm_args = args

    def retranslate_download_status(self, status: str):
        """Re - emit the download status.

        Args:
            status (str): [download status]
        """

        self.progress_label = status
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def retranslate_download_progress(self, progress: int):
        """Re - emit the download progress.

        Args:
            progress (int): [download progress]
        """

        self.progress = progress
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def retranslate_download_max(self, new_max: int):
        """Re - emit the download max value.

        Args:
            new_max (int): [maximum value]
        """

        self.progress_max = new_max
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def run(self):
        """Function that calls then start() function of thread called.
        """

        if self.run_type == 1 or self.run_type == 2 or self.run_type == 3:
            try:
                _type = "vanilla"
                if self.run_type == 2:
                    _type = "forge"
                elif self.run_type == 3:
                    _type = "fabric"

                mlauncher = mm.MinecraftVersionLauncher(self.username, self.version_id, _type)

                callback = {
                    "setStatus": self.retranslate_download_status,
                    "setProgress": self.retranslate_download_progress,
                    "setMax": self.retranslate_download_max
                }

                if not mlauncher.check_minecraft_version():
                    print(f"Minecraft version {self.version_id}\
                            not available for type {self.run_type}")
                    self.run_complete_callback.emit(-2)
                    return -2

                print(f"==========================Downloading Minecraft [ {self.version_id} ]==========================")
                mlauncher.install_minecraft_version(callback, self.run_type-1)
                self.run_complete_callback.emit(1)

            except Exception as err:
                print(f"Failed to install Minecraft version [ {self.version_id} ]\
                        because [ {err} ]")

                self.run_complete_callback.emit(-2)
                return -2
        elif self.run_type == 0:
            mlauncher = mm.MinecraftVersionLauncher(self.username, self.version_id)

            mlauncher.start_minecraft_version([self.jvm_args])

            self.run_complete_callback.emit(0)


#===============================Windows============================

class DownloadWindow(QtWidgets.QMainWindow):
    """Class for download progress bar
    """

    def __init__(self):
        super(DownloadWindow, self).__init__()
        self.ui = Ui_DownloadWindow()
        self.ui.setupUi(self)

        self.current_max = 1
        self.set_download_progress(0)

    def set_download_status(self, status: str):
        """Sets the download status .

        Args:
            status (str)
        """

        self.ui.label.setText(status)

    def set_download_progress(self, progress: int):
        """Set download progress to bar.

        Args:
            progress (int)
        """

        if self.current_max != 0:
            self.ui.progressBar.setValue(int(progress/self.current_max*100))
                # максимум (по стандарту) 100 едениц

    def set_download_max(self, new_max: int):
        """Set the download max to bar.

        Args:
            new_max (int)
        """

        self.current_max = new_max

class EditWindow(QtWidgets.QMainWindow):
    """Window for editing already existing vlaunchers.
    """    
    
    mods_selected = []
    current_vlauncher_data = {}
    current_vlauncher_index = 0
    
    def __init__(self):
        super(EditWindow, self).__init__()
        self.ui = Ui_EditWindow()
        self.ui.setupUi(self)
        
        self.ui.button_mod_add.clicked.connect(self.onClick_add_mod)
        self.ui.button_mod_remove.clicked.connect(self.onClick_remove_mod)
        self.ui.button_create.clicked.connect(self.onClick_save)
    
    def setup_mod_ui(self, vlauncher_data: dict, vlauncher_index: int):
        """Setup ui before showing up window

        Args:
            vlauncher_data (dict): [check vlaunchers_data.json structure]
            vlauncher_index (int)

        Raises:
            ValueError: [if version not found]
        """  
        self.current_vlauncher_data = vlauncher_data
        self.current_vlauncher_index = vlauncher_index
                           
        self.ui.comboBox_avalableVersions.clear()
        self.ui.list_mods.clear()
        
        installed_versions = mm.get_installed_versions()
        
        if vlauncher_data['type'] == "fabric" and vlauncher_data['version'][0].isdigit():
            for i in installed_versions:
                if vlauncher_data['version'] in i[0] and "fabric-loader-" in i[0]:
                    with open(LAUNCHER_DIRS["vlaunchers_data"], 'r+') as file:
                        file_data = json.load(file)

                        file_data["vlaunchers"]\
                            [self.ui.comboBox_avalableVersions.currentIndex()]["version"] = i[0]

                        file.seek(0)
                        json.dump(file_data, file, indent = 4)

                        vlauncher_data['version'] = i[0]
                        self.current_vlauncher_data['version'] = i[0]

                        break
        
        current_ver_index = -1
        for index, i in enumerate(installed_versions):
            self.ui.comboBox_avalableVersions.addItem(i[0])
            
            if i[0] == vlauncher_data['version']:
                current_ver_index = index
        
        if current_ver_index == -1:
            raise ValueError("Version not found")
            
        self.ui.comboBox_avalableVersions.setCurrentIndex(current_ver_index)
        
        mods = list(map(lambda x: LAUNCHER_DIRS["vlaunchers"]+vlauncher_data['name']+"/"+x, os.listdir(LAUNCHER_DIRS["vlaunchers"]+vlauncher_data['name'])))
        
        for i in mods:
            mod = mcmm.get_mod_data(i)

            if mod is not None:
                if mod.name != '':
                    self.mods_selected.append(mod)
                    #self.ui.list_mods.addItem(mod.name)
                    
                    item = QtWidgets.QListWidgetItem()
                    item.setText(mod.name)
                    item.setToolTip(f"{mod.description}\n\nVersion: {mod.version}\nAuthors: {mod.authors}\n")
                    self.ui.list_mods.addItem(item)

                    print(f"Mod [ {mod.name} ] added succesfully")
                else:
                    print(f" Mod [ {mod.name} ] launcher type is incorrect")
    
    def onClick_add_mod(self):
        """Add a mod to the list
        """

        mods = filedialog.askopenfilenames(filetypes=[('JAR files', '*.jar')])

        for i in mods:
            mod = mcmm.get_mod_data(i)

            if mod is not None:
                if mod.name != '' and mod.launcher_type == self.current_vlauncher_data['type']:
                    self.mods_selected.append(mod)
                    #self.ui.list_mods.addItem(mod.name)
                    
                    item = QtWidgets.QListWidgetItem()
                    item.setText(mod.name)
                    item.setToolTip(f"{mod.description}\n\nVersion: {mod.version}\nAuthors: {mod.authors}\n")
                    self.ui.list_mods.addItem(item)
                    
                    mod_name = mod.path.split("/")[-1]
                    shutil.copyfile(mod.path, LAUNCHER_DIRS["vlaunchers"]+self.current_vlauncher_data['name']+"/"+mod_name)

                    print(f"Mod [ {mod.name} ] added succesfully")
                else:
                    print(f" Mod [ {mod.name} ] launcher type is incorrect")
    
    def onClick_remove_mod(self):
        """Remove a mod from the list
        """

        selected_items = self.ui.list_mods.selectedItems()
        if len(selected_items) != 0:
            for item in reversed(selected_items):
                row = self.ui.list_mods.row(item)

                self.ui.list_mods.takeItem(row)
                os.remove(self.mods_selected[row].path)
                self.mods_selected.remove(self.mods_selected[row])

                print(f"Mod [ row:{row} ] removed")
    
    def onClick_save(self):
        """Save the current version of the vlauncher to the file and closes the window.
        """        
        
        if self.ui.comboBox_avalableVersions.currentData() != self.current_vlauncher_data['version']:
            with open(LAUNCHER_DIRS["vlaunchers_data"], 'r+') as file:
                file_data = json.load(file)

                file_data["vlaunchers"]\
                    [self.current_vlauncher_index]["version"] = self.ui.comboBox_avalableVersions.currentText()

                file.seek(0)
                json.dump(file_data, file, indent = 4)
                
        self.hide()
        

class CreateWindow(QtWidgets.QMainWindow):
    """Class for create_window where creating new VLaunchers.
    """

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
        self.ui.comboBox_avalableVersions.currentIndexChanged\
                                         .connect(self.onChanged_avalableVersions)

        # устанавливаем кнопки модов и строки имени на выключено при ваниле
        self.ui.button_mod_add.setEnabled(False)
        self.ui.button_mod_remove.setEnabled(False)
        self.ui.line_launcherName.setEnabled(False)

        self.ui.button_create.clicked.connect(self.onClicked_create)

        self.ui.button_mod_add.clicked.connect(self.onClicked_mod_add)
        self.ui.button_mod_remove.clicked.connect(self.onClicked_mod_remove)

    def onClicked_create(self):
        """Callback when the create button is clicked .
        """

        self.ui.button_mod_add.setEnabled(False)
        self.ui.button_mod_remove.setEnabled(False)
        self.ui.line_launcherName.setEnabled(False)
        self.ui.button_create.setEnabled(False)
        self.ui.comboBox_avalableTypes.setEnabled(False)
        self.ui.comboBox_avalableVersions.setEnabled(False)
        self.onClick_create.emit(self.ui.comboBox_avalableTypes.currentText(), \
                                 self.ui.comboBox_avalableVersions.currentIndex(), \
                                 self.ui.line_launcherName.text(), \
                                 self.mods_selected)

    def onClicked_mod_add(self):
        """Add a mod to the list
        """

        mods = filedialog.askopenfilenames(filetypes=[('JAR files', '*.jar')])
        index = self.ui.comboBox_avalableVersions.currentIndex()

        for i in mods:
            mod = mcmm.get_mod_data(i)

            if mod is not None:
                if mod.name != '' and mod.launcher_type == ((index == 1)*"forge" + (index == 2)*"fabric"):
                    self.mods_selected.append(mod)
                    #self.ui.list_mods.addItem(mod.name)
                    
                    item = QtWidgets.QListWidgetItem()
                    item.setText(mod.name)
                    item.setToolTip(f"{mod.description}\n\nVersion: {mod.version}\nAuthors: {mod.authors}\n")
                    self.ui.list_mods.addItem(item)

                    print(f"Mod [ {mod.name} ] added succesfully")
                else:
                    print(f" Mod [ {mod.name} ] launcher type is incorrect")

    def onClicked_mod_remove(self):
        """Remove a mod from the list
        """

        selected_items = self.ui.list_mods.selectedItems()
        if len(selected_items) != 0:
            for item in reversed(selected_items):
                row = self.ui.list_mods.row(item)

                self.ui.list_mods.takeItem(row)
                self.mods_selected.remove(self.mods_selected[row])

                print(f"Mod [ row:{row} ] removed")

    def onChanged_avalableVersions(self):
        """Called when the user has changed the version.
        """

        self.mods_selected.clear()
        self.ui.list_mods.clear()

        if self.ui.comboBox_avalableVersions.currentIndex() == 0:
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
        """Reset the state of the editor to its initial state.
        """

        self.mods_selected = []
        self.ui.list_mods.clear()

        self.ui.button_create.setEnabled(True)
        self.ui.comboBox_avalableTypes.setEnabled(True)
        self.ui.comboBox_avalableVersions.setEnabled(True)

        self.ui.comboBox_avalableVersions.setCurrentIndex(0)
        self.ui.line_launcherName.setText("")



class MainWindow(QtWidgets.QMainWindow):
    """Class what controls main window and operates all.
    """

    username = ""
    current_mods = []

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("MGLauncher")


        self.ui.button_start.clicked.connect(self.onClick_start)
        self.ui.button_check.clicked.connect(self.onClick_check)
        self.ui.button_check.setText("Check")
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
        self.ui.lineEdit.editingFinished.connect(self.save_username)

        self.download_window = DownloadWindow()
        self.download_window.setWindowTitle("Downloading")

        self.create_window = CreateWindow()
        self.create_window.setWindowTitle("Create new")
        self.create_window.onClick_create.connect(self.install)
        
        self.edit_window = EditWindow()
        self.edit_window.setWindowTitle("Edit")

        with open(CSS_STYLESHEET, "r") as f:
            css = f.read()

            self.setStyleSheet(css)
            self.download_window.setStyleSheet(css)
            self.create_window.setStyleSheet(css)
            self.edit_window.setStyleSheet(css)

        self.launch_thread = LaunchThread()
        self.launch_thread.progress_update_signal.connect(self.update_progress)
        self.launch_thread.run_complete_callback.connect(self.run_callback)
        
        if self.config["Player"]["PATH_NUM"] != PATH_NUM:
            self.config["Player"]["PATH_NUM"] = str(PATH_NUM)
            
            with open(LAUNCHER_DIRS["player_data"], 'w') as configfile:    # save
                self.config.write(configfile)

    def install(self, version:str, _type:int, name="", mods: list[mcmm.ModData]=[]):
        """install a new mc version (or vlauncher)

        Args:
            version [str]: [mc or forge version]
            _type [int]: [0 for install vanilla, 
                             1 for install forge, 
                             2 for install fabric]
            name (str, optional): [vlauncher's name]. Defaults to "".
            mods (list[mc_mod_manager.ModData], optional): [vlauncher's mods]. Defaults to [].
        """

        self.download_window.show()

        if _type != 0 and len(mods) != 0 and name != "":
            data_version = version
            if _type == 1:
                splitted = version.split("-")

                data_version = splitted[0] + "-forge-" + splitted[1]
            elif _type == 2:
                data_version = version

            new_vlauncher = {
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

                    file_data["vlaunchers"].append(new_vlauncher)

                    file.seek(0)
                    json.dump(file_data, file, indent = 4)
            except json.decoder.JSONDecodeError:
                with open(LAUNCHER_DIRS["vlaunchers_data"], 'w') as file:
                    json.dump(new_vlauncher, file, indent = 4)


        self.launch_thread.launch_setup_signal.emit(version, self.username, _type+1, self.config["Java"]["args"])
        self.launch_thread.start()

    def save_username(self):
        """Save username to config file .
        """

        self.username = self.ui.lineEdit.text()
        self.config["Player"]["username"] = self.ui.lineEdit.text()

        with open(LAUNCHER_DIRS["player_data"], 'w') as configfile:    # save
            self.config.write(configfile)

    def run_callback(self, code:int):
        """Callback when run function in LaunchThread ended.

        Args:
            code [int]: [0 - mc closed
                         1 - created new version
                         errors:
                         -2 - error while creating new version]
        """

        if code == 0:
            if self.current_mods != []:
                deleted_mods = os.listdir(LAUNCHER_DIRS["mc_mods"])

                for i in deleted_mods:
                    if i.split(".")[-1] == "jar":
                        os.remove(LAUNCHER_DIRS["mc_mods"]+i)
                self.current_mods = []

            self.show()
        elif code == 1:
            self.update_versions_comboBox()

            self.download_window.hide()
            self.create_window.hide()
        elif code == -2:
            self.download_window.hide()
            self.create_window.hide()

    def onClick_start(self):
        """Start the mc launch
        """

        self.hide()

        if self.ui.comboBox_avalableTypes.currentIndex() == 0:
            self.launch_thread.launch_setup_signal.emit(mm.get_installed_versions()[self.ui.comboBox_avalableVersions.currentIndex()][0], \
                                                        self.username, \
                                                        0, self.config["Java"]["args"])
            self.launch_thread.start()
        elif self.ui.comboBox_avalableTypes.currentIndex() == 1:
            version = get_vlaunchers()[self.ui.comboBox_avalableVersions.currentIndex()]

            if version['type'] == "fabric":
                if version['version'][0].isdigit():
                    ver_to_parse = mm.get_installed_versions()

                    for i in ver_to_parse:
                        if version['version'] in i[0] and "fabric-loader-" in i[0]:
                            with open(LAUNCHER_DIRS["vlaunchers_data"], 'r+') as file:
                                file_data = json.load(file)

                                file_data["vlaunchers"]\
                                    [self.ui.comboBox_avalableVersions.currentIndex()]["version"] = i[0]

                                file.seek(0)
                                json.dump(file_data, file, indent = 4)

                                version['version'] = i[0]

                                break

            old_mods = os.listdir(LAUNCHER_DIRS["mc_mods"])

            for i in old_mods:
                if i.split(".")[-1] == "jar":
                    shutil.move(LAUNCHER_DIRS["mc_mods"]+"/"+i, \
                                LAUNCHER_DIRS["mc_old_mods"]+i.split("/")[-1])

            self.current_mods = os.listdir(LAUNCHER_DIRS["vlaunchers"]+version['name'])

            for i in self.current_mods:
                shutil.copyfile(LAUNCHER_DIRS["vlaunchers"]+version['name']+"/"+i, \
                                LAUNCHER_DIRS["mc_mods"]+i.split("/")[-1])

            self.launch_thread.launch_setup_signal.emit(version['version'], self.username, 0, self.config["Java"]["args"])
            self.launch_thread.start()

    def onClick_check(self):
        """Callback when the user clicks the check (or edit) button
        """

        if self.ui.comboBox_avalableTypes.currentIndex() == 0:
            self.download_window.show()

            self.launch_thread.launch_setup_signal.emit(mm.get_installed_versions()\
                                                        [self.ui.comboBox_avalableVersions.currentIndex()][0], \
                                                        self.username, 1, self.config["Java"]["args"])
            self.launch_thread.start()
        elif self.ui.comboBox_avalableTypes.currentIndex() == 1:
            vlauncher_data = get_vlaunchers()[self.ui.comboBox_avalableVersions.currentIndex()]
            
            self.edit_window.setup_mod_ui(vlauncher_data, self.ui.comboBox_avalableVersions.currentIndex())
            self.edit_window.show()

    def onClick_new(self):
        """Callback when the user clicks "Create new VLauncher" button
        """

        self.create_window.reset()
        self.create_window.show()

    def onClick_delete(self):
        """Deletes the vlauncher or mc version.
        """

        if self.ui.comboBox_avalableTypes.currentIndex() == 0:
            shutil.rmtree(LAUNCHER_DIRS["mc_versions"]+mm.get_installed_versions()\
                          [self.ui.comboBox_avalableVersions.currentIndex()][0])

            self.update_versions_comboBox()
        elif self.ui.comboBox_avalableTypes.currentIndex() == 1:
            vlauncher_name = ""
            with open(LAUNCHER_DIRS["vlaunchers_data"], 'r+') as file:
                data = json.load(file)

                vlauncher_name = data["vlaunchers"]\
                                     [self.ui.comboBox_avalableVersions.currentIndex()]["name"]

                del data['vlaunchers'][self.ui.comboBox_avalableVersions.currentIndex()]
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()

            shutil.rmtree(LAUNCHER_DIRS["vlaunchers"]+vlauncher_name)
            self.update_versions_comboBox()

    def onChanged_type(self):
        """Callback when type changed.
        """

        self.update_versions_comboBox()

        if self.ui.comboBox_avalableTypes.currentIndex() == 0:
            self.ui.button_check.setText("Check")
        elif self.ui.comboBox_avalableTypes.currentIndex() == 1:
            self.ui.button_check.setText("Edit")

    def update_progress(self, progress:int, max_progress:int, label:str):
        """Update progress bar.

        Args:
            progress (int): [download progress]
            max_progress (int): [download max progress]
            label (str): [download state]
        """

        print(f"[ {label} ] - {progress}/{max_progress}")

        self.download_window.set_download_status(label)
        self.download_window.set_download_max(max_progress)
        self.download_window.set_download_progress(progress)

    def update_versions_comboBox(self):
        """Update the list of versions of the combo box.
        """

        if self.ui.comboBox_avalableTypes.currentIndex() == 0:
            installed_versions = mm.get_installed_versions()
            self.ui.comboBox_avalableVersions.clear()

            for i in installed_versions:
                self.ui.comboBox_avalableVersions.addItem(f"{i[0]}{(i[1] != 'release')*(' - '+i[1])}")
        elif self.ui.comboBox_avalableTypes.currentIndex() == 1:
            installed_versions = get_vlaunchers()
            self.ui.comboBox_avalableVersions.clear()

            for i in installed_versions:
                self.ui.comboBox_avalableVersions.addItem(f"{i['name']} - {i['type']}")


if __name__ == "__main__":
    if not os.path.exists(LAUNCHER_DIRS["launcher"]):
        os.mkdir(LAUNCHER_DIRS["launcher"])
    if not os.path.exists(LAUNCHER_DIRS["player_data"]):
        shutil.copyfile(INITAL_DIRS["player_data"], LAUNCHER_DIRS["player_data"])
    if not os.path.exists(LAUNCHER_DIRS["vlaunchers_data"]):
        shutil.copyfile(INITAL_DIRS["vlaunchers_data"], LAUNCHER_DIRS["vlaunchers_data"])
    if not os.path.exists(LAUNCHER_DIRS["vlaunchers"]):
        os.mkdir(LAUNCHER_DIRS["vlaunchers"])
    if not os.path.exists(LAUNCHER_DIRS["mc_mods"]):
        os.mkdir(LAUNCHER_DIRS["mc_mods"])
    if not os.path.exists(LAUNCHER_DIRS["mc_old_mods"]):
        os.mkdir(LAUNCHER_DIRS["mc_old_mods"])

    app = QtWidgets.QApplication([])
    application = MainWindow()
    application.show()

    sys.exit(app.exec())

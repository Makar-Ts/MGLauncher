# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace, no-name-in-module, unused-import

"""Main script
"""

import time
import configparser
import base64, traceback
import io, sys, os
import shutil, zipfile, json, tomli
from tkinter import filedialog
from mojang import Client
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from Crypto.Cipher import AES
import configs_manager
from assets.ui.main_ui import          Ui_MainWindow
from assets.ui.download_menu_ui import Ui_DownloadWindow
from assets.ui.create_menu_ui import   Ui_CreateWindow
from assets.ui.edit_menu_ui import     Ui_EditWindow
from assets.ui.log_in_window_ui import Ui_LogInWindow
from assets.animated_ui import PopupWindow
import minecraft_manager as mm
import mc_mod_manager as mcmm


#=========================================================            =========================================================
#========================================================= Constants  =========================================================
#=========================================================            =========================================================

SECRET_CRYPTO_KEY = b'Z\xc9\xd0\x16\xaf\x01\x85\x0e\xff\x9f\xd7\x96$\x0b\xe6\xcb\xfco\xe2\x85\xc5\xebUC\xb1E\xc72L\xa3\rJ'

LAUNCHER_DIRS = {
    "launcher":        mm.MC_DIR + "/.mglauncher/",
    "player_data":     mm.MC_DIR + "/.mglauncher/player_data.ini",
    "vlaunchers_data": mm.MC_DIR + "/.mglauncher/vlaunchers_data.json",
    "vlaunchers":      mm.MC_DIR + "/.mglauncher/vlaunchers/",           # Папка с сохраненными сборками
    "mc_mods":         mm.MC_DIR + "/mods/",
    "mc_old_mods":     mm.MC_DIR + "/mods/old/",
    "mc_versions":     mm.MC_DIR + "/versions/"
}

MODS_DATA_PATH = {      # расположение инфы о моде (имени) внутри .jar файла
    "forge": "META-INF/mods.toml",
    "fabric": "fabric.mod.json"
}


#=========================================================               =========================================================
#========================================================= PATH CHECKING =========================================================
#=========================================================               =========================================================

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


POPUP_WINDOW = None # Позже (в main) приравняется к PopupWindow() это просто заполнитель


#=========================================================               =========================================================
#========================================================= CONFIGS SETUP =========================================================
#=========================================================               =========================================================

player_data = configs_manager.Config(LAUNCHER_DIRS["player_data"], {
                                            "Player":              "__dir__",
                                            "Player.username":     "player",
                                            "Player.path_num":     2,
                                            "Mojang":              "__dir__",
                                            "Mojang.have_licence": 0,
                                            "Mojang.access_code":  "",
                                            "Mojang.uuid":         "",
                                            "Mojang.crypto_vi":    "",
                                            "Java":                "__dir__",
                                            "Java.args":           ""
                                        })
vlaunchers_data = configs_manager.Config(LAUNCHER_DIRS["vlaunchers_data"], {
                                            "vlaunchers":          "__dir__"
                                        })

CONFIG_MANAGER = configs_manager.ConfigManager(player=player_data, \
                                               vlaunchers=vlaunchers_data)

#=========================================================           =========================================================
#========================================================= Functions =========================================================
#=========================================================           =========================================================

def encode_str(secret_key, iv_base64, text) -> str:
    """Encrypt a string using the secret key and IV.

    Args:
        secret_key (bytes): [secret encrypt key]
        iv_base64 (str): [base64 encrypt vector]
        text ([type]): [description]

    Returns:
        str: [encrypted data]
    """    
    
    obj = AES.new(secret_key, AES.MODE_CFB, base64.b64decode(iv_base64))
    
    encrypted_text = obj.encrypt(text.encode("utf8"))
    
    return base64.b64encode(encrypted_text).decode("utf-8")

def decode_str(secret_key, iv_base64, text_base64) -> str:
    """Decrypt a string using the secret key and IV.

    Args:
        secret_key (bytes): [secret encrypt key]
        iv_base64 (str): [base64 encrypt vector]
        text_base64 (str): [base64 encrypted data]

    Returns:
        str: [decrypted data]
    """    
    
    obj = AES.new(secret_key, AES.MODE_CFB, base64.b64decode(iv_base64))
    
    decrypted_text = obj.decrypt(base64.b64decode(text_base64))
    
    return decrypted_text.decode("utf-8")

def excepthook(exc_type, exc_value, exc_tb):
    """Called when an exception is raised.
    """    
    
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"CRITICAL ERROR: {tb}")
    print("--This window will be closed in 200 seconds--")
    time.sleep(200)
    QtWidgets.QApplication.quit()


#=========================================================              =========================================================
#========================================================= Data Classes =========================================================
#=========================================================              =========================================================

# пока что ничего

#=========================================================              =========================================================
#========================================================= LaunchThread =========================================================
#=========================================================              =========================================================

class LaunchThread(QThread): # работа с minecraft_manager в отдельном потоке, что бы не стопить взаимодействие с интерфейсом
    """Creating separate stream for downloading and running mc.
    """

    launch_setup_signal = pyqtSignal(str, str, str, str, int, str) # см. launch_setup функцию
    progress_update_signal = pyqtSignal(int, int, str)        # progress, progress_max, progress_label
    run_complete_callback = pyqtSignal(int)                   # exit code

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

    def launch_setup(self, version_id:str, username:str, access_code:str, uuid:str, _type:int, args:str):
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
        self.access_code = access_code
        self.uuid = uuid
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
                
                if POPUP_WINDOW: 
                    POPUP_WINDOW.update("Error", f"Failed to install Minecraft version [ {self.version_id} ] because [ {err} ]")


                self.run_complete_callback.emit(-2)
                return -2
        elif self.run_type == 0:
            mlauncher = mm.MinecraftVersionLauncher(self.username, self.version_id, access_token=self.access_code, uuid=self.uuid)

            mlauncher.start_minecraft_version([self.jvm_args])

            self.run_complete_callback.emit(0)


#========================================================= Windows Classes ==================================================


#=========================================================                =========================================================
#========================================================= DownloadWindow =========================================================
#=========================================================                =========================================================

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


#=========================================================            =========================================================
#========================================================= EditWindow =========================================================
#=========================================================            =========================================================

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
                    CONFIG_MANAGER.update_config_data(f"vlaunchers.vlaunchers.{i[0]}.version", \
                                                               i[0], update_save=True)
                    
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
        
        if self.ui.comboBox_avalableVersions.currentText() != self.current_vlauncher_data['version']:
            CONFIG_MANAGER.update_config_data(f"vlaunchers.vlaunchers.{self.current_vlauncher_index}.version", \
                                                               self.ui.comboBox_avalableVersions.currentText(), update_save=True)
                
        self.hide()


#=========================================================              =========================================================
#========================================================= CreateWindow =========================================================
#=========================================================              =========================================================

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


#=========================================================             =========================================================
#========================================================= LogInWindow =========================================================
#=========================================================             =========================================================

class LogInWindow(QtWidgets.QMainWindow):
    """Class for microsoft login window.
    """    
    
    succesfull_login = pyqtSignal(str)
    
    def __init__(self):
        super(LogInWindow, self).__init__()
        self.ui = Ui_LogInWindow()
        self.ui.setupUi(self)
        
        self.setWindowTitle("Log In")
        
        self.ui.button_login.clicked.connect(self.onClick_login)
        self.ui.button_cancel.clicked.connect(self.onClick_cancel)
    
    def onClick_login(self):
        """Callback thar is called when the user clicks on the login button
        """        
        
        login = self.ui.line_login.text().replace(" ", "")
        password = self.ui.line_password.text().replace(" ", "")
        
        if (login == "" or password == ""): 
            return
        
        try:
            print("====================== Connecting to Mojang servers ======================")
            
            client = Client(login, password)
        except Exception as err:
            print(f"ERROR. Login failed. Error: {err}")
            if POPUP_WINDOW: 
                POPUP_WINDOW.update("Error", f"Login failed. Error: {err}")
            return
        
        profile = client.get_profile()
        
        print("====================== Save data ======================")
        
        CONFIG_MANAGER.update_config_data("player.Player.username", profile.name)
        CONFIG_MANAGER.update_config_data("player.Mojang.have_licence", str(1))
        
        print("====================== Save crypted data ======================")
        
        CONFIG_MANAGER.update_config_data("player.Mojang.access_code", encode_str(SECRET_CRYPTO_KEY, \
                                                                            CONFIG_MANAGER.get_config("player.Mojang.crypto_vi"), \
                                                                            str(client.bearer_token)))
        CONFIG_MANAGER.update_config_data("player.Mojang.uuid", str(profile.id), update_save=True)
        
        self.succesfull_login.emit(profile.name)
    
    def onClick_cancel(self):
        """Hide the window.
        """        
        
        self.hide()


#=========================================================            =========================================================
#========================================================= MainWindow =========================================================
#=========================================================            =========================================================

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
        self.ui.button_microsoftAccount.setIcon(QIcon(ASSETS_DIRS["microsoft_icon"]))
        

        installed_versions = mm.get_installed_versions()

        for i in installed_versions:
            self.ui.comboBox_avalableVersions.addItem(f"{i[0]}{(i[1] != 'release')*(' - '+i[1])}")

        self.ui.comboBox_avalableVersions.currentIndexChanged.connect(self.onChanged_version)
        
        self.ui.comboBox_avalableTypes.addItem("Installed")
        self.ui.comboBox_avalableTypes.addItem("VLaunchers")
        self.ui.comboBox_avalableTypes.currentTextChanged.connect(self.onChanged_type)

        self.username = str(CONFIG_MANAGER.get_config("player.Player.username"))

        self.ui.lineEdit.setText(self.username)
        self.ui.lineEdit.editingFinished.connect(self.save_username)

        self.download_window = DownloadWindow()
        self.download_window.setWindowTitle("Downloading")

        self.create_window = CreateWindow()
        self.create_window.setWindowTitle("Create new")
        self.create_window.onClick_create.connect(self.install)
        
        self.edit_window = EditWindow()
        self.edit_window.setWindowTitle("Edit")
        
        self.login_window = LogInWindow()
        self.login_window.setWindowTitle("Log In")
        self.login_window.succesfull_login.connect(self.succesful_login)
        self.ui.button_microsoftAccount.clicked.connect(self.login_window.show)

        with open(CSS_STYLESHEET, "r") as f:
            css = f.read()

            self.setStyleSheet(css)
            self.download_window.setStyleSheet(css)
            self.create_window.setStyleSheet(css)
            self.edit_window.setStyleSheet(css)
            self.login_window.setStyleSheet(css)
            if POPUP_WINDOW: 
                POPUP_WINDOW.setStyleSheet(css)

        self.launch_thread = LaunchThread()
        self.launch_thread.progress_update_signal.connect(self.update_progress)
        self.launch_thread.run_complete_callback.connect(self.run_callback)
        
        if CONFIG_MANAGER.get_config("player.Mojang.have_licence") == "1":
            client = Client(bearer_token=str(decode_str(SECRET_CRYPTO_KEY, \
                                                    CONFIG_MANAGER.get_config("player.Mojang.crypto_vi"), \
                                                    CONFIG_MANAGER.get_config("player.Mojang.access_code"))))
            
            profile = client.get_profile()
            
            CONFIG_MANAGER.update_config_data("player.Player.username", profile.name)
            CONFIG_MANAGER.update_config_data("player.Mojang.uuid", profile.id)
            CONFIG_MANAGER.update_config_data("player.Mojang.have_licence", str(1))
            CONFIG_MANAGER.update_config_data("player.Mojang.access_code", encode_str(SECRET_CRYPTO_KEY, \
                                                                                CONFIG_MANAGER.get_config("player.Mojang.crypto_vi"), \
                                                                                str(client.bearer_token)), update_save=True)
            
            self.ui.button_microsoftAccount.setToolTip(f"You are already logged in\nProfile ID: {profile.id}")
            self.ui.lineEdit.setEnabled(False)

        if int(CONFIG_MANAGER.get_config("player.Player.path_num")) != PATH_NUM: # type: ignore
            CONFIG_MANAGER.update_config_data("player.Player.path_num", str(PATH_NUM))

        self.username = str(CONFIG_MANAGER.get_config("player.Player.username"))
        
        self.ui.lineEdit.setText(self.username)

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
            
            match _type:
                case 1:
                    splitted = version.split("-")

                    data_version = splitted[0] + "-forge-" + splitted[1]
                case 2:
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

            CONFIG_MANAGER.update_config_data("vlaunchers.vlaunchers", new_vlauncher, write_type="append.list")

        self.launch_thread.launch_setup_signal.emit(version, self.username, "", "", _type+1, CONFIG_MANAGER.get_config("player.Java.args"))
        self.launch_thread.start()

    def succesful_login(self, username:str):
        """Saves username.

        Args:
            username (str)
        """      
        
        self.login_window.hide()       
        
        POPUP_WINDOW.update("Success", "You have successfully logged in")
        self.ui.button_microsoftAccount.setToolTip(f"You are already logged in\nProfile ID: {CONFIG_MANAGER.get_config('player.Mojang.uuid')}")
        self.ui.lineEdit.setEnabled(False)
        
        self.username = username

        self.ui.lineEdit.setText(self.username)
    
    def save_username(self):
        """Save username to config file .
        """
        
        CONFIG_MANAGER.update_config_data("player.Player.username", self.ui.lineEdit.text())

        self.username = self.ui.lineEdit.text()

    def run_callback(self, code:int):
        """Callback when run function in LaunchThread ended.

        Args:
            code [int]: [0 - mc closed
                         1 - created new version
                         errors:
                         -2 - error while creating new version]
        """

        match code:
            case 0:
                if self.current_mods != []:
                    deleted_mods = os.listdir(LAUNCHER_DIRS["mc_mods"])

                    for i in deleted_mods:
                        if i.split(".")[-1] == "jar":
                            os.remove(LAUNCHER_DIRS["mc_mods"]+i)
                    self.current_mods = []

                self.show()
            case 1:
                self.update_versions_comboBox()

                self.download_window.hide()
                self.create_window.hide()
                
                if POPUP_WINDOW: 
                    POPUP_WINDOW.update("Complete", f"Version download complete")
            case -2:
                self.download_window.hide()
                self.create_window.hide()

    def onClick_start(self):
        """Start the mc launch
        """

        self.hide()
        
        code = ""
        if int(CONFIG_MANAGER.get_config("player.Mojang.have_licence")) == 1: # type: ignore
            code = decode_str(SECRET_CRYPTO_KEY, \
                                CONFIG_MANAGER.get_config("player.Mojang.crypto_vi"), \
                                CONFIG_MANAGER.get_config("player.Mojang.access_code"))

        if self.ui.comboBox_avalableTypes.currentIndex() == 0:
            self.launch_thread.launch_setup_signal.emit(mm.get_installed_versions()[self.ui.comboBox_avalableVersions.currentIndex()][0], \
                                                        self.username, code, CONFIG_MANAGER.get_config("player.Mojang.uuid"), \
                                                        0, CONFIG_MANAGER.get_config("player.Java.args"))
            self.launch_thread.start()
        elif self.ui.comboBox_avalableTypes.currentIndex() == 1:
            version = CONFIG_MANAGER.get_config("vlaunchers.vlaunchers")[self.ui.comboBox_avalableVersions.currentIndex()] # type: ignore

            if not isinstance(version, dict): 
                return
            
            if version['type'] == "fabric":
                if not "fabric-loader-" in version['version']:
                    ver_to_parse = mm.get_installed_versions()

                    for i in ver_to_parse:
                        if version['version'] in i[0] and "fabric-loader-" in i[0]:
                            CONFIG_MANAGER.update_config_data(f"vlaunchers.vlaunchers.{self.ui.comboBox_avalableVersions.currentIndex()}.version", \
                                                               i[0], update_save=True)
                            version['version'] = i[0]

            old_mods = os.listdir(LAUNCHER_DIRS["mc_mods"])

            for i in old_mods:
                if i.split(".")[-1] == "jar":
                    shutil.move(LAUNCHER_DIRS["mc_mods"]+"/"+i, \
                                LAUNCHER_DIRS["mc_old_mods"]+i.split("/")[-1])

            self.current_mods = os.listdir(LAUNCHER_DIRS["vlaunchers"]+version['name'])

            for i in self.current_mods:
                shutil.copyfile(LAUNCHER_DIRS["vlaunchers"]+version['name']+"/"+i, \
                                LAUNCHER_DIRS["mc_mods"]+i.split("/")[-1])

            self.launch_thread.launch_setup_signal.emit(version['version'], self.username, code, CONFIG_MANAGER.get_config("player.Mojang.uuid"), 0, CONFIG_MANAGER.get_config("player.Java.args"))
            self.launch_thread.start()

    def onClick_check(self):
        """Callback when the user clicks the check (or edit) button
        """
        match self.ui.comboBox_avalableTypes.currentIndex():
            case 0:
                self.download_window.show()

                self.launch_thread.launch_setup_signal.emit(mm.get_installed_versions()\
                                                            [self.ui.comboBox_avalableVersions.currentIndex()][0], \
                                                            self.username, "", "", \
                                                            1, CONFIG_MANAGER.get_config("player.Java.args"))
                self.launch_thread.start()
            case 1:
                vlauncher_data = CONFIG_MANAGER.get_config("vlaunchers.vlaunchers")[self.ui.comboBox_avalableVersions.currentIndex()] # type: ignore

                if not isinstance(vlauncher_data, dict): 
                    return
                
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
        match self.ui.comboBox_avalableTypes.currentIndex():
            case 0:
                shutil.rmtree(LAUNCHER_DIRS["mc_versions"]+mm.get_installed_versions()\
                            [self.ui.comboBox_avalableVersions.currentIndex()][0])

                self.update_versions_comboBox()
            case 1:
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

        match self.ui.comboBox_avalableTypes.currentIndex():
            case 0:
                self.ui.button_check.setText("Check")
            case 1:
                self.ui.button_check.setText("Edit")
    
    def onChanged_version(self):
        """Callback when version changed.
        """        
        
        if "-forge-" in self.ui.comboBox_avalableVersions.currentText() or \
            "fabric-loader-" in self.ui.comboBox_avalableVersions.currentText():

            self.ui.button_check.setEnabled(False)
        else:
            self.ui.button_check.setEnabled(True)

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

        match self.ui.comboBox_avalableTypes.currentIndex():
            case 0:
                installed_versions = mm.get_installed_versions()
                self.ui.comboBox_avalableVersions.clear()

                for i in installed_versions:
                    self.ui.comboBox_avalableVersions.addItem(f"{i[0]}{(i[1] != 'release')*(' - '+i[1])}")
            case 1:
                installed_versions = CONFIG_MANAGER.get_config("vlaunchers.vlaunchers") # type: ignore

                if not isinstance(installed_versions, list): 
                    return
                
                self.ui.comboBox_avalableVersions.clear()

                for i in installed_versions:
                    self.ui.comboBox_avalableVersions.addItem(f"{i['name']} - {i['type']}")


if __name__ == "__main__":
    print("====================== Launcher is loading ======================")
    
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
    
    POPUP_WINDOW = PopupWindow()
    POPUP_WINDOW.setup("Test", f"Test")
    
    CONFIG_MANAGER.check_config_struct("player")
    
    if CONFIG_MANAGER.get_config("player.Mojang.crypto_vi") == "":
        CONFIG_MANAGER.update_config_data("player.Mojang.crypto_vi", base64.b64encode(os.urandom(16)).decode("utf-8"), update_save=True)
        
        if CONFIG_MANAGER.get_config("player.Mojang.have_licence") == "1":
            CONFIG_MANAGER.update_config_data("player.Mojang.have_licence", 0)
            CONFIG_MANAGER.update_config_data("player.Mojang.access_code", "")
            
            POPUP_WINDOW.update("No crypto", "You need to log in again, as your access code has not been encrypted")
    
    application = MainWindow()
    application.show()
    
    sys.excepthook = excepthook
    
    ext = app.exec()
    
    sys.exit(ext)

# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace, no-name-in-module, unused-import

"""Main script
"""

import time
import configparser
import base64, traceback
import io, sys, os
import shutil, zipfile, json, tomli
from requests.exceptions import ConnectionError
from tkinter import filedialog
from mojang import Client, errors
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from Crypto.Cipher import AES
from dir_data import LAUNCHER_DIRS, CSS_STYLESHEET, INITAL_DIRS, ASSETS_DIRS, PATH_NUM
import configs_manager
from assets.ui.structure.main_ui import          Ui_MainWindow
from assets.ui.windows.DownloadWindow import DownloadWindow
from assets.ui.windows.EditWindow     import EditWindow
from assets.ui.windows.CreateWindow   import CreateWindow
from assets.ui.windows.LogInWindow    import LogInWindow
from assets.animated_ui import PopupWindow
import minecraft_manager as mm
import mc_mod_manager as mcmm


#=========================================================            =========================================================
#========================================================= Constants  =========================================================
#=========================================================            =========================================================

SECRET_CRYPTO_KEY = b'Z\xc9\xd0\x16\xaf\x01\x85\x0e\xff\x9f\xd7\x96$\x0b\xe6\xcb\xfco\xe2\x85\xc5\xebUC\xb1E\xc72L\xa3\rJ'


#=========================================================               =========================================================
#========================================================= PATH CHECKING =========================================================
#=========================================================               =========================================================

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
                                            "Java.args":           "",
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

            mlauncher.start_minecraft_version(self.jvm_args)

            self.run_complete_callback.emit(0)


#========================================================= Windows Classes ==================================================

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
        
        self.ui.comboBox_avalableTypes.addItem("Installed")
        self.ui.comboBox_avalableTypes.addItem("VLaunchers")
        self.ui.comboBox_avalableTypes.currentTextChanged.connect(self.onChanged_type)

        self.username = str(CONFIG_MANAGER.get_config("player.Player.username"))

        self.ui.lineEdit.setText(self.username)
        self.ui.lineEdit.editingFinished.connect(self.save_username)

        self.launch_thread = LaunchThread()
        self.launch_thread.progress_update_signal.connect(self.update_progress)
        self.launch_thread.run_complete_callback.connect(self.run_callback)
        
        if CONFIG_MANAGER.get_config("player.Mojang.have_licence") == "1":
            try:
                client = None
                
                try:
                    client = Client(bearer_token=str(decode_str(SECRET_CRYPTO_KEY, \
                                                            CONFIG_MANAGER.get_config("player.Mojang.crypto_vi"), \
                                                            CONFIG_MANAGER.get_config("player.Mojang.access_code"))))
                except (errors.TooManyRequests, ConnectionError):
                    reconnect_try = 0
                    
                    while 1:
                        try: 
                            reconnect_try += 1
                            client = Client(bearer_token=str(decode_str(SECRET_CRYPTO_KEY, \
                                                            CONFIG_MANAGER.get_config("player.Mojang.crypto_vi"), \
                                                            CONFIG_MANAGER.get_config("player.Mojang.access_code"))))

                            break
                        except (errors.TooManyRequests, ConnectionError) as e:
                            if reconnect_try >= 10:
                                print("ERROR: Too many requests. Retry later")
                                time.sleep(10)
                                
                                sys.exit(0)
                            
                            retry_time = 5
                            if isinstance(e, errors.TooManyRequests):
                                retry_time = 10
                                
                            error = str(type(e))
                            
                            time_to_sleep = retry_time
                            sys.stdout.write(f"\rERROR: Bad server request. Retrying in {time_to_sleep} seconds. Retry try: {reconnect_try}")
                            
                            for i in range(retry_time):
                                time.sleep(1)
                                time_to_sleep -= 1
                                sys.stdout.write(f"\rERROR: Bad server request. Retrying in {time_to_sleep} seconds. Retry try: {reconnect_try}")
                
                print()
                profile = client.get_profile()

                CONFIG_MANAGER.update_config_data("player.Player.username", profile.name)
                CONFIG_MANAGER.update_config_data("player.Mojang.uuid", profile.id)
                CONFIG_MANAGER.update_config_data("player.Mojang.have_licence", str(1))
                CONFIG_MANAGER.update_config_data("player.Mojang.access_code", encode_str(SECRET_CRYPTO_KEY, \
                                                                                    CONFIG_MANAGER.get_config("player.Mojang.crypto_vi"), \
                                                                                    str(client.bearer_token)), update_save=True)
                
                self.ui.button_microsoftAccount.setToolTip(f"You are already logged in\nProfile ID: {profile.id}")
                self.ui.lineEdit.setEnabled(False)
            except errors.MissingMinecraftLicense:
                print("ERROR: Your login code has expired. Please log in again.")
                if POPUP_WINDOW:
                    POPUP_WINDOW.update("Code has expired", "Your login code has expired. Please log in again.")
                
                CONFIG_MANAGER.update_config_data("player.Mojang.have_licence", str(0))
         
            
        installed_versions = mm.get_installed_versions()

        for i in installed_versions:
            self.ui.comboBox_avalableVersions.addItem(f"{i[0]}{(i[1] != 'release')*(' - '+i[1])}")

        self.ui.comboBox_avalableVersions.currentIndexChanged.connect(self.onChanged_version)
        
        enabled = len(installed_versions) != 0
        self.ui.button_check.setEnabled(enabled)
        self.ui.button_delete.setEnabled(enabled)


        if int(CONFIG_MANAGER.get_config("player.Player.path_num")) != PATH_NUM: # type: ignore
            CONFIG_MANAGER.update_config_data("player.Player.path_num", str(PATH_NUM))

        self.username = str(CONFIG_MANAGER.get_config("player.Player.username"))
        
        self.ui.lineEdit.setText(self.username)
        
        
        self.download_window = DownloadWindow()
        self.download_window.setWindowTitle("Downloading")

        self.create_window = CreateWindow()
        self.create_window.setWindowTitle("Create new")
        self.create_window.onClick_create.connect(self.install)
        
        self.edit_window = EditWindow(CONFIG_MANAGER)
        self.edit_window.setWindowTitle("Edit")
        
        self.login_window = LogInWindow(CONFIG_MANAGER, encode_str, SECRET_CRYPTO_KEY, POPUP_WINDOW)
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
                
                enabled = len(installed_versions) != 0
                self.ui.button_check.setEnabled(enabled)
                self.ui.button_delete.setEnabled(enabled)
                    
            case 1:
                installed_versions = CONFIG_MANAGER.get_config("vlaunchers.vlaunchers") # type: ignore

                if not isinstance(installed_versions, list): 
                    return
                
                self.ui.comboBox_avalableVersions.clear()

                for i in installed_versions:
                    self.ui.comboBox_avalableVersions.addItem(f"{i['name']} - {i['type']}")
                
                enabled = len(installed_versions) != 0
                self.ui.button_check.setEnabled(enabled)
                self.ui.button_delete.setEnabled(enabled)


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

# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace, no-name-in-module, unused-import

import sys, time
from assets.ui.structure.log_in_window_ui import Ui_LogInWindow
from requests.exceptions import ConnectionError
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from mojang import Client, errors

class LogInWindow(QtWidgets.QMainWindow):
    """Class for microsoft login window.
    """    
    
    succesfull_login = pyqtSignal(str)
    
    def __init__(self, CONFIG_MANAGER, encode_str_func, SECRET_CRYPTO_KEY, POPUP_WINDOW=None):
        super(LogInWindow, self).__init__()
        self.ui = Ui_LogInWindow()
        self.ui.setupUi(self)
        
        self.encode_str_func = encode_str_func
        self.SECRET_CRYPTO_KEY = SECRET_CRYPTO_KEY
        self.CONFIG_MANAGER = CONFIG_MANAGER
        self.POPUP_WINDOW = POPUP_WINDOW
        
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
        
        client = None
                
        try:
            print("====================== Get data ======================")
            client = Client(email=login, password=password)
        except (errors.TooManyRequests, ConnectionError):
            reconnect_try = 0
            
            while 1:
                try: 
                    reconnect_try += 1
                    client = Client(email=login, password=password)
                    
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
        
        print("====================== Save data ======================")
        
        self.CONFIG_MANAGER.update_config_data("player.Player.username", profile.name)
        self.CONFIG_MANAGER.update_config_data("player.Mojang.have_licence", str(1))
        
        print("====================== Save crypted data ======================")
        
        self.CONFIG_MANAGER.update_config_data("player.Mojang.access_code", self.encode_str_func(self.SECRET_CRYPTO_KEY, \
                                                                            self.CONFIG_MANAGER.get_config("player.Mojang.crypto_vi"), \
                                                                            str(client.bearer_token)))
        self.CONFIG_MANAGER.update_config_data("player.Mojang.uuid", str(profile.id), update_save=True)
        
        self.succesfull_login.emit(profile.name)
    
    def onClick_cancel(self):
        """Hide the window.
        """        
        
        self.hide()

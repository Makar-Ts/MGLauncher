# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace, no-name-in-module, unused-import


import os, shutil
from tkinter import filedialog
from dir_data import LAUNCHER_DIRS
from assets.ui.structure.edit_menu_ui import Ui_EditWindow
from PyQt5 import QtWidgets
import minecraft_manager as mm
import mc_mod_manager as mcmm

class EditWindow(QtWidgets.QMainWindow):
    """Window for editing already existing vlaunchers.
    """    
    
    mods_selected = []
    current_vlauncher_data = {}
    current_vlauncher_index = 0
    
    def __init__(self, CONFIG_MANAGER):
        self.CONFIG_MANAGER = CONFIG_MANAGER
        
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
                    self.CONFIG_MANAGER.update_config_data(f"vlaunchers.vlaunchers.{i[0]}.version", \
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
            self.CONFIG_MANAGER.update_config_data(f"vlaunchers.vlaunchers.{self.current_vlauncher_index}.version", \
                                                               self.ui.comboBox_avalableVersions.currentText(), update_save=True)
                
        self.hide()

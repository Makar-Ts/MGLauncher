# pylint: disable=line-too-long, invalid-name, import-error, multiple-imports, unspecified-encoding, broad-exception-caught, trailing-whitespace, no-name-in-module, unused-import

from tkinter import filedialog
from assets.ui.structure.create_menu_ui import Ui_CreateWindow
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
import minecraft_manager as mm
import mc_mod_manager as mcmm

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

        for i in versions: # type: ignore
            self.ui.comboBox_avalableTypes.addItem(i[0])

        self.ui.comboBox_avalableVersions.addItem("Vanilla")
        self.ui.comboBox_avalableVersions.addItem("Forge")
        self.ui.comboBox_avalableVersions.addItem("Fabric")
        self.ui.comboBox_avalableVersions.currentIndexChanged\
                                         .connect(self.onChanged_avalableVersions)
                                         
        self.ui.comboBox_avalableSubTypes.hide()
        
        self.ui.comboBox_avalableTypes.currentIndexChanged.connect(self.onChanged_avalableTypes)

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
        self.ui.comboBox_avalableSubTypes.setEnabled(False)
        self.ui.comboBox_avalableVersions.setEnabled(False)
        self.onClick_create.emit(self.ui.comboBox_avalableTypes.currentText()+"-"+self.ui.comboBox_avalableSubTypes.currentText(), \
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

    def onChanged_avalableTypes(self):
        if self.ui.comboBox_avalableVersions.currentIndex() != 1: 
            return
        
        versions = mm.get_all_versions(1.1)
        self.ui.comboBox_avalableSubTypes.clear()
        self.ui.comboBox_avalableSubTypes.show()
            
        for j in versions[self.ui.comboBox_avalableTypes.currentIndex()]["minor"]: #type: ignore
            self.ui.comboBox_avalableSubTypes.addItem(j)
    
    def onChanged_avalableVersions(self):
        """Called when the user has changed the version.
        """

        self.mods_selected.clear()
        self.ui.list_mods.clear()

        if self.ui.comboBox_avalableVersions.currentIndex() == 0:
            versions = mm.get_all_versions()
            self.ui.comboBox_avalableTypes.clear()
            self.ui.comboBox_avalableSubTypes.hide()

            for i in versions: #type: ignore
                self.ui.comboBox_avalableTypes.addItem(i[0])

            self.ui.button_mod_add.setEnabled(False)
            self.ui.button_mod_remove.setEnabled(False)
            self.ui.line_launcherName.setEnabled(False)
        else:
            self.ui.button_mod_add.setEnabled(True)
            self.ui.button_mod_remove.setEnabled(True)
            self.ui.line_launcherName.setEnabled(True)

            index = self.ui.comboBox_avalableVersions.currentIndex()
            
            match index:
                case 1:
                    versions = mm.get_all_versions(1.1)
                    self.ui.comboBox_avalableTypes.clear()

                    for i in versions: #type: ignore
                        self.ui.comboBox_avalableTypes.addItem(i["major"]) #type: ignore
                case 2:
                    versions = mm.get_all_versions(2)
                    self.ui.comboBox_avalableTypes.clear()
                    self.ui.comboBox_avalableSubTypes.hide()

                    for i in versions: #type: ignore
                        self.ui.comboBox_avalableTypes.addItem(i[0])

    def reset(self):
        """Reset the state of the editor to its initial state.
        """

        self.mods_selected = []
        self.ui.list_mods.clear()

        self.ui.button_create.setEnabled(True)
        self.ui.comboBox_avalableTypes.setEnabled(True)
        self.ui.comboBox_avalableSubTypes.setEnabled(True)
        self.ui.comboBox_avalableSubTypes.hide()
        self.ui.comboBox_avalableVersions.setEnabled(True)

        self.ui.comboBox_avalableVersions.setCurrentIndex(0)
        self.ui.line_launcherName.setText("")

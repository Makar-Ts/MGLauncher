from PyQt5 import QtWidgets
from assets.ui.structure.download_menu_ui import Ui_DownloadWindow

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
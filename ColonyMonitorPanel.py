from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure



class ColonyMonitorPanel(QtWidgets.QMainWindow):

    def __init__(self, main, n_antennas=4, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.main = main
        self.__n_antennas = n_antennas
        self._setupUi(self)

    def _setupUi(self, MainWindow):
        self.ColoMonitorWindow = QtWidgets.QWidget(MainWindow)

        self.verticalLayout = QtWidgets.QVBoxLayout(self.ColoMonitorWindow)
        self.verticalLayout.setContentsMargins(48, 24, 48, 24)
        self.verticalLayout.setObjectName("verticalLayout")

        self.MainGrid = QtWidgets.QGridLayout()
        self.MainGrid.setHorizontalSpacing(24)
        self.MainGrid.setVerticalSpacing(36)

        # --------------------------------------------------------------------------------------------------------------#

        self.in_colony_graph = MplCanvas(self, width=5, height=4, dpi=100)
        self.MainGrid.addWidget(self.in_colony_graph, 0, 0, 1, 1)

        self.transitions_graph = MplCanvas(self, width=5, height=4, dpi=100)
        self.MainGrid.addWidget(self.transitions_graph, 1, 0, 1, 1)


        # --------------------------------------------------------------------------------------------------------------#
        self.verticalLayout.addLayout(self.MainGrid)
        MainWindow.setCentralWidget(self.ColoMonitorWindow)
        self.layout = QtWidgets.QGridLayout()


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


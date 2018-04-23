# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Tabbed container with all plot widgets
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import logging
logger = logging.getLogger(__name__)

import importlib
from ..compat import QTabWidget, QVBoxLayout, QEvent, QtCore, pyqtSlot, pyqtSignal

from pyfda.pyfda_rc import params

plot_wdg_lst = ['Plot_Hf', 'Plot_Phi']#[ 'Plot_Phi', 'Plot_PZ', 'Plot_Tau_G', 'Plot_Impz', 'Plot_3D']
plot_wdg_dir = 'plot_widgets'
from pyfda.plot_widgets import (plot_pz, plot_tau_g, plot_impz, plot_3d)

#------------------------------------------------------------------------------
class PlotTabWidgets(QTabWidget):

    # incoming, connected to input_tab_widget.sig_tx in pyfdax    
    sig_rx = pyqtSignal(object)
    # outgoing: emitted by process_signals  
    sig_tx = pyqtSignal(object)
    
    def __init__(self, parent):
        super(PlotTabWidgets, self).__init__(parent)
        self._construct_UI()

#------------------------------------------------------------------------------
    def _construct_UI(self):
        """ 
        Initialize UI with tabbed subwidgets and connect the signals of all
        subwidgets. Plot widgets are not sending back anything (yet), hence no
        need to connect self.sig_rx to the subwidgets
        """
        tabWidget = QTabWidget(self)
        tabWidget.setObjectName("plot_tabs")
        #
        for i, plot_wdg in enumerate(plot_wdg_lst):
            plot_mod_name = 'pyfda.' + plot_wdg_dir + '.' + plot_wdg.lower()
            try:  # Try to import the module from the  package and get a handle:
                plot_mod = importlib.import_module(plot_mod_name)
                plot_class = getattr(plot_mod, plot_wdg, None)
                plot_inst = plot_class(self)
                if hasattr(plot_inst, 'tab_label'):
                    tabWidget.addTab(plot_inst, plot_inst.tab_label)
                else:
                    tabWidget.addTab(plot_inst, str(i))
                if hasattr(plot_inst, 'tool_tip'):
                    tabWidget.setTabToolTip(i, plot_inst.tool_tip)
                if hasattr(plot_inst, 'sig_tx'):
                    plot_inst.sig_tx.connect(self.sig_rx)
                if hasattr(plot_inst, 'sig_rx'):
                    self.sig_tx.connect(plot_inst.sig_rx)

            except ImportError as e:
                logger.warning('Plotting module "{0}" could not be imported.\n{1}'\
                               .format(plot_mod_name, e))
                continue
            except Exception as e:
                logger.warning("Unexpected error during module import:\n{0}".format(e))
                continue

# =============================================================================
#         self.pltHf = plot_hf.PlotHf(self)
#         self.sig_tx.connect(self.pltHf.sig_rx)
#         tabWidget.addTab(self.pltHf, '|H(f)|')
#         tabWidget.setTabToolTip(0, "Magnitude and phase frequency response")
#         #
# =============================================================================
# =============================================================================
#         self.pltPhi = plot_phi.PlotPhi(self)
#         self.sig_tx.connect(self.pltPhi.sig_rx)
#         tabWidget.addTab(self.pltPhi, 'phi(f)')
#         tabWidget.setTabToolTip(1, "Phase frequency response")
#         #
# =============================================================================
        self.pltPZ = plot_pz.PlotPZ(self)
        self.sig_tx.connect(self.pltPZ.sig_rx)
        tabWidget.addTab(self.pltPZ, 'P/Z')
        tabWidget.setTabToolTip(2, "Pole / zero plan")
        #
        self.pltTauG = plot_tau_g.PlotTauG(self)
        self.sig_tx.connect(self.pltTauG.sig_rx)
        tabWidget.addTab(self.pltTauG, 'tau_g')
        tabWidget.setTabToolTip(3, "Group delay")
        #
        self.pltImpz = plot_impz.PlotImpz(self)
        self.sig_tx.connect(self.pltImpz.ui.sig_rx)
        tabWidget.addTab(self.pltImpz, 'h[n]')
        tabWidget.setTabToolTip(4, "Impulse and transient response")
        #
        self.plt3D = plot_3d.Plot3D(self)
        self.sig_tx.connect(self.plt3D.sig_rx)
        tabWidget.addTab(self.plt3D, '3D')
        tabWidget.setTabToolTip(5, "3D magnitude response |H(z)|")
        #
        layVMain = QVBoxLayout()
        layVMain.addWidget(tabWidget)
        layVMain.setContentsMargins(*params['wdg_margins'])#(left, top, right, bottom)

        self.setLayout(layVMain)
        
        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_signals)
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------        
        self.timer_id = QtCore.QTimer()
        self.timer_id.setSingleShot(True)
        # redraw current widget at timeout (timer was triggered by resize event):
        self.timer_id.timeout.connect(self.current_tab_redraw)

        # When user has selected a different tab, trigger a redraw of current tab
        tabWidget.currentChanged.connect(self.current_tab_redraw)
        # The following does not work: maybe current scope must be left?
        # tabWidget.currentChanged.connect(tabWidget.currentWidget().redraw)

        tabWidget.installEventFilter(self)
        
        
#    @pyqtSlot(object)
    def process_signals(self, dict_sig=None):
        """
        Process signals coming in via sig_rx
        """
        logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
        if type(dict_sig) != dict:
            dict_sig = {'sender':__name__}
        self.sig_tx.emit(dict_sig)

        """
        https://stackoverflow.com/questions/29128936/qtabwidget-size-depending-on-current-tab

        The QTabWidget won't select the biggest widget's height as its own height
        unless you use layout on the QTabWidget. Therefore, if you want to change
        the size of QTabWidget manually, remove the layout and call QTabWidget::resize
        according to the currentChanged signal.

        You can set the size policy of the widget that is displayed to QSizePolicy::Preferred
        and the other ones to QSizePolicy::Ignored. After that call adjustSize to update the sizes.
        
        void MainWindow::updateSizes(int index)
        {
        for(int i=0;i<ui->tabWidget->count();i++)
            if(i!=index)
                ui->tabWidget->widget(i)->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Ignored);

        ui->tabWidget->widget(index)->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Preferred);
        ui->tabWidget->widget(index)->resize(ui->tabWidget->widget(index)->minimumSizeHint());
        ui->tabWidget->widget(index)->adjustSize();
        resize(minimumSizeHint());
        adjustSize();
        }
        
        adjustSize(): The last two lines resize the main window itself. You might want to avoid it, 
        depending on your application. For example, if you set the rest of the widgets 
        to expand into the space just made available, it's not so nice if the window 
        resizes itself instead. 
        """

#------------------------------------------------------------------------------
        
    def current_tab_redraw(self):
        self.sig_tx.emit({'sender':__name__, 'tab_changed':True})
            
#------------------------------------------------------------------------------
    def eventFilter(self, source, event):
        """
        Filter all events generated by the QTabWidget. Source and type of all
         events generated by monitored objects are passed to this eventFilter,
        evaluated and passed on to the next hierarchy level.
        
        This filter stops and restarts a one-shot timer for every resize event.
        When the timer generates a timeout after 500 ms, current_tab_redraw is 
        called by the timer.
        """
        if isinstance(source, QTabWidget):
            if event.type() == QEvent.Resize:
                self.timer_id.stop()
                self.timer_id.start(500)

        # Call base class method to continue normal event processing:
        return super(PlotTabWidgets, self).eventFilter(source, event)
       
#------------------------------------------------------------------------

def main():
    import sys
    from pyfda import pyfda_rc as rc
    from ..compat import QApplication
    
    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)

    mainw = PlotTabWidgets(None)
    mainw.resize(300,400)
    
    app.setActiveWindow(mainw) 
    mainw.show()
    
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
# test with: python -m  pyfda.plot_widgets.plot_tab_widgets
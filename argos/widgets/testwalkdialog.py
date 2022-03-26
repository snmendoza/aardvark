# -*- coding: utf-8 -*-
# This file is part of Argos.
#
# Argos is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Argos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Argos. If not, see <http://www.gnu.org/licenses/>.

""" Contains the TestWalkDialog widget.
"""
import base64
import logging
import time
from typing import Optional, Tuple, List

from argos.qt import QtCore, QtGui, QtWidgets, QtSlot
from argos.widgets.constants import MONO_FONT, FONT_SIZE, COLOR_ERROR
from argos.widgets.misc import processEvents
from argos.utils.cls import check_is_a_sequence
from argos.utils.config import ConfigDict
from qt.misc import getWidgetGeom, getWidgetState
from utils.misc import wrapHtmlColor

logger = logging.getLogger(__name__)


# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201


class TestWalkDialog(QtWidgets.QDialog):
    """ Dialog that shows progress of test walk through the data and gives a summary when done.
    """
    def __init__(self, mainWindow, parent=None):
        """ Constructor

            Args:
                mainWindow: the Argos main window.
        """
        super(TestWalkDialog, self).__init__(parent=parent)
        self.setModal(False)

        self._isOngoing = False

        self._mainWindow = mainWindow

        self._currentTestName: Optional[str] = None
        self._results: List[Tuple[bool, str]] = []

        self.walkCurrentAction = QtWidgets.QAction("Walk Current Item", self)
        self.walkCurrentAction.setToolTip("Does a test walk on the currently selected tree item.")
        self.walkCurrentAction.triggered.connect(self.walkCurrentRepoNode)
        self.addAction(self.walkCurrentAction)

        self.walkAllAction = QtWidgets.QAction("Walk All Items", self)
        self.walkAllAction.setToolTip("Does a test walk on all tree nodes.")
        self.walkAllAction.triggered.connect(self.walkAllRepoNodes)
        self.addAction(self.walkAllAction)

        self.abortWalkAction = QtWidgets.QAction("Abort Walk", self)
        self.abortWalkAction.setToolTip("Aborts the current test walk.")
        self.abortWalkAction.triggered.connect(self.abortTestWalk)
        self.addAction(self.abortWalkAction)

        #################
        # Setup widgets #
        #################

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.controlLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(self.controlLayout)

        self.walkCurrentButton = QtWidgets.QToolButton()
        self.walkCurrentButton.setDefaultAction(self.walkCurrentAction)
        self.controlLayout.addWidget(self.walkCurrentButton)

        self.walkAllButton = QtWidgets.QToolButton()
        self.walkAllButton.setDefaultAction(self.walkAllAction)
        self.controlLayout.addWidget(self.walkAllButton)

        self.abortWalkButton = QtWidgets.QToolButton()
        self.abortWalkButton.setDefaultAction(self.abortWalkAction)
        self.controlLayout.addWidget(self.abortWalkButton)

        self.allInspectorsCheckBox = QtWidgets.QCheckBox("Test all Inspectors")
        self.controlLayout.addWidget(self.allInspectorsCheckBox)
        self.allDetailTabsCheckBox = QtWidgets.QCheckBox("Test all Detail-tabs")
        self.controlLayout.addWidget(self.allDetailTabsCheckBox)
        self.controlLayout.addStretch()

        self.curPathLabel = QtWidgets.QLabel()
        self.curPathLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.mainLayout.addWidget(self.curPathLabel)

        font = QtGui.QFont()
        font.setFamily(MONO_FONT)
        font.setFixedPitch(True)
        font.setPointSize(FONT_SIZE)

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(font)
        self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.editor.clear()
        self.mainLayout.addWidget(self.editor)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(buttonBox)

        self.resize(QtCore.QSize(800, 400))
        self._updateButtons()


    def marshall(self) -> Tuple[ConfigDict, ConfigDict]:
        """ Returns a layout and state config dictionaries
        """
        layoutCfg = dict(
            winGeom = base64.b64encode(getWidgetGeom(self)).decode('ascii'),
        )

        cfg = dict(
            testAllInspectors = self.allInspectorsCheckBox.isChecked(),
            testAllDetailTabs = self.allDetailTabsCheckBox.isChecked(),
        )
        return layoutCfg, cfg


    def unmarshall(self, layoutCfg, cfg):
        """ Initializes itself from a layout and config dict form the persistent settings.
        """
        if 'testAllInspectors' in cfg:
            self.allInspectorsCheckBox.setChecked(cfg['testAllInspectors'])

        if 'testAllDetailTabs' in cfg:
            self.allDetailTabsCheckBox.setChecked(cfg['testAllDetailTabs'])

        if 'winGeom' in layoutCfg:
            self.restoreGeometry(base64.b64decode(layoutCfg['winGeom']))


    def reject(self):
        """ Called when the user closes the dialog. Aborts any running test walk.
        """
        logger.debug("Closing TestWalkDialog")
        self.abortTestWalk()
        super().reject()


    def clear(self):
        """ Clear all test results and current test name.
        """
        self._currentTestName = None
        self._results = None
        self.editor.clear()


    def _updateButtons(self):
        """ Enables/disables buttons depending on if the test is ongaing
        """
        self.walkAllButton.setEnabled(not self._isOngoing)
        self.walkCurrentButton.setEnabled(not self._isOngoing)
        self.abortWalkButton.setEnabled(self._isOngoing)


    def appendText(self, text: str, isError: bool = False):
        """ Appends a text message to the editor.
        """
        if not isError:
            self.editor.appendPlainText(text)
        else:
            self.editor.appendHtml(wrapHtmlColor(text, COLOR_ERROR))


    @QtSlot(bool)
    def setTestResult(self, success: bool):
        """ Appends the currently selected path node to the list of tests.

            This slot will be called whenever the inspector or detail tab (properties, attributes,
            quicklook) updates itself.

            Setting the name and result are separate methods because the inspector and detail tab
            don't know which node is currently selected in the repo tree.
        """
        if not self._isOngoing:
            logger.debug("No test ongoing. Test result discarded.")
            return

        if self._currentTestName is None:
            # When we test also for different inspector or detail panels, the test with the
            # current inspector & panels is ignored because the same test will be repeated later
            # This prevents showing the same test result again but with a different name.
            logger.debug("Ignoring test with current inspector and detail panel")
            return

        # An inspector may be updated twice during a single test. For example, if a node was not
        # yet expanded, expanding will redraw the inspector for that node. In that case this
        # function will be called twice for the current test. We therefore merge these results.
        if self._results:
            prevSuccess, prevName = self._results[-1]
            if self._currentTestName == prevName:
                logger.debug("Ignoring duplicate test result: {}".format(self._currentTestName))
                # New result should be the same as the old, It should not matter if a node was
                # previously expanded or not.
                assert success == prevSuccess, \
                    "New result ({}) differs from old ({})".format(success, prevSuccess)
                return

        self._results.append((success, self._currentTestName))

        line = "{:8s}: {}".format("success" if success else "FAILED", self._currentTestName)
        logger.info("setTestResult: {}".format(line))
        self.appendText(line, isError=not success)


    @QtSlot()
    def abortTestWalk(self):
        """ Sets the flag to abort the test walk
        """
        self._isOngoing = False
        self._updateButtons()
        self.curPathLabel.setText("Test walk aborted!")


    @QtSlot()
    def walkCurrentRepoNode(self, allInspectors: bool=None, allDetailTabs: bool=None):
        """ Will visit all nodes below the currently selected node
        """
        logger.debug(f"walkCurrentRepoNode: {allInspectors} {allDetailTabs}")
        if allInspectors is not None:
            self.allInspectorsCheckBox.setChecked(allInspectors)

        if allDetailTabs is not None:
            self.allDetailTabsCheckBox.setChecked(allDetailTabs)

        curItem, _curIdx = self._mainWindow.repoWidget.repoTreeView.getCurrentItem()
        logger.info("Test walk current item: {}".format(curItem.nodePath))
        self.walkRepoNodes([curItem.nodePath])


    @QtSlot()
    def walkAllRepoNodes(self, allInspectors: bool=None, allDetailTabs: bool=None):
        """ Will visit all nodes in the repo tree.

            See walkRepoNodes docstring for more info
        """
        logger.info("testWalkAllNodes")
        if allInspectors is not None:
            self.allInspectorsCheckBox.setChecked(allInspectors)

        if allDetailTabs is not None:
            self.allDetailTabsCheckBox.setChecked(allDetailTabs)

        repo = self._mainWindow.repoWidget.repoTreeView.model()
        nodePaths = [rti.nodePath for rti in repo.rootItems()]
        logger.debug("All root items: {}".format(nodePaths))
        self.walkRepoNodes(nodePaths)


    def walkRepoNodes(self, nodePaths):
        """ Will recursively walk through a list of repo tree nodes and all their descendants

            Is useful for testing.
        """
        # TODO: detail tabs must signal when they fail
        # TODO: test walk dialog with progress bar
        # TODO: select original node at the end of the tests.

        logger.info("-------------- Running Tests ----------------")
        logger.debug("Visiting all nodes below: {}".format(nodePaths))

        self.show()
        self._currentTestName = None
        self._results = []
        self.editor.clear()

        nodesVisited = 0
        logger.debug("Starting test walk")
        self._isOngoing = True
        self._updateButtons()

        # Unselect the current item to force the first node to trigger a new inspector
        invalidIndex = self._mainWindow.repoWidget.repoTreeView.model().index(-1, -1)
        assert not invalidIndex.isValid(), "sanity check"
        self._mainWindow.repoWidget.repoTreeView.setCurrentIndex(invalidIndex)

        try:
            timeAtStart = time.perf_counter()
            check_is_a_sequence(nodePaths) # prevent accidental iteration over strings.

            for nodePath in nodePaths:
                nodeItem, nodeIndex = self._mainWindow.repoWidget.repoTreeView.model().findItemAndIndex(nodePath)

                assert nodeItem is not None, "Test data not found, rootNode: {}".format(nodePath)
                assert nodeIndex

                nodesVisited += self._visitNodes(nodeIndex)

            duration = time.perf_counter() - timeAtStart
            self._logTestSummary(duration, nodesVisited)
            self._displayTestSummary(duration, nodesVisited)
        finally:
            logger.debug("Stopping test walk")
            self._isOngoing = False
            self._currentTestName = None
            self._results = []
            self._updateButtons()
            logger.info("-------------- Test walk done ----------------")


    def _visitNodes(self, index: QtCore.QModelIndex) -> int:
        """ Helper function that visits all the nodes recursively.

            Args:
                allInspectors: if True all inspectors are tried for this node.
                allDetailsTabs: if True all detail tabs (attributes, quicklook, etc.) are tried.

            Returns:
                The number of nodes that where visited.
        """
        assert index.isValid(), "sanity check"

        if not self._isOngoing:
            return 0  # Test walk aborted.

        nodesVisited = 1

        repoWidget = self._mainWindow.repoWidget
        repoModel = repoWidget.repoTreeView.model()

        item = repoModel.getItem(index)
        logger.info("Visiting: {!r} ({} children)".
                    format(item.nodePath, repoModel.rowCount(index)))

        self.curPathLabel.setText(item.nodePath)

        # Select index
        if item.nodeName.startswith('_'):
            logger.warning("Skipping node during testing: {}".format(item.nodePath))
            return 0
        else:
            logger.debug("Not skipping node during testing: {}".format(item.nodePath))

        if self.allDetailTabsCheckBox.isChecked() or self.allInspectorsCheckBox.isChecked():
            self._currentTestName = None
        else:
            self._currentTestName = "{}".format(item.nodePath)
            logger.info("processEvents: {}".format(self._currentTestName))
            processEvents()

        repoWidget.repoTreeView.setCurrentIndex(index)
        repoWidget.repoTreeView.expand(index)

        if self.allDetailTabsCheckBox.isChecked():
            # Try properties, attributes and quicklook tabs
            for idx in range(repoWidget.tabWidget.count()):
                tabName = repoWidget.tabWidget.tabText(idx)
                self._currentTestName = "{:11}: {}".format(tabName, item.nodePath)
                logger.debug("Setting repo detail tab : {}".format(tabName))
                repoWidget.tabWidget.setCurrentIndex(idx)
                logger.info("processEvents: {}".format(self._currentTestName))
                processEvents()

        if self.allInspectorsCheckBox.isChecked():
            for action in self._mainWindow.inspectorActionGroup.actions():
                assert action.text(), "Action text undefined: {!r}".format(action.text())
                self._currentTestName = "{:11}: {}".format(action.text(), item.nodePath)
                action.trigger()
                logger.info("processEvents: {}".format(self._currentTestName))
                processEvents()

        for rowNr in range(repoModel.rowCount(index)):
            childIndex = repoModel.index(rowNr, 0, parentIndex=index)
            nodesVisited += self._visitNodes(childIndex)

        # TODO: see if we can close the node
        return nodesVisited


    def _displayTestSummary(self, duration: float, nodesVisited: int):
        """ Displays a test summary in the dialog
        """
        self.appendText('-' * 80)
        if self._isOngoing:
            self.appendText("Test finished.")
        else:
            self.appendText("Test ABORTED", isError=True)


    def _logTestSummary(self, duration: float, nodesVisited: int):
        """ Logs a summary of the test results.
        """
        logger.info("Visited {} nodes in {:.1f} seconds ({:.1f} nodes/second)."
                    .format(nodesVisited, duration, nodesVisited/duration))

        failedTests = [(success, name) for success, name in self._results if not success]
        logger.info("Number of failed tests during test walk: {}".format(len(failedTests)))
        for testName in failedTests:
            logger.info("    {}".format(testName))

        if not self._isOngoing:
            logger.info("")
            logger.info("NOTE: the test walk was aborted!")

        # if len(self._results) != nodesVisited:
        #     logger.warning("Number of results ({}) != Nodes visited: {}"
        #                    .format(len(self._results), nodesVisited))

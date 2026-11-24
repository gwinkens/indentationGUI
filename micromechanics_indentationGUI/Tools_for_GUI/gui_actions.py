""" Module for tools for GUI """
from pathlib import Path
import numpy as np
from PySide6.QtCore import Qt # pylint: disable=no-name-in-module
from PySide6.QtGui import QColor # pylint: disable=no-name-in-module
from PySide6.QtWidgets import QFileDialog, QTableWidgetItem # pylint: disable=no-name-in-module

def Select_TypedTest(self,tabName=None): #pylint: disable=no-self-use
  "select the tests for calculation in one tab"
  if tabName is None:
    tableWidget = getattr(self.ui, "tableWidget")
    plainTextEdit = getattr(self.ui, "plainTextEdit_SelectTypedTest")
  else:
    tableWidget = getattr(self.ui, f"tableWidget_{tabName}")
    plainTextEdit = getattr(self.ui, f"plainTextEdit_SelectTypedTest_{tabName}")
  Text = plainTextEdit.toPlainText()
  TypedTests = Text.split(',')
  for k in range(tableWidget.rowCount()):
    try:
      tableWidget.item(k,0).setCheckState(Qt.Unchecked)
    except:
      pass
  for k, theTest in enumerate(TypedTests):
    if '-' in theTest:
      startNumber = int(theTest.split('-')[0])-1
      EndNumber = int(theTest.split('-')[1])-1
      for j in np.arange(startNumber, EndNumber+1, 1):
        try:
          tableWidget.item(j,0).setCheckState(Qt.Checked)
        except:
          pass
    else:
      try:
        tableWidget.item(int(theTest)-1,0).setCheckState(Qt.Checked)
      except:
        pass

def click_pushButton_SelectAll(self, tabName=None): #pylint: disable=no-self-use
  """ select/ unselect all tests in {tabName} """
  State = Qt.Checked
  if tabName is None:
    tableWidget = getattr(self.ui, "tableWidget")
  else:
    tableWidget = getattr(self.ui, f"tableWidget_{tabName}")
  if tableWidget.item(0,0).checkState() == Qt.Checked:
    State = Qt.Unchecked
  for k in range(tableWidget.rowCount()):
    try:
      tableWidget.item(k,0).setCheckState(State)
    except:
      pass


def addFile_tab(self,tabName):
  """ + "select" Button to select a file path for tab  """
  file = str(QFileDialog.getOpenFileName(self, "Select File")[0])
  if tabName is None:
    theTableWidget = getattr(self.ui, "tableWidget_path")
  else:
    theTableWidget = getattr(self.ui, f"tableWidget_path_{tabName}")
  theRowCount = theTableWidget.rowCount()
  if file != '':
    if theRowCount>0:
      if len(theTableWidget.item(theRowCount-1,0).text()) > 0:
        theRowCount+=1
    else:
      theRowCount=1
    theTableWidget.setRowCount(theRowCount)
    qtablewidgetitem = QTableWidgetItem(file)
    qtablewidgetitem.setCheckState(Qt.Checked)
    theTableWidget.setVerticalHeaderItem(theRowCount-1, QTableWidgetItem(f"Path{int(theRowCount)}"))
    theTableWidget.setItem(0,theRowCount-1,qtablewidgetitem)
    checkFile(self, qtablewidgetitem)
    refreshTestList(theTableWidget)

def deleteFile_tab(self,tabName):
  """ click "-" Button to delete a file path for tab  """
  if tabName is None:
    theTableWidget = getattr(self.ui, "tableWidget_path")
  else:
    theTableWidget = getattr(self.ui, f"tableWidget_path_{tabName}")
  # get selected rows
  selected_items = theTableWidget.selectedItems()
  if not selected_items:
    return  # nothing selected
  # collect row indices (unique + sorted descending, so deleting doesn’t shift others)
  rows = sorted({item.row() for item in selected_items}, reverse=True)
  for row in rows:
    theTableWidget.removeRow(row)
  for i in range(theTableWidget.rowCount()):
    theTableWidget.setVerticalHeaderItem(i, QTableWidgetItem(f"Path{int(i+1)}"))
  refreshTestList(theTableWidget)

def MoveFileUp_tab(self,tabName):
  """ click "up" Button to move up a file path  """
  if tabName is None:
    theTableWidget = getattr(self.ui, "tableWidget_path")
  else:
    theTableWidget = getattr(self.ui, f"tableWidget_path_{tabName}")
  # rowCount = theTableWidget.rowCount()
  columnCount = theTableWidget.columnCount()
  # get selected rows
  selected_items = theTableWidget.selectedItems()
  if not selected_items:
    return  # nothing selected
  # collect row indices (unique + sorted descending, so deleting doesn’t shift others)
  rows = sorted({item.row() for item in selected_items}, reverse=True)
  if len(rows) == 1:
    row = rows[0]
    for i in range(columnCount):
      thisItemClone = theTableWidget.item(row,i).clone()
      upItem = theTableWidget.item(row-1,i)
      if upItem is not None:
        theTableWidget.setItem(row,i,upItem.clone())
        theTableWidget.setItem(row-1,i,thisItemClone)

def MoveFileDown_tab(self,tabName):
  """ click "down" Button to move down a file path  """
  if tabName is None:
    theTableWidget = getattr(self.ui, "tableWidget_path")
  else:
    theTableWidget = getattr(self.ui, f"tableWidget_path_{tabName}")
  # rowCount = theTableWidget.rowCount()
  columnCount = theTableWidget.columnCount()
  # get selected rows
  selected_items = theTableWidget.selectedItems()
  if not selected_items:
    return  # nothing selected
  # collect row indices (unique + sorted descending, so deleting doesn’t shift others)
  rows = sorted({item.row() for item in selected_items}, reverse=True)
  if len(rows) == 1:
    row = rows[0]
    for i in range(columnCount):
      thisItemClone = theTableWidget.item(row,i).clone()
      downItem = theTableWidget.item(row+1,i)
      if downItem is not None:
        theTableWidget.setItem(row,i,downItem.clone())
        theTableWidget.setItem(row+1,i,thisItemClone)

def changeFile_tab(self, tabName):
  """Click 'Change' Button to replace the selected file path in the table."""
  if tabName is None:
    theTableWidget = getattr(self.ui, "tableWidget_path")
  else:
    theTableWidget = getattr(self.ui, f"tableWidget_path_{tabName}")
  selected_items = theTableWidget.selectedItems()
  if not selected_items:
    return  # nothing selected
  # assume we only care about the first selected row
  row = selected_items[0].row()
  # open file dialog
  file, _ = QFileDialog.getOpenFileName(self, "Select File")
  if not file:
    return  # user canceled
  # set new file path in column 0 (adjust column index if needed)
  qtablewidgetitem = QTableWidgetItem(file)
  qtablewidgetitem.setCheckState(Qt.Checked)
  theTableWidget.setVerticalHeaderItem(row, QTableWidgetItem(f"Path{int(row+1)}"))
  theTableWidget.setItem(row, 0, qtablewidgetitem)
  checkFile(self, qtablewidgetitem)
  refreshTestList(theTableWidget)

def loadIndentation(fileNameList):
  """
  read the files like the calculations do

  Args:
    fileNameList (list): paths of the files; several files are merged as in the calculations

  Returns:
    IndentationXXX: the indentation data (datafile is open)

  Raises:
    Exception: if the files cannot be read
  """
  #imported here: WaitingUpgrade_of_micromechanics imports load_depth, which imports this module
  from ..WaitingUpgrade_of_micromechanics import IndentationXXX #pylint: disable=import-outside-toplevel
  from ..Tools4LoadingData import Convert2inGUI #pylint: disable=import-outside-toplevel
  return IndentationXXX(fileName=Convert2inGUI(list(fileNameList)))

def readTestList(fileNameList):
  """
  read the files like the calculations do and return the names of their tests

  Args:
    fileNameList (list): paths of the files; several files are merged as in the calculations

  Returns:
    list: names of the tests

  Raises:
    Exception: if the files cannot be read
  """
  i = loadIndentation(fileNameList)
  testList = list(getattr(i, 'allTestList', []))
  try:
    i.datafile.close()
  except Exception: #pylint: disable=broad-except
    pass
  return testList

def refreshTestList(theTableWidget):
  """
  list the tests of the checked file of a file list in the test list of the same tab (all tests checked)
  and keep the data as i_{tabName}, so that tests can be plotted before the calculation.
  With several checked files the test list is only cleared, since merging is done by the calculation.

  Args:
    theTableWidget (QTableWidget): the file list, i.e. tableWidget_path_{tabName} of the main window
  """
  from ..Tools4LoadingData import read_file_list #pylint: disable=import-outside-toplevel
  mainWindow = theTableWidget.window()
  tabName = theTableWidget.objectName().removeprefix('tableWidget_path_')
  if tabName == 'tabHE_FrameStiffness' and hasattr(mainWindow.ui, 'tableWidget_path_tabHE'):
    copyNewFiles_tabHE(mainWindow, theTableWidget)
  testTable = getattr(mainWindow.ui, f"tableWidget_{tabName}", None)
  if tabName == theTableWidget.objectName() or tabName == 'tabClassification' or testTable is None:
    return #not a file list of the main window or no test list of this kind
  fileNameList = read_file_list(theTableWidget)
  testList = []
  if len(fileNameList) == 1:
    try:
      i = loadIndentation(fileNameList)
      testList = list(getattr(i, 'allTestList', []))
    except Exception: #pylint: disable=broad-except
      pass
    if testList:
      #prepared as in the calculations
      i.parameters_for_GUI()
      i.surface['surfaceIdx'] = {}
      setattr(mainWindow, f"i_{tabName}", i)
  testTable.clearContents()
  testTable.setRowCount(len(testList))
  for k, theTest in enumerate(testList):
    qtablewidgetitem = QTableWidgetItem(theTest)
    qtablewidgetitem.setCheckState(Qt.Checked)
    testTable.setItem(k, 0, qtablewidgetitem)

def readFileSummary(fileName):
  """
  read a file like the calculations do to check if it can be used

  Args:
    fileName (str): path of the file

  Returns:
    tuple: (success, info, suggestion)
  """
  name = Path(fileName).name
  if Path(fileName).suffix.lower() == '.h5':
    return False, f"{name} is a cache file created by the GUI.", \
      'Select the original data file (e.g. .xls or .xlsx); the .h5 file is created from it automatically.'
  suggestion = 'Check if the file is a supported indentation file (.xls/.xlsx, .zip, .smart500).'
  try:
    testList = readTestList([fileName])
  except Exception as e: #pylint: disable=broad-except
    return False, f"{name} could not be read:\n{e}", suggestion
  if len(testList) == 0:
    return False, f"No tests found in {name}.", suggestion
  return True, f"{name}: {len(testList)} tests ({testList[0]} … {testList[-1]})", ''

def allFiles(tableWidget):
  """
  all files of a file list, checked or not

  Args:
    tableWidget (QTableWidget): file list

  Returns:
    list: paths of the files
  """
  return [tableWidget.item(k, 0).text() for k in range(tableWidget.rowCount())
          if tableWidget.item(k, 0) is not None and tableWidget.item(k, 0).text()]

def copyNewFiles_tabHE(mainWindow, theTableWidget):
  """
  files added to the frame stiffness calibration of tabHE are also added to the hardness and modulus calculation;
  a changed file is replaced there as well, deleted files are kept.
  mainWindow.files_tabHE_FrameStiffness holds the files of the last call (set at start and when a session is loaded)

  Args:
    mainWindow (class): MainWindow
    theTableWidget (QTableWidget): tableWidget_path_tabHE_FrameStiffness
  """
  newFiles = allFiles(theTableWidget)
  oldFiles = getattr(mainWindow, 'files_tabHE_FrameStiffness', newFiles)
  mainWindow.files_tabHE_FrameStiffness = newFiles
  added = [file for file in newFiles if file not in oldFiles]
  removed = [file for file in oldFiles if file not in newFiles]
  targetTable = mainWindow.ui.tableWidget_path_tabHE
  targetFiles = allFiles(targetTable)
  added = [file for file in added if file not in targetFiles]
  if not added:
    return
  if len(added) == 1 and len(removed) == 1 and removed[0] in targetFiles: #"change" of a file
    rows = [targetFiles.index(removed[0])]
  else:
    rows = list(range(len(targetFiles), len(targetFiles)+len(added)))
    targetTable.setRowCount(len(targetFiles)+len(added))
  for row, file in zip(rows, added):
    sourceItem = theTableWidget.findItems(file, Qt.MatchExactly)[0]
    targetTable.setItem(row, 0, sourceItem.clone())
    targetTable.setVerticalHeaderItem(row, QTableWidgetItem(f"Path{int(row+1)}"))
  refreshTestList(targetTable)

def checkFile(self, theItem):
  """
  check the file of a file-list item: green background and a summary as tooltip if it can be read,
  red background and the reason otherwise. Shows the result in a dialog if self is the main window.

  Args:
    theItem (QTableWidgetItem): item containing the file path
  """
  isMainWindow = hasattr(self, 'show_error')
  if isMainWindow:
    self.show_wait('GUI is reading the file')
  success, info, suggestion = readFileSummary(theItem.text())
  theItem.setBackground(QColor(0, 170, 0, 60) if success else QColor(220, 0, 0, 60))
  theItem.setToolTip(info)
  if isMainWindow:
    if success:
      self.close_wait(info=f"File read successfully:\n{info}")
    else:
      self.close_wait()
      self.show_error(info, suggestion)

def FilesToDialog_tab(self):
  """ + "select" Button to select a file path for tab  """
  IsPath=False
  try:
    Widget = getattr(self.ui, "tableWidget_path")
  except:
    Widget = getattr(self.ui, "tableWidget")
  else:
    IsPath = True
  theTableWidget_INPUT = self.OriginalTableWidget
  rowCount = theTableWidget_INPUT.rowCount()
  columnCount = theTableWidget_INPUT.columnCount()
  Widget.setRowCount(rowCount)
  Widget.setColumnCount(columnCount)
  for i in range(rowCount):
    for j in range(columnCount):
      theItem = theTableWidget_INPUT.item(i,j)
      try:
        Widget.setItem(i,j,theItem.clone())
      except:
        Widget.setItem(i,j,None)
    if IsPath:
      Widget.setVerticalHeaderItem(i, QTableWidgetItem(f"Path{int(i+1)}"))
  # Copy horizontal header labels (if they exist)
  header_labels = []
  for j in range(columnCount):
    h_item = theTableWidget_INPUT.horizontalHeaderItem(j)
    header_labels.append(h_item.text() if h_item else "")
  Widget.setHorizontalHeaderLabels(header_labels)

def PlainTextToDialog_tab(self):
  """ + "select" Button to select a file path for tab  """
  Widget = getattr(self.ui, "plainTextEdit_SelectTypedTest")
  thePlainTextWidget_INPUT = self.OriginalPlainTextWidget
  if thePlainTextWidget_INPUT is not None:
    Text = thePlainTextWidget_INPUT.toPlainText()
    Widget.setPlainText(Text)

def PlainTextToMainWindow_tab(self):
  """ + "select" Button to select a file path for tab  """
  Widget = self.OriginalPlainTextWidget
  thePlainTextWidget_INPUT = getattr(self.ui, "plainTextEdit_SelectTypedTest")
  if thePlainTextWidget_INPUT is not None:
    Text = thePlainTextWidget_INPUT.toPlainText()
    Widget.setPlainText(Text)

def FilesToMainWindow_tab(self):
  """ + "select" Button to select a file path for tab  """
  Widget = self.OriginalTableWidget
  IsPath=False
  try:
    theTableWidget_INPUT = getattr(self.ui, "tableWidget_path")
  except:
    theTableWidget_INPUT = getattr(self.ui, "tableWidget")
  else:
    IsPath = True
  rowCount = theTableWidget_INPUT.rowCount()
  columnCount = theTableWidget_INPUT.columnCount()
  Widget.setRowCount(rowCount)
  Widget.setColumnCount(columnCount)
  for i in range(rowCount):
    for j in range(columnCount):
      theItem = theTableWidget_INPUT.item(i,j)
      if theItem is not None:
        Widget.setItem(i,j,theItem.clone())
    if IsPath:
      Widget.setVerticalHeaderItem(i, QTableWidgetItem(f"Path{int(i+1)}"))
  # Copy horizontal header labels (if they exist)
  header_labels = []
  for j in range(columnCount):
    h_item = theTableWidget_INPUT.horizontalHeaderItem(j)
    header_labels.append(h_item.text() if h_item else "")
  Widget.setHorizontalHeaderLabels(header_labels)
  if IsPath:
    refreshTestList(Widget)

def selectedTestItems(theTableWidget):
  """
  test-name items (column 0) of all rows with at least one selected cell

  Args:
    theTableWidget (QTableWidget): the table listing the tests

  Returns:
    list: one QTableWidgetItem per selected row, sorted by row
  """
  rows = sorted({item.row() for item in theTableWidget.selectedItems()})
  return [theTableWidget.item(row, 0) for row in rows]

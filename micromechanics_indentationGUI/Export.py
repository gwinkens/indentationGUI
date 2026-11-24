#pylint: disable=possibly-used-before-assignment, used-before-assignment

""" Graphical user interface to export results """
import os
from pandas import ExcelWriter, DataFrame
import numpy as np
from PySide6.QtWidgets import QMessageBox # pylint: disable=no-name-in-module
from . import __version__
from .Tools4LoadingData import read_file_list
from .Tools4hdf5 import NEXUS_CREATOR, nexus_file, nexus_group, nexus_field, nexus_name

def confirm_overwrite(parent, paths):
  """
  Ask the user before existing files are overwritten

  Args:
    parent (QWidget): parent of the message box
    paths (list): full paths of the files that will be written

  Returns:
    bool: True if no file exists or the user agrees to overwrite
  """
  existing = [str(path) for path in paths if os.path.exists(path)]
  if not existing:
    return True
  answer = QMessageBox.warning(parent, 'Overwrite files?',
                               'These files already exist and will be overwritten:\n\n' + '\n'.join(existing),
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                               QMessageBox.StandardButton.No)
  return answer == QMessageBox.StandardButton.Yes

#graphs of tabHE (incl. the frame stiffness calibration) exported as png-files: canvas of the MainWindow -> suffix of the file name
PLOTS_tabHE = {
  'static_canvas_tabHE_FrameStiffness': 'frame_calibration_frame_compliance',
  'static_canvas_load_depth_tab_inclusive_frame_stiffness_tabHE_FrameStiffness': 'frame_calibration_load_depth',
  'static_canvas_load_depth_tab_exclusive_frame_stiffness_tabHE_FrameStiffness': 'frame_calibration_load_depth_frame_corrected',
  'static_canvas_load_depth_tab_inclusive_frame_stiffness_tabHE': 'load_depth',
  'static_canvas_load_depth_tab_exclusive_frame_stiffness_tabHE': 'load_depth_frame_corrected',
  'static_canvas_H_hc_tabHE': 'H_hc',
  'static_canvas_H_h_tabHE': 'H_h',
  'static_canvas_H_Index_tabHE': 'H_test',
  'static_canvas_E_hc_tabHE': 'E_hc',
  'static_canvas_E_h_tabHE': 'E_h',
  'static_canvas_E_Index_tabHE': 'E_test',
  'static_canvas_HE_tabHE': 'H_E',
  'static_canvas_HE2_hc_tabHE': 'H_E2_hc',
  }

def plot_files(output_path, index_export_tab, win):
  """
  graphs exported together with the results: all graphs of tabHE that show data

  Args:
    output_path (str): full path of the exported results
    index_export_tab (int): exported tab, see comboBox_ExportTab
    win (class): MainWindow

  Returns:
    dict: full path of the png-file -> canvas
  """
  if index_export_tab != 0:
    return {}
  basePath = os.path.splitext(output_path)[0]
  plots = {}
  for canvasName, suffix in PLOTS_tabHE.items():
    canvas = getattr(win, canvasName, None)
    if canvas is not None and any(ax.has_data() for ax in canvas.figure.axes):
      plots[f"{basePath}_{suffix}.png"] = canvas
  return plots

def save_plots(plots, win):
  """
  save the graphs as png-files

  Args:
    plots (dict): full path of the png-file -> canvas, see plot_files
    win (class): MainWindow
  """
  try:
    for fileName, canvas in plots.items():
      canvas.figure.savefig(fileName, dpi=300)
  except OSError as e:
    win.show_error(str(e), 'Check if the folder exists and is writable.')

def export(self, win):
  """
  Graphical user interface to export calculated hardness and young's modulus

  Args:
    win (class): MainWindow

  Returns:
    bool: False if the user cancelled because the file exists
  """
  Index_ExportTab = self.ui.comboBox_ExportTab.currentIndex()
  Index_ExportFormat = self.ui.comboBox_ExportFormat.currentIndex()
  Index_ExportFileType = self.ui.comboBox_ExportFileType.currentIndex()
  output_path = os.path.join(self.ui.lineEdit_ExportFolder.text(), self.ui.lineEdit_ExportFileName.text())
  plots = plot_files(output_path, Index_ExportTab, win)
  if not confirm_overwrite(self, [output_path, *plots]):
    return False
  writer = None
  if Index_ExportFileType == 0:
    try:
      writer = ExcelWriter(output_path, engine='xlsxwriter') # pylint: disable=abstract-class-instantiated
    except Exception as e: #pylint:disable=broad-except
      suggestion = 'Close the opened Excel file.'
      win.show_error(str(e), suggestion)
      return
  #define the data frame of experimental parameters
  if Index_ExportTab == 0:
    #define the data frame of experimental parameters of tabHE
    df = DataFrame([
                    ['Tested Material'],
                    [win.ui.lineEdit_MaterialName_tabHE.text()],
                    [win.ui.lineEdit_path_tabHE.text()],
                    [win.ui.doubleSpinBox_Poisson_tabHE.value()],
                    ['Tip'],
                    [win.ui.lineEdit_TipName_tabHE.text()],
                    [win.ui.doubleSpinBox_E_Tip_tabHE.value()],
                    [win.ui.doubleSpinBox_Poisson_Tip_tabHE.value()],
                    [' '],
                    [win.ui.lineEdit_TAF1_tabHE.text()],
                    [win.ui.lineEdit_TAF2_tabHE.text()],
                    [win.ui.lineEdit_TAF3_tabHE.text()],
                    [win.ui.lineEdit_TAF4_tabHE.text()],
                    [win.ui.lineEdit_TAF5_tabHE.text()],
                    [' '],
                    [win.ui.lineEdit_FrameCompliance_tabHE.text()],
                    ['Unloading Range to Calculate Stiffness'],
                    [win.ui.doubleSpinBox_Start_Pmax_tabHE.value()],
                    [win.ui.doubleSpinBox_End_Pmax_tabHE.value()],
                    ['Range for calculating mean value'],
                    [win.ui.doubleSpinBox_minhc4mean_tabHE.value()],
                    [win.ui.doubleSpinBox_maxhc4mean_tabHE.value()],

                  ],
                  index=[
                          ' ',
                          'Name of Tested Material',
                          'Path',
                          'Poisson\'s Ratio',
                          ' ',
                          'Tip Name',
                          'Young\'s Modulus of Tip [GPa]',
                          'Poisson\'s Ratio of Tip [GPa]',
                          'Terms of Tip Area Function (TAF)',
                          'C0',
                          'C1',
                          'C2',
                          'C3',
                          'C4',
                          ' ',
                          'Frame Compliance [µm/mN]',
                          ' ',
                          'Start[100\% of Pmax]', #pylint: disable=anomalous-backslash-in-string
                          'End[100\% of Pmax]', #pylint: disable=anomalous-backslash-in-string
                          ' ',
                          'min. hc [µm]', #pylint: disable=anomalous-backslash-in-string
                          'max. hc [µm]', #pylint: disable=anomalous-backslash-in-string
                        ],
                    columns=[' '])
  elif Index_ExportTab == 1:
    #define the data frame of experimental parameters of tabPopIn
    df = DataFrame([
                    ['Tested Material'],
                    [win.ui.lineEdit_MaterialName_tabPopIn.text()],
                    [win.ui.lineEdit_path_tabPopIn.text()],
                    [win.ui.doubleSpinBox_Poisson_tabPopIn.value()],
                    ['Tip'],
                    [win.ui.lineEdit_TipName_tabPopIn.text()],
                    [win.ui.doubleSpinBox_E_Tip_tabPopIn.value()],
                    [win.ui.doubleSpinBox_Poisson_Tip_tabPopIn.value()],
                    [win.ui.doubleSpinBox_TipRadius_tabPopIn.value()],
                    [' '],
                    [win.ui.lineEdit_FrameCompliance_tabPopIn.text()],
                  ],
                  index=[
                          ' ',
                          'Name of Tested Material',
                          'Path',
                          'Poisson\'s Ratio',
                          ' ',
                          'Tip Name',
                          'Young\'s Modulus of Tip [GPa]',
                          'Poisson\'s Ratio of Tip [GPa]',
                          'Tip Radius [µm]',
                          ' ',
                          'Frame Compliance [µm/mN]',
                        ],
                    columns=[' '])
  elif Index_ExportTab == 2:
    #define the data frame of experimental parameters of tabClassification
    df = DataFrame([
                    [win.ui.textEdit_Files_tabClassification.toPlainText()],
                    ['Parameters'],
                    [win.ui.spinBox_NumberClusters_tabClassification.value()],
                    [win.ui.doubleSpinBox_WeightingRatio_tabClassification.value()],
                    [win.ui.comboBox_FlipMapping_tabClassification.currentIndex()],
                  ],
                  index=[
                          'Files',
                          ' ',
                          'Number of Clusters [-]',
                          'Weighting ratio, y/x [-]',
                          'Flip mapping (0=None, 1=Left-Right, 2=Top-Bottom, 3=Both)',
                        ],
                    columns=[' '])
  elif Index_ExportTab == 3:
    #define the data frame of experimental parameters of tabCreep
    file_list = read_file_list(win.ui.tableWidget_path_tabCreep)
    df = DataFrame([
                    [file_list[0] if file_list else ''],
                    [win.ui.doubleSpinBox_Poisson_tabCreep.value()],
                    [win.ui.doubleSpinBox_E_Tip_tabCreep.value()],
                    [win.ui.doubleSpinBox_Poisson_Tip_tabCreep.value()],
                    [win.ui.lineEdit_FrameCompliance_tabCreep.text()],
                    [win.ui.doubleSpinBox_DataSegment4Smooth_tabCreep.value()],
                  ],
                  index=[
                          'Path',
                          'Poisson\'s Ratio',
                          'Young\'s Modulus of Tip [GPa]',
                          'Poisson\'s Ratio of Tip',
                          'Frame Compliance [µm/mN]',
                          'Data Segment for Smoothing [s]',
                        ],
                    columns=[' '])

  if Index_ExportFileType == 1:
    try:
      _export_hdf5(output_path, Index_ExportTab, _nexus_parameters(Index_ExportTab, win), win)
    except OSError as e:
      win.show_error(str(e), 'Close the opened HDF5 file.')
      return
    save_plots(plots, win)
    return

  #write to excel
  df.to_excel(writer,sheet_name='Experimental Parameters')
  #set the width of column
  writer.sheets['Experimental Parameters'].set_column(0, 1, 30)
  writer.sheets['Experimental Parameters'].set_column(0, 2, 60)
  if Index_ExportTab == 2:
    #set the height of column
    writer.sheets['Experimental Parameters'].set_row(1, 30)
  if Index_ExportFormat == 0:
    if Index_ExportTab == 0:
      #define the data frame of each tests for tabHE
      for j, _ in enumerate(win.tabHE_testName_collect):
        sheetName = win.tabHE_testName_collect[j]
        if win.tabHE_X_Position_collect[j] is None:
          win.tabHE_X_Position_collect[j]=0
          win.tabHE_Y_Position_collect[j]=0
        df = DataFrame(
                        [
                          win.tabHE_hc_collect[j],
                          win.tabHE_hmax_collect[j],
                          win.tabHE_Pmax_collect[j],
                          win.tabHE_H_collect[j],
                          win.tabHE_E_collect[j],
                          win.tabHE_Er_collect[j],
                          win.tabHE_X_Position_collect[j] * np.ones(len(win.tabHE_E_collect[j])),
                          win.tabHE_Y_Position_collect[j] * np.ones(len(win.tabHE_E_collect[j])),
                        ],
                        index =[
                                  'hc[µm]',
                                  'hmax[µm]',
                                  'Pmax[mN]',
                                  'H[GPa]',
                                  'E[GPa]',
                                  'Er[GPa]',
                                  'X Position [µm]',
                                  'Y Position [µm]',
                                ],
                        )
        df = df.T
        #write to excel
        df.to_excel(writer,sheet_name=sheetName, index=False)
        for k in range(10):
          #set the width of column
          writer.sheets[sheetName].set_column(0, k, 20)
    if Index_ExportTab == 1:
      #define the data frame of each tests for tabPopIn
      for j, _ in enumerate(win.tabPopIn_testName_collect):
        sheetName = win.tabPopIn_testName_collect[j]
        df = DataFrame(
                        [
                          win.tabPopIn_fPopIn_collect[j],
                          win.tabPopIn_prefactor_collect[j],
                          win.tabPopIn_E_collect[j],
                          win.tabPopIn_maxShearStress_collect[j],
                        ],
                        index =[
                                  'Pop-in Load [mN]',
                                  'fitted Hertzian prefactor[mN*µm^(-3/2)]',
                                  'calculated E [GPa]',
                                  'calculated max. shear stress [GPa]',
                                ],
                        )
        df = df.T
        #write to excel
        df.to_excel(writer,sheet_name=sheetName, index=False)
        for k in range(10):
          #set the width of column
          writer.sheets[sheetName].set_column(0, k, 20)
    if Index_ExportTab == 3:
      #define the data frame of each tests for tabCreep
      for j, _ in enumerate(win.tabCreep_testName_collect):
        sheetName = win.tabCreep_testName_collect[j]
        n = len(win.tabCreep_equivStress_collect[j])
        time_values = _tab_creep_time_values(win, j, n)
        df = DataFrame(
                        [
                          time_values,
                          win.tabCreep_equivStress_collect[j],
                          win.tabCreep_CreepRate_collect[j],
                        ],
                        index =[
                                  'time[s]',
                                  'equiv stress[GPa]',
                                  'creep rate[s-1]',
                                ],
                        )
        df = df.T
        #write to excel
        df.to_excel(writer,sheet_name=sheetName, index=False)
        for k in range(10):
          #set the width of column
          writer.sheets[sheetName].set_column(0, k, 20)
  elif Index_ExportFormat == 1:
    if Index_ExportTab == 0:
      #define the data frame of all tests for tabHE
      All_testName_collect = []
      All_hc_collect = []
      All_hmax_collect = []
      All_Pmax_collect = []
      All_Hmean_collect = []
      All_Hstd_collect = []
      All_Emean_collect = []
      All_Estd_collect = []
      All_Er_mean_collect = []
      All_Er_std_collect = []
      All_X_Position_collect=win.tabHE_X_Position_collect
      All_Y_Position_collect=win.tabHE_Y_Position_collect
      for j, _ in enumerate(win.tabHE_testName_collect):
        All_testName_collect.append(win.tabHE_testName_collect[j])
        All_hc_collect.append(win.tabHE_hc_collect[j][-1])
        All_hmax_collect.append(win.tabHE_hmax_collect[j])
        All_Pmax_collect.append(win.tabHE_Pmax_collect[j][-1])
        All_Hmean_collect.append(win.tabHE_Hmean_collect[j])
        All_Hstd_collect.append(win.tabHE_Hstd_collect[j])
        All_Emean_collect.append(win.tabHE_Emean_collect[j])
        All_Estd_collect.append(win.tabHE_Estd_collect[j])
        All_Er_mean_collect.append(win.tabHE_Er_mean_collect[j])
        All_Er_std_collect.append(win.tabHE_Er_std_collect[j])
      df = DataFrame(
                      [
                        All_testName_collect,
                        All_hc_collect,
                        All_hmax_collect,
                        All_Pmax_collect,
                        All_Hmean_collect,
                        All_Hstd_collect,
                        All_Emean_collect,
                        All_Estd_collect,
                        All_Er_mean_collect,
                        All_Er_std_collect,
                        All_X_Position_collect,
                        All_Y_Position_collect,
                      ],
                      index =[
                              'Test Name',
                              'max. hc [µm]',
                              'max. hmax [µm]',
                              'max. Pmax [mN]',
                              'mean of H [GPa]',
                              'std of H [GPa]',
                              'mean of E [GPa]',
                              'std of E [GPa]',
                              'mean of Er [GPa]',
                              'std of Er [GPa]',
                              'X Position [µm]',
                              'Y Position [µm]',
                              ],
                      )
    elif Index_ExportTab == 1:
      #define the data frame of all tests for tabPopIn
      All_testName_collect = []
      All_fPopIn_collect = []
      All_prefactor_collect = []
      All_E_collect = []
      All_maxShearStress_collect = []
      for j, _ in enumerate(win.tabPopIn_testName_collect):
        try:
          for k, _ in enumerate(win.tabPopIn_fPopIn_collect[j]):
            All_testName_collect.append(win.tabPopIn_testName_collect[j])
            All_fPopIn_collect.append(win.tabPopIn_fPopIn_collect[j][k])
            All_prefactor_collect.append(win.tabPopIn_prefactor_collect[j][k])
            All_E_collect.append(win.tabPopIn_E_collect[j][k])
            All_maxShearStress_collect.append(win.tabPopIn_maxShearStress_collect[j][k])
        except (TypeError, IndexError):
          All_testName_collect.append(win.tabPopIn_testName_collect[j])
          All_fPopIn_collect.append(win.tabPopIn_fPopIn_collect[j])
          All_prefactor_collect.append(win.tabPopIn_prefactor_collect[j])
          All_E_collect.append(win.tabPopIn_E_collect[j])
          All_maxShearStress_collect.append(win.tabPopIn_maxShearStress_collect[j])

      df = DataFrame(
                      [
                        All_testName_collect,
                        All_fPopIn_collect,
                        All_prefactor_collect,
                        All_E_collect,
                        All_maxShearStress_collect,
                      ],
                      index =[
                                'Test Name',
                                'Pop-in Load [mN]',
                                'fitted Hertzian prefactor[mN*µm^(-3/2)]',
                                'calculated E [GPa]',
                                'calculated max. shear stress [GPa]',
                              ],
                      )
    elif Index_ExportTab == 2:
      #define the data frame of all tests for tabClassification
      df = DataFrame(
                      [
                        win.tabClassification_FileNumber_collect,
                        win.tabClassification_TestName_collect,
                        win.tabClassification_ClusterLabels,
                        win.tabClassification_H_collect,
                        win.tabClassification_E_collect,
                        win.tabClassification_Er_collect,
                      ],
                      index =[
                              'File Number',
                              'Test Name',
                              'Cluster Number',
                              'mean of H [GPa]',
                              'mean of E [GPa]',
                              'mean of Er [GPa]',
                              ],
                      )
    elif Index_ExportTab == 3:
      #define the data frame of all tests for tabCreep
      All_testName_collect = []
      All_time_collect = []
      All_equivStress_collect = []
      All_CreepRate_collect = []
      for j, _ in enumerate(win.tabCreep_testName_collect):
        time_values = _tab_creep_time_values(win, j, len(win.tabCreep_equivStress_collect[j]))
        for k, _ in enumerate(win.tabCreep_equivStress_collect[j]):
          All_testName_collect.append(win.tabCreep_testName_collect[j])
          All_time_collect.append(time_values[k])
          All_equivStress_collect.append(win.tabCreep_equivStress_collect[j][k])
          All_CreepRate_collect.append(win.tabCreep_CreepRate_collect[j][k])
      df = DataFrame(
                      [
                        All_testName_collect,
                        All_time_collect,
                        All_equivStress_collect,
                        All_CreepRate_collect,
                      ],
                      index =[
                              'Test Name',
                              'time[s]',
                              'equiv stress[GPa]',
                              'creep rate[s-1]',
                              ],
                      )

    df = df.T
    sheetName = 'Results'
    #write to excel
    df.to_excel(writer,sheet_name=sheetName, index=False)
    for k in range(15):
      #set the width of column
      writer.sheets[sheetName].set_column(0, k, 20)

  #save the writer and create the excel file (.xlsx)
  writer.close()
  save_plots(plots, win)
  return


def _float_or_text(text):
  """Return the content of a line edit as float if possible, else as text."""
  try:
    return float(text)
  except ValueError:
    return text


def _nexus_parameters(index_export_tab, win):
  """
  Collect the experimental parameters of a tab for the NeXus export

  Args:
    index_export_tab (int): exported tab, see comboBox_ExportTab
    win (class): MainWindow

  Returns:
    list: tuples of (name, value, units, long_name)
  """
  ui = win.ui
  if index_export_tab == 0:
    return [
      ('material_name', ui.lineEdit_MaterialName_tabHE.text(), None, 'Name of Tested Material'),
      ('data_file', ui.lineEdit_path_tabHE.text(), None, 'Path'),
      ('poisson_ratio', ui.doubleSpinBox_Poisson_tabHE.value(), None, "Poisson's Ratio"),
      ('tip_name', ui.lineEdit_TipName_tabHE.text(), None, 'Tip Name'),
      ('tip_youngs_modulus', ui.doubleSpinBox_E_Tip_tabHE.value(), 'GPa', "Young's Modulus of Tip"),
      ('tip_poisson_ratio', ui.doubleSpinBox_Poisson_Tip_tabHE.value(), None, "Poisson's Ratio of Tip"),
      ('tip_area_function_C0', _float_or_text(ui.lineEdit_TAF1_tabHE.text()), None, 'Tip Area Function (TAF) term C0'),
      ('tip_area_function_C1', _float_or_text(ui.lineEdit_TAF2_tabHE.text()), None, 'Tip Area Function (TAF) term C1'),
      ('tip_area_function_C2', _float_or_text(ui.lineEdit_TAF3_tabHE.text()), None, 'Tip Area Function (TAF) term C2'),
      ('tip_area_function_C3', _float_or_text(ui.lineEdit_TAF4_tabHE.text()), None, 'Tip Area Function (TAF) term C3'),
      ('tip_area_function_C4', _float_or_text(ui.lineEdit_TAF5_tabHE.text()), None, 'Tip Area Function (TAF) term C4'),
      ('frame_compliance', _float_or_text(ui.lineEdit_FrameCompliance_tabHE.text()), 'um/mN', 'Frame Compliance'),
      ('unloading_range_start', ui.doubleSpinBox_Start_Pmax_tabHE.value(), None,
       'Unloading Range to Calculate Stiffness: Start [fraction of Pmax]'),
      ('unloading_range_end', ui.doubleSpinBox_End_Pmax_tabHE.value(), None,
       'Unloading Range to Calculate Stiffness: End [fraction of Pmax]'),
      ('hc_min_for_mean', ui.doubleSpinBox_minhc4mean_tabHE.value(), 'um', 'Range for calculating mean value: min. hc'),
      ('hc_max_for_mean', ui.doubleSpinBox_maxhc4mean_tabHE.value(), 'um', 'Range for calculating mean value: max. hc'),
    ]
  if index_export_tab == 1:
    return [
      ('material_name', ui.lineEdit_MaterialName_tabPopIn.text(), None, 'Name of Tested Material'),
      ('data_file', ui.lineEdit_path_tabPopIn.text(), None, 'Path'),
      ('poisson_ratio', ui.doubleSpinBox_Poisson_tabPopIn.value(), None, "Poisson's Ratio"),
      ('tip_name', ui.lineEdit_TipName_tabPopIn.text(), None, 'Tip Name'),
      ('tip_youngs_modulus', ui.doubleSpinBox_E_Tip_tabPopIn.value(), 'GPa', "Young's Modulus of Tip"),
      ('tip_poisson_ratio', ui.doubleSpinBox_Poisson_Tip_tabPopIn.value(), None, "Poisson's Ratio of Tip"),
      ('tip_radius', ui.doubleSpinBox_TipRadius_tabPopIn.value(), 'um', 'Tip Radius'),
      ('frame_compliance', _float_or_text(ui.lineEdit_FrameCompliance_tabPopIn.text()), 'um/mN', 'Frame Compliance'),
    ]
  if index_export_tab == 2:
    return [
      ('data_files', ui.textEdit_Files_tabClassification.toPlainText(), None, 'Files'),
      ('number_of_clusters', ui.spinBox_NumberClusters_tabClassification.value(), None, 'Number of Clusters'),
      ('weighting_ratio', ui.doubleSpinBox_WeightingRatio_tabClassification.value(), None, 'Weighting ratio, y/x'),
      ('flip_mapping', ui.comboBox_FlipMapping_tabClassification.currentIndex(), None,
       'Flip mapping (0=None, 1=Left-Right, 2=Top-Bottom, 3=Both)'),
    ]
  file_list = read_file_list(ui.tableWidget_path_tabCreep)
  return [
    ('data_file', file_list[0] if file_list else '', None, 'Path'),
    ('poisson_ratio', ui.doubleSpinBox_Poisson_tabCreep.value(), None, "Poisson's Ratio"),
    ('tip_youngs_modulus', ui.doubleSpinBox_E_Tip_tabCreep.value(), 'GPa', "Young's Modulus of Tip"),
    ('tip_poisson_ratio', ui.doubleSpinBox_Poisson_Tip_tabCreep.value(), None, "Poisson's Ratio of Tip"),
    ('frame_compliance', _float_or_text(ui.lineEdit_FrameCompliance_tabCreep.text()), 'um/mN', 'Frame Compliance'),
    ('data_segment_for_smoothing', ui.doubleSpinBox_DataSegment4Smooth_tabCreep.value(), 's',
     'Data Segment for Smoothing'),
  ]


NEXUS_ANALYSES = {
  0: 'Hardness and Young\'s modulus',
  1: 'Pop-in analysis',
  2: 'K-means clustering',
  3: 'Creep rate',
}


def _nexus_data(parent, name, fields, signal, *, axes=None, auxiliary_signals=None, title=None):
  """
  Write a NXdata group

  Args:
    parent (h5py.Group): parent group
    name (str): name of the group
    fields (list): tuples of (name, values, units, long_name); a field FIELD_errors holds the uncertainty of FIELD
    signal (str): name of the field to plot
    axes (str): name of the field used as x-axis
    auxiliary_signals (list): names of further fields to plot
    title (str): title of the plot
  """
  attrs = {'signal': signal}
  if axes is not None:
    attrs['axes'] = axes
    attrs[f'{axes}_indices'] = 0
  if auxiliary_signals:
    attrs['auxiliary_signals'] = auxiliary_signals
  data = nexus_group(parent, name, 'NXdata', **attrs)
  if title is not None:
    nexus_field(data, 'title', title)
  for field_name, values, units, long_name in fields:
    nexus_field(data, field_name, values, units=units, long_name=long_name)


def _export_hdf5(output_path, index_export_tab, parameters, win):
  """
  Export results to a NeXus file (hdf5)

  Layout: /entry (NXentry) with sample (NXsample), analysis (NXprocess) including the
  parameters (NXparameters), results (NXdata: one row per test) and one NXdata per test

  Args:
    output_path (str): full file path
    index_export_tab (int): exported tab, see comboBox_ExportTab
    parameters (list): tuples of (name, value, units, long_name), see _nexus_parameters
    win (class): MainWindow
  """
  with nexus_file(output_path) as hdf:
    hdf.attrs['default'] = 'entry'
    entry = nexus_group(hdf, 'entry', 'NXentry', default='results')
    material = next((value for name, value, _, _ in parameters if name == 'material_name'), '')
    title = NEXUS_ANALYSES[index_export_tab] + (f' of {material}' if material else '')
    nexus_field(entry, 'title', title)
    nexus_field(entry, 'program_name', NEXUS_CREATOR).attrs['version'] = __version__
    if material:
      sample = nexus_group(entry, 'sample', 'NXsample')
      nexus_field(sample, 'name', material)
    analysis = nexus_group(entry, 'analysis', 'NXprocess')
    nexus_field(analysis, 'program', f'{NEXUS_CREATOR}: {NEXUS_ANALYSES[index_export_tab]}')
    nexus_field(analysis, 'version', __version__)
    nexus_field(analysis, 'date', hdf.attrs['file_time'])
    group_parameters = nexus_group(analysis, 'parameters', 'NXparameters')
    for name, value, units, long_name in parameters:
      nexus_field(group_parameters, name, value, units=units, long_name=long_name)
    used_names = {'title', 'program_name', 'sample', 'analysis', 'results'}

    if index_export_tab == 0:
      _nexus_data(entry, 'results', [
        ('test_name', win.tabHE_testName_collect, None, 'Test Name'),
        ('hc_max', [values[-1] for values in win.tabHE_hc_collect], 'um', 'max. hc'),
        ('hmax_max', [np.atleast_1d(values)[-1] for values in win.tabHE_hmax_collect], 'um', 'max. hmax'),
        ('Pmax_max', [values[-1] for values in win.tabHE_Pmax_collect], 'mN', 'max. Pmax'),
        ('H_mean', win.tabHE_Hmean_collect, 'GPa', 'mean of H'),
        ('H_mean_errors', win.tabHE_Hstd_collect, 'GPa', 'std of H'),
        ('E_mean', win.tabHE_Emean_collect, 'GPa', 'mean of E'),
        ('E_mean_errors', win.tabHE_Estd_collect, 'GPa', 'std of E'),
        ('Er_mean', win.tabHE_Er_mean_collect, 'GPa', 'mean of Er'),
        ('Er_mean_errors', win.tabHE_Er_std_collect, 'GPa', 'std of Er'),
        ('x_position', win.tabHE_X_Position_collect, 'um', 'X Position'),
        ('y_position', win.tabHE_Y_Position_collect, 'um', 'Y Position'),
      ], signal='H_mean', auxiliary_signals=['E_mean', 'Er_mean'], title=title)
      for i, test_name in enumerate(win.tabHE_testName_collect):
        _nexus_data(entry, nexus_name(test_name, used_names), [
          ('hc', win.tabHE_hc_collect[i], 'um', 'hc'),
          ('H', win.tabHE_H_collect[i], 'GPa', 'H'),
          ('E', win.tabHE_E_collect[i], 'GPa', 'E'),
          ('Er', win.tabHE_Er_collect[i], 'GPa', 'Er'),
          ('Pmax', win.tabHE_Pmax_collect[i], 'mN', 'Pmax'),
          ('hmax', win.tabHE_hmax_collect[i], 'um', 'hmax'),
          ('x_position', win.tabHE_X_Position_collect[i], 'um', 'X Position'),
          ('y_position', win.tabHE_Y_Position_collect[i], 'um', 'Y Position'),
        ], signal='H', axes='hc', auxiliary_signals=['E', 'Er'], title=str(test_name))
    elif index_export_tab == 1:
      rows = []
      for j, test_name in enumerate(win.tabPopIn_testName_collect):
        try:
          for k, _ in enumerate(win.tabPopIn_fPopIn_collect[j]):
            rows.append((test_name, win.tabPopIn_fPopIn_collect[j][k], win.tabPopIn_prefactor_collect[j][k],
                         win.tabPopIn_E_collect[j][k], win.tabPopIn_maxShearStress_collect[j][k]))
        except (TypeError, IndexError):
          rows.append((test_name, win.tabPopIn_fPopIn_collect[j], win.tabPopIn_prefactor_collect[j],
                       win.tabPopIn_E_collect[j], win.tabPopIn_maxShearStress_collect[j]))
      columns = list(zip(*rows)) if rows else [[]] * 5
      _nexus_data(entry, 'results', [
        ('test_name', list(columns[0]), None, 'Test Name'),
        ('pop_in_load', list(columns[1]), 'mN', 'Pop-in Load'),
        ('hertzian_prefactor', list(columns[2]), 'mN/um^1.5', 'fitted Hertzian prefactor'),
        ('E', list(columns[3]), 'GPa', 'calculated E'),
        ('max_shear_stress', list(columns[4]), 'GPa', 'calculated max. shear stress'),
      ], signal='pop_in_load', auxiliary_signals=['max_shear_stress', 'E'], title=title)
    elif index_export_tab == 2:
      _nexus_data(entry, 'results', [
        ('file_number', win.tabClassification_FileNumber_collect, None, 'File Number'),
        ('test_name', win.tabClassification_TestName_collect, None, 'Test Name'),
        ('cluster_number', win.tabClassification_ClusterLabels, None, 'Cluster Number'),
        ('H_mean', win.tabClassification_H_collect, 'GPa', 'mean of H'),
        ('E_mean', win.tabClassification_E_collect, 'GPa', 'mean of E'),
        ('Er_mean', win.tabClassification_Er_collect, 'GPa', 'mean of Er'),
      ], signal='H_mean', auxiliary_signals=['E_mean', 'Er_mean'], title=title)
    elif index_export_tab == 3:
      _nexus_data(entry, 'results', [
        ('test_name', win.tabCreep_testName_collect, None, 'Test Name'),
        ('H_mean', win.tabCreep_Hmean_collect, 'GPa', 'mean of H'),
        ('H_mean_errors', win.tabCreep_Hstd_collect, 'GPa', 'std of H'),
        ('E_mean', win.tabCreep_Emean_collect, 'GPa', 'mean of E'),
        ('E_mean_errors', win.tabCreep_Estd_collect, 'GPa', 'std of E'),
        ('x_position', win.tabCreep_X_Position_collect, 'um', 'X Position'),
        ('y_position', win.tabCreep_Y_Position_collect, 'um', 'Y Position'),
      ], signal='H_mean', auxiliary_signals=['E_mean'], title=title)
      for i, test_name in enumerate(win.tabCreep_testName_collect):
        n = len(win.tabCreep_equivStress_collect[i])
        _nexus_data(entry, nexus_name(test_name, used_names), [
          ('time', _tab_creep_time_values(win, i, n), 's', 'time'),
          ('creep_rate', win.tabCreep_CreepRate_collect[i], '1/s', 'creep rate'),
          ('equiv_stress', win.tabCreep_equivStress_collect[i], 'GPa', 'equiv stress'),
        ], signal='creep_rate', axes='time', auxiliary_signals=['equiv_stress'], title=str(test_name))


def _tab_creep_time_values(win, index, length):
  """Return creep time values matching one exported creep-rate test."""
  time_collect = getattr(win, 'tabCreep_time_collect', [])
  if index < len(time_collect):
    try:
      values = np.asarray(time_collect[index], dtype=float)
    except (TypeError, ValueError):
      values = np.asarray(time_collect[index])
    if len(values) == length:
      return values
  return np.arange(length, dtype=float)

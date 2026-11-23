""" Module for tools for hdf5

All hdf5-files written by the GUI follow the NeXus format (https://www.nexusformat.org):
groups carry the attribute NX_class, numeric fields carry the attribute units.
"""
import re
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from . import __version__

NEXUS_CREATOR = 'micromechanics_indentationGUI'
CONVERSION_PROGRAM = 'convertXLSXtoHDF5'

def _normalize_excel_sheet_for_hdf5(data):
  """Convert Excel sheet columns to HDF5-friendly NumPy/object dtypes."""
  if data.empty and len(data.columns) == 0:
    return data
  normalized_columns = []
  for i, col_name in enumerate(data.columns):
    column = data.iloc[:, i]
    if i == 0 and col_name == 'Markers':
      column = column.map(lambda value: '' if pd.isna(value) else str(value)).astype(object)
    else:
      column = pd.Series(
        pd.to_numeric(column, errors='coerce').to_numpy(dtype='float64'),
        index=data.index,
      )
    normalized_columns.append(column)
  normalized_data = pd.DataFrame(
    {i: column.to_numpy() for i, column in enumerate(normalized_columns)},
    index=data.index,
  )
  normalized_data.columns = data.columns
  return normalized_data

def nexus_name(label, used_names=None):
  """
  Convert a label (e.g. sheet or column name) into a NeXus conform name [a-zA-Z0-9_]

  Args:
    label (str): original label
    used_names (set): names already used in the same group; the returned name is added

  Returns:
    str: name, unique within used_names
  """
  name = re.sub(r'[^0-9a-zA-Z_]+', '_', str(label)).strip('_') or 'unnamed'
  if used_names is None:
    return name
  unique_name, counter = name, 2
  while unique_name in used_names:
    unique_name = f'{name}_{counter}'
    counter += 1
  used_names.add(unique_name)
  return unique_name

def nexus_file(fileName):
  """
  Create a new NeXus file; the caller has to close it

  Args:
    fileName (str): full file path

  Returns:
    h5py.File: opened file, root group is NXroot
  """
  hdf = h5py.File(fileName, mode='w', track_order=True)
  hdf.attrs['NX_class'] = 'NXroot'
  hdf.attrs['file_name'] = Path(fileName).name
  hdf.attrs['file_time'] = datetime.now().astimezone().isoformat(timespec='seconds')
  hdf.attrs['creator'] = NEXUS_CREATOR
  hdf.attrs['creator_version'] = __version__
  hdf.attrs['HDF5_Version'] = h5py.version.hdf5_version
  hdf.attrs['h5py_version'] = h5py.version.version
  return hdf

def nexus_group(parent, name, nxClass, **attrs):
  """
  Create a NeXus group

  Args:
    parent (h5py.Group): parent group
    name (str): name of the group
    nxClass (str): NeXus base class, e.g. NXentry
    attrs: further attributes

  Returns:
    h5py.Group: the new group
  """
  group = parent.create_group(name, track_order=True)
  group.attrs['NX_class'] = nxClass
  group.attrs.update(attrs)
  return group

def nexus_field(group, name, values, units=None, long_name=None):
  """
  Write a NeXus field (dataset)

  Args:
    group (h5py.Group): parent group
    name (str): name of the field
    values (any): scalar, string, list or array; None is stored as NaN
    units (str): units of numeric values
    long_name (str): human readable name

  Returns:
    h5py.Dataset: the new field
  """
  if isinstance(values, str):
    dataset = group.create_dataset(name, data=values, dtype=h5py.string_dtype())
  else:
    array = np.asarray(values)
    if array.dtype.kind == 'O' and not any(isinstance(value, str) for value in array.ravel()):
      #numbers mixed with None
      try:
        array = np.array([np.nan if value is None else value for value in array.ravel()],
                         dtype=np.float64).reshape(array.shape)
      except (TypeError, ValueError):
        pass
    if array.dtype.kind in 'OUS':
      #fixed length utf-8 strings: unlike variable length strings they can be compressed
      encoded = [('' if value is None else str(value)).encode('utf-8') for value in array.ravel()]
      length = max([1]+[len(value) for value in encoded])
      array = np.array(encoded, dtype=h5py.string_dtype('utf-8', length)).reshape(array.shape)
      dataset = group.create_dataset(name, data=array,
                                     **({'compression':'gzip', 'compression_opts':9} if array.size > 0 else {}))
    elif array.ndim > 0 and array.size > 0:
      dataset = group.create_dataset(name, data=array, compression='gzip', compression_opts=9, shuffle=True)
    else:
      dataset = group.create_dataset(name, data=array)
  if units is not None:
    dataset.attrs['units'] = units
  if long_name is not None:
    dataset.attrs['long_name'] = long_name
  return dataset

def convertXLSXtoHDF5(XLSX_File,progressbar=None):
  """
  convert xlsx-file to NeXus hdf5-file with the same name and suffix .h5

  Each sheet becomes a NXcollection in /entry (attribute sheet_name: original name),
  each column a field in it (attribute long_name: original column name).

  Args:
    XLSX_File (string): the full file path of the xlsx-file
    progressbar (def) : to describe the percent of progress
  """
  df = pd.ExcelFile(XLSX_File)
  with nexus_file(str(Path(XLSX_File).with_suffix('.h5'))) as hdf:
    hdf.attrs['default'] = 'entry'
    entry = nexus_group(hdf, 'entry', 'NXentry')
    nexus_field(entry, 'title', f'Raw data of {Path(XLSX_File).name}')
    nexus_field(entry, 'program_name', NEXUS_CREATOR).attrs['version'] = __version__
    conversion = nexus_group(entry, 'conversion', 'NXprocess')
    nexus_field(conversion, 'program', CONVERSION_PROGRAM)
    nexus_field(conversion, 'version', __version__)
    nexus_field(conversion, 'date', hdf.attrs['file_time'])
    parameters = nexus_group(conversion, 'parameters', 'NXparameters')
    nexus_field(parameters, 'source_file', str(XLSX_File))
    usedSheetNames = {'title', 'program_name', 'conversion'}
    for idx, sheet_name in enumerate(df.sheet_names):
      data = _normalize_excel_sheet_for_hdf5(df.parse(sheet_name))
      sheet = nexus_group(entry, nexus_name(sheet_name, usedSheetNames), 'NXcollection', sheet_name=sheet_name)
      usedColumnNames = set()
      for i, col_name in enumerate(data.columns):
        nexus_field(sheet, nexus_name(col_name, usedColumnNames), data.iloc[:, i].to_numpy(), long_name=str(col_name))
      if progressbar is not None:
        progressbar(idx/len(df.sheet_names)*100, 'convert')

class ConvertedXLSX:
  """
  Read a xlsx-file converted by convertXLSXtoHDF5

  Offers the methods of pandas.HDFStore that are used for reading: keys, get, close
  """
  def __init__(self, fileName):
    """
    Args:
      fileName (str): full path of the .h5 file

    Raises:
      OSError: if the file cannot be opened
      ValueError: if the file was not written by convertXLSXtoHDF5 (e.g. old pandas format)
    """
    self.hdf = h5py.File(fileName, mode='r')
    try:
      program = self.hdf['entry/conversion/program'].asstr()[()]
    except (KeyError, TypeError):
      program = None
    if self.hdf.attrs.get('creator') != NEXUS_CREATOR or program != CONVERSION_PROGRAM:
      self.hdf.close()
      raise ValueError(f'{fileName} is not a converted xlsx-file')
    self.sheets = {group.attrs['sheet_name']: group for group in self.hdf['entry'].values()
                   if isinstance(group, h5py.Group) and 'sheet_name' in group.attrs}

  def keys(self):
    """
    Returns:
      list: sheet names with leading '/' like pandas.HDFStore
    """
    return [f'/{sheet_name}' for sheet_name in self.sheets]

  def get(self, key):
    """
    Args:
      key (str): sheet name, with or without leading '/'

    Returns:
      DataFrame: content of the sheet
    """
    sheet = self.sheets[key[1:] if key.startswith('/') else key]
    columns = {}
    for field in sheet.values():
      if h5py.check_string_dtype(field.dtype) is not None:
        columns[field.attrs['long_name']] = field.asstr()[()].astype(object)
      else:
        columns[field.attrs['long_name']] = field[()]
    return pd.DataFrame(columns)

  def close(self):
    """close the file"""
    self.hdf.close()

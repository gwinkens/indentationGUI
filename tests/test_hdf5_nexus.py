from pathlib import Path
from types import SimpleNamespace

import h5py
import numpy as np
import pandas as pd

from micromechanics_indentationGUI.Export import _export_hdf5
from micromechanics_indentationGUI.Tools4hdf5 import convertXLSXtoHDF5, ConvertedXLSX


def test_agilent_xlsx_conversion_is_readable(tmp_path):
  source_xlsx = (
    Path("micromechanics_indentationGUI/Examples/Example1/FusedSilica.xlsx")
  )
  working_xlsx = tmp_path / "FusedSilica.xlsx"
  working_xlsx.write_bytes(source_xlsx.read_bytes())

  convertXLSXtoHDF5(str(working_xlsx))

  hdf5_path = working_xlsx.with_suffix(".h5")
  store = ConvertedXLSX(str(hdf5_path))
  try:
    assert "/Results" in store.keys()
    assert store.get("Results").shape == (20, 6)
    assert "/Test 1" in store.keys()
    assert not store.get("Test 1").empty
    excel = pd.read_excel(source_xlsx, sheet_name="Test 1")
    assert list(store.get("/Test 1").columns) == list(excel.columns)
  finally:
    store.close()

  with h5py.File(hdf5_path, "r") as hdf:
    assert hdf.attrs["NX_class"] == "NXroot"
    assert hdf["entry"].attrs["NX_class"] == "NXentry"
    assert hdf["entry/Test_1"].attrs["sheet_name"] == "Test 1"


def test_old_cache_is_rejected(tmp_path):
  hdf5_path = tmp_path / "old.h5"
  with h5py.File(hdf5_path, "w") as hdf:
    hdf.attrs["export_format"] = "pandas_hdfstore"
    hdf.create_dataset("Results/block0_values", data=np.ones((1, 1)))
  try:
    ConvertedXLSX(str(hdf5_path))
  except ValueError:
    return
  raise AssertionError("old cache was accepted")


def test_hdf5_export_writes_nexus_results_and_per_test_data(tmp_path):
  output_path = tmp_path / "exported_results.h5"
  params = [
    ("material_name", "Fused Silica", None, "Name of Tested Material"),
    ("tip_youngs_modulus", 1141.0, "GPa", "Young's Modulus of Tip"),
  ]
  win = SimpleNamespace(
    tabHE_testName_collect=["Test 1"],
    tabHE_hc_collect=[[1.0, 2.0]],
    tabHE_hmax_collect=[3.0],
    tabHE_Pmax_collect=[[4.0, 5.0]],
    tabHE_H_collect=[[6.0, 7.0]],
    tabHE_E_collect=[[8.0, 9.0]],
    tabHE_Er_collect=[[10.0, 11.0]],
    tabHE_Hmean_collect=[6.5],
    tabHE_Hstd_collect=[0.5],
    tabHE_Emean_collect=[8.5],
    tabHE_Estd_collect=[0.5],
    tabHE_Er_mean_collect=[10.5],
    tabHE_Er_std_collect=[0.5],
    tabHE_X_Position_collect=[None],
    tabHE_Y_Position_collect=[None],
  )

  _export_hdf5(str(output_path), 0, params, win)

  with h5py.File(output_path, "r") as hdf:
    assert hdf.attrs["NX_class"] == "NXroot"
    entry = hdf["entry"]
    assert entry.attrs["NX_class"] == "NXentry"
    assert entry["sample/name"].asstr()[()] == "Fused Silica"
    parameters = entry["analysis/parameters"]
    assert parameters.attrs["NX_class"] == "NXparameters"
    assert parameters["tip_youngs_modulus"].attrs["units"] == "GPa"

    results = entry["results"]
    assert results.attrs["NX_class"] == "NXdata"
    assert results.attrs["signal"] == "H_mean"
    assert list(results["test_name"].asstr()[()]) == ["Test 1"]
    assert results["H_mean"][()] == [6.5]
    assert results["H_mean_errors"][()] == [0.5]
    assert np.isnan(results["x_position"][0])

    test = entry["Test_1"]
    assert test.attrs["signal"] == "H"
    assert test.attrs["axes"] == "hc"
    assert test["title"].asstr()[()] == "Test 1"
    assert list(test["hc"][()]) == [1.0, 2.0]
    assert test["hc"].attrs["units"] == "um"

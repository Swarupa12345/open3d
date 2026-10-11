DRDL AEROSPACE GUI — OPEN3D INTEGRATION TEST COPY
================================================

This ZIP is a separate test copy of the project. It does not overwrite your
original C:\Users\user\Downloads\files16_matplotlib folder.

WHAT CHANGED
------------
1. Added open3d_viewer.py:
   - Uses aero_body_vis.py's existing aircraft geometry builder.
   - Creates a native Open3D window with the nose, fuselage, symmetric wings,
     and cruciform tail fins.
   - S key exports STL; O key exports OBJ.
   - Writes exports into open3d_exports beside this script.
   - Watches a parameter JSON file so an open viewer can refresh while the
     optimizer or flight-envelope playback changes geometry.

2. Patched app.py:
   - The existing VISUALIZE buttons in Prediction, Optimizer and Flight
     Envelope now launch/update the native Open3D viewer in a separate process.
   - Open3D runs outside the PySimpleGUI process so the main GUI event loop
     is not blocked by the viewer.
   - Existing predictor.py, optimizer.py, envelope.py, model files and the
     Matplotlib geometry history are otherwise preserved.

IMPORTANT WINDOWS SETUP
-----------------------
Open Command Prompt and run:

  C:\Users\user\Downloads\files16_matplotlib\open3d_test_env\Scripts\python.exe -m pip install matplotlib

Why: open3d_viewer.py reuses the project's aero_body_vis.py geometry generator,
which imports Matplotlib. Open3D itself is already installed in the isolated
environment from the earlier compatibility test.

RUN THIS COPY WITHOUT OVERWRITING YOUR ORIGINAL
-----------------------------------------------
1. Extract this ZIP to:
   C:\Users\user\Downloads\files16_matplotlib_open3d_test

2. Open Command Prompt:

   cd /d C:\Users\user\Downloads\files16_matplotlib_open3d_test

3. Launch with your regular Python 3.8 environment (the one already used for
   the GUI and its ML dependencies):

   python app.py

4. If prompted for login, the credentials in this app.py are:
   username: drdl
   password: drdl

5. Click VISUALIZE in the Prediction tab first. Check that a separate Open3D
   window appears. Rotate with left mouse drag and zoom with the mouse wheel.
   Press S to export STL or O to export OBJ. Files should appear in:
   open3d_exports

6. Then test the Optimizer and Flight Envelope tabs. If their geometry changes
   while the Open3D viewer remains open, the viewer should refresh from the
   updated parameter file.

OPEN3D PYTHON DISCOVERY
-----------------------
app.py searches in this order:
- OPEN3D_PYTHON environment variable, if set
- .\open3d_test_env\Scripts\python.exe
- ..\files16_matplotlib\open3d_test_env\Scripts\python.exe
- current sys.executable (if it can import Open3D)

If the viewer fails, inspect:
  open3d_sessions\pred_geo_canvas_viewer.log
or the corresponding optimizer/envelope log.

TEST STATUS / LIMITATIONS
-------------------------
- Python syntax compilation passed for app.py and open3d_viewer.py.
- The existing aero_body_vis.build_geometry() function was exercised in the
  build environment and returned the expected nose, body, wing and tail grids.
- The Open3D GUI could not be launched in this build environment because this
  environment does not have Open3D installed. You already confirmed Open3D
  0.18.0 works on your Windows machine with a sphere, so please verify the
  aircraft mesh in this separate test copy before copying any changes over
  your original folder.
- This integration adds native viewer launch/export. It does not replace the
  project's Matplotlib 2D plots with Plotly.

UPDATED LIVE-VISUALIZATION BEHAVIOR (2026-10-11)
================================================
- The Prediction, Optimization, and Flight Envelope tabs no longer show an
  embedded geometry preview or preview-metrics dashboard. Each tab keeps a
  button that opens/updates the separate native Open3D viewer.
- During Optimization, the viewer receives the actual best geometry snapshot
  emitted by the existing Differential Evolution generation callback. It
  updates once per completed generation; it does not create synthetic
  intermediate geometry shapes between generations.
- The Open3D window title shows the current label (for example, GEN 1, GEN 2,
  GEN 3) while the corresponding geometry is refreshed. The title also keeps
  the S (STL export) and O (OBJ export) keyboard hints.
- The DE algorithm, objective/fitness calculations, bounds/constraints,
  mutation/crossover/selection, predictor calculations, and envelope sweeps
  were not intentionally changed. Changes are in GUI/viewer communication.
- Flight-envelope sweeps do not use Differential Evolution. Their physical
  geometry remains the same unless the geometry parameters themselves change;
  changes to alpha/Mach/altitude alone do not imply a new body shape.

HOW TO TEST THE UPDATED PROJECT
===============================
1. Keep your original project folder as a backup.
2. Extract this ZIP into a NEW folder, or into your existing integration-test
   folder after backing it up. Allow replacement of app.py, open3d_viewer.py,
   and this README when prompted. Do not delete your .pkl model files.
3. Use the Python environment that already imports Open3D and Matplotlib.
   If needed, set OPEN3D_PYTHON to that environment's full python.exe path.
4. Open Command Prompt in this project folder and run: python app.py
5. In Optimization, click VISUALIZE IN SEPARATE 3D WINDOW first, then run the
   optimizer. Watch the Open3D title change to GEN 1, GEN 2, GEN 3, etc.
   If you start optimization first, opening the viewer later should show the
   latest generation label and geometry.
6. Prediction and Flight Envelope use their own separate Open3D viewer buttons.

This project ZIP was syntax-checked in the packaging environment, but the
Open3D GUI behavior still needs to be tested on your Windows computer.

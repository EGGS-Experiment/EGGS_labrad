:: Opens the EGGS GUI.
::  Intended as a desktop shortcut.

@ECHO OFF

CD %EGGS_LABRAD_ROOT%\EGGS_labrad\clients\EGGS_GUI
CALL conda activate labart
python EGGS_GUI.py

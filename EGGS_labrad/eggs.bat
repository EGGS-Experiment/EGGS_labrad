

@ECHO OFF

TITLE EGGS GUI
CD C:\Users\joshr\OneDrive\Documents\UCLA\Research\EGGS_Code\EGGS_labrad\EGGS_labrad\clients\EGGS_GUI
CALL C:\Users\joshr\anaconda3\Scripts\activate.bat
CALL conda activate labart
python EGGS_GUI.py

EXIT /B
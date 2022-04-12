:: Opens the RealSimpleGrapher Client.

@ECHO OFF

CD %EGGS_LABRAD_ROOT%\..\RealSimpleGrapher
CALL conda activate grapher
python rsg_client.py

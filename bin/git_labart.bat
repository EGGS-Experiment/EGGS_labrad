@ECHO OFF

::Saves labart environment package list as yml file and pushes it to main repository

::Setup
SET "filename=labart_%COMPUTERNAME%.yml"
CALL activate labart
CD "%HOME%\Code\EGGS_labrad\env"

::Create .yml file
CALL conda env export --name labart > %filename%

::Push .yml file to main
CALL git add %filename%
CALL git commit -m "updated labart environment yml file"
CALL git push origin main
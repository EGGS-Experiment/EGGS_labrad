@ECHO OFF

SET "filename=labart_%COMPUTERNAME%.yml"
CALL activate labart
CD "%HOME%\Code\EGGS_labrad\lib\misc"
CALL conda env export --name labart > %filename%
CALL git add %filename%
CALL git commit -m "updated labart environment yml file"
CALL git push origin main
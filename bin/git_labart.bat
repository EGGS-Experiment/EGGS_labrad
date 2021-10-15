@ECHO OFF

conda activate labart
CD %HOME%/Code/EGGS_labrad/lib/misc
::todo: need to set name
SET name = labart and %hostname%
::todo: make sure this is done correctly
conda env create --file %name%.yml

git add %name%.yml
git commit -m "updated conda env file"
git push origin main
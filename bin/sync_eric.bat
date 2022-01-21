@echo off

REM This is an example script how to run rsync.  Make sure you ran the
REM "install.bat" script once before you attempt to run this script!
REM
REM ===================================================================
REM README: HOW TO USE!
REM ===================================================================
REM
REM 1) Copy this example script to your computer (e.g. to the Desktop).
REM
REM 2) Modify the following things in the rsync command found towards
REM    the end of this file (starting with ".\bash ..."):
REM
REM    a) the user name part (change 'example-user' to your user name)
REM    b) the source, i.e. your local file or directory ("/c/Foo/" in
REM       the example corresponding to "C:\Foo\" in Windows notation);
REM       if the source is a directory, terminate it with a slash '/'!
REM    c) the destination, i.e. the file or directory where stuff will
REM       be put on the file server ("/bar/" in the example); if the
REM       destination is a directory, terminate it with a slash '/'!
REM
REM 3) You may add multiple rsync commands to synchronize different
REM    files/directories.  Copy and paste the rsync command you modified
REM    under 2) and adapt source and destination accordingly.
REM
REM 4) This script MUST BE RUN MANUALLY each time you want to synchronize
REM    your local data with the file server!  It does NOT automatically
REM    do this for you!  (This is intentional to prevent the computer
REM    from stalling or not reacting as expected during data taking.)
REM
REM 5) The synchronized contents can be seen (read-only) here:
REM    \\eric.physics.ucla.edu\example-user
REM
REM 6) Most importantly: CHECK THAT THE SYNCRONIZATION WAS SUCCESSFUL!
REM    (Check (manually) that all the files can be found on the server.)

setlocal enableextensions
set TERM=
cd /d "Q:\cygwin\bin"
echo Synchronizing ... (Please be patient.)

REM ===================================================================
REM RSYNC COMMANDS GO BELOW (NO MODIFICATIONS ABOVE THIS LINE!)
REM ===================================================================

REM .\bash /home/example-user/bin/rsync.sh -rtluh --stats "/c/Foo/" "/bar/"
.\bash /home/eggs-1/bin/rsync.sh -rtluh --stats "c/Users/EGGS1/Documents" "/documents/"

REM keep shell open after synchronization
pause

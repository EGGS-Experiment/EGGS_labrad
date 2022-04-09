:: GF (git fast)
:: Commits & pushes changes to git

@ECHO OFF

REM: Parse input for flags
SET /A local_flag=0
FOR %%x IN (%*) DO (
    IF "%%x"=="-l" (SET /A local_flag=1)
)

REM: Check if we already have files staged for commit
SET staged_flag=0
FOR /F "tokens=*" %%F IN ('git diff --name-only --cached') DO (
    SET /A staged_flag=1
)

REM: Add files for commit
REM:     If local flag (-l) is passed, add all files in local directory
If %local_flag% == 1 (
    CALL git add *
)
REM:     If we have no staged files, then add all files to git
REM: todo: only if local flag is 0
IF %staged_flag% == 0 (
    CALL git add -A
)


REM: Create git messages
REM: todo: ensure bounded by quotation marks
SET "msg="
SET argCount=0
for %%x in (%*) do (
    ECHO Commit message: %%x
    SET /A argCount+=1
    CALL SET "msg=%%msg%% --m %%x"
)

REM: Don't commit if we have no commit messages
IF %argCount% == 0 (
	ECHO Error: can't commit without messages
	goto :EOF
)

:EOF

REM: Clear variables
SET "msg="
SET "argCount="
SET "local_flag="
SET "staged_flag="

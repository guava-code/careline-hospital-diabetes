@echo off
REM Builds hospital.exe (needs MinGW gcc/g++ on PATH). sqlite3.c is compiled once with gcc.
if not exist sqlite3.o (
    gcc -c sqlite3.c -o sqlite3.o
    if errorlevel 1 exit /b 1
)
g++ main.cpp sqlite3.o -o hospital.exe
if errorlevel 1 exit /b 1
echo Built hospital.exe

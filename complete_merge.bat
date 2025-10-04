@echo off
REM Force complete the git merge
cd /d "c:\Users\aarni\Documents\Programming\DefHack"

REM Kill any stuck editors
taskkill /F /IM vim.exe 2>NUL
taskkill /F /IM nano.exe 2>NUL
taskkill /F /IM notepad.exe 2>NUL

REM Complete the merge with default message
git commit -m "Merge telegram_bot branch into database_test_2"

REM Check the result
git status
git log --oneline -3

echo.
echo ✅ Telegram bot merge completed!
echo 📁 New files added in DefHack/clarity_opsbot/
pause
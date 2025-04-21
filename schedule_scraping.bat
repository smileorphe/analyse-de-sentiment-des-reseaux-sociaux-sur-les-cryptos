@echo off
echo Planification du scraping des cryptomonnaies...
py manage.py schedule_scraping --interval 30
pause 
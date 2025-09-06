# NetSuite Automation
This library contains a class that allows programmatic filling of your weekly timesheet in NetSuite
Currently, the library doesn't contain any fancy user input. just a demo script on how to enter the daily entries and save and submit them

## Setup
You need to install playwright for python. figure it out

## Running
See main.py for demo
The first this runs, a chromium browser will open on the login page for qualitest Qt.One portal. You need to complete the first login
by yourself. After you do that, you shouldn't be asked to log in again the next time you use this library, since the context of the browser is saved at some persistent user folder.

The demo shows how to enter basic daily hours. So currently for each week you need to modify the script. My suggestion is to first do a "save" run, view it in the weekly page, and then do a "submit" run, at your own risk. always review the weekly summary before running "submit"

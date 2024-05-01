If you have other Python projects installed which are dependent on specific library versions (i.e. have a `requirements.txt` file included), we recommend that you use a [Python virtual environment](https://www.dataquest.io/blog/a-complete-guide-to-python-virtual-environments/#what-are-python-virtual-environments) for installing the Buggy Editor dependencies to avoid any conficts. Instructions for installation are show below. 

__Instructions for Unix (Mac) users__:

*  Open a new Terminal in VSCode using the menu `Terminal -> New Terminal`. Run `pwd` and confirm you are in the `buggy-editor-main` folder, if not, change directory into it.

* Run `python3 -m venv buggy-env` and select "Yes" when the popup says "We noted a new environment has been created. Do you want to select it for the workspace folder?". You now have a virtual environment called `buggy-env`.

* Run `source buggy-env/bin/activate` - this will activate the new virtual environment.

* To confirm you are using the virtual environment, run `which python`. This should return a directory ending in `buggy-editor-main/buggy-env/bin/python`.

__Instructions for Windows users__:

*  Open a new Powershell Terminal in VSCode using the menu `Terminal -> New Terminal`. Run `pwd` and confirm you are in the `buggy-editor-main` folder, if not, change directory into it.

* Run `python -m venv buggy-env` and if it appears, select "Yes" when the popup says "We noted a new environment has been created. Do you want to select it for the workspace folder?". You now have a virtual environment called `buggy-env`.

* Run `buggy-env\Scripts\activate` - this will activate the new virtual environment.

* To confirm you are using the virtual environment, run `where python`. This should return a directory ending in `buggy-editor-main/buggy-env/bin/python`.
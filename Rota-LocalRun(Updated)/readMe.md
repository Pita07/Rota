# Program Installation and Usage

- Python Installation:
    Install Python at: `https://www.python.org/downloads/` *INSTALL THE STANDALONE INSTALLER, NOT THE INSTALL MANAGER*

- Libraries Installation:
    In Windows PowerShell run the following commands:
        - python -m pip install numpy
        - python -m pip install pandas
        - python -m pip install pathlib
        - python -m pip install openpyxl

- Script Setup:
    Store the script folder in a safe place.
    Create a shortcut for each file in the `Files` folder (both Excel files and `Women.txt`) and store them in an accessible location.
    Create a shortcut for the `TableGenerator.bat` file.
    *THE ORIGINAL FILES MUST BE KEPT IN THEIR ORIGINAL DIRECTORIES*

- File Editing:
    To edit the files, access them through the shortcuts.
    The Excel files must contain only `IN`/`OFF` or `YES`/`NO` in each cell; empty cells are counted as `OFF`/`NO`.
    The `Women` text file must have one name per line (no extra spaces); names should match those in the Excel files.

- Running the Script:
    Edit the files as needed, then double-click the shortcut for the `TableGenerator.bat` file.

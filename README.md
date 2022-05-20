# CereStimDBS

GUI Application for Blackrock CereStim96 with controls that are convenient for DBS surgery.

The Python application located in the `cerestim_dbs` folder is the preferred application. It requires a Python interface to the CereStim API we made called [cerestimwrapper]([https://github.com/SachsLab/CereStimWrapper](https://github.com/CerebusOSS/CereStimWrapper)).

The Matlab AppDesigner-based application also works. Please see the `matlab` directory for that code.

The C++ Qt-based application was started then abandoned because the CereStim SDK does not work in Debug mode!

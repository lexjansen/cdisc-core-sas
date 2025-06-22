%* All programs including this configuration program must define the project_folder macro variable;

options sasautos =
  (%qsysfunc(compress(%qsysfunc(getoption(SASAUTOS)),%str(%()%str(%))))
  "&project_folder/macros");

%if %sysfunc(libref(macros)) %then %do;
  libname macros "&project_folder/macros";
%end;
%if %sysfunc(libref(metadata)) %then %do;
  libname metadata "&project_folder/metadata";
%end;
/*
This code assumes that your SAS environment is able to run Python objects.

Python objects require environment variables to be set before you can use Python objects in your SAS environment.
If the environment variables have not been set, or if they have been set incorrectly,
SAS returns an error when you publish your Python code. Environment variable related errors can look like these examples:

ERROR: MAS_PYPATH environment variable is undefined.
ERROR: The executable C:\file-path\python.exe cannot be located
or is not a valid executable.

Also, this program assumes that your Python environment has packages as defined in cdisc-rules-engine/requirements.txt:

More information:
Using PROC FCMP Python Objects:
https://documentation.sas.com/doc/en/pgmsascdc/9.4_3.5/lecompobjref/p18qp136f91aaqn1h54v3b6pkant.htm

Configuring SAS to Run the Python Language:
https://go.documentation.sas.com/doc/en/bicdc/9.4/biasag/n1mquxnfmfu83en1if8icqmx8cdf.htm
 */

 %* MAS_PYPATH and MAS_M2PATH needed to be able to run Python ;
%* Update to your own locations                              ;
options set = MAS_PYPATH = "&project_folder/.venv312/Scripts/python.exe";
options set = MAS_M2PATH = "%sysget(SASROOT)/tkmas/sasmisc/mas2py.py";

options cmplib = macros.core_funcs;

data _null_;
  core_version = core_version();
  call symputx('core_version', core_version);
run;
  
%let core_path = %sysfunc(sysget(CORE_PATH));
%put;
%put NOTE: %str(CORE_VERSION: &core_version);
%put NOTE: %str(CORE_PATH: &core_path);
%put;

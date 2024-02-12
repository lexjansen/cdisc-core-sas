options sasautos = (%qsysfunc(compress(%qsysfunc(getoption(SASAUTOS)),%str(%()%str(%)))) "&project_folder/macros");
libname macros "&project_folder/macros";
libname data "&project_folder/data";

%* This is needed to be able to run Python;
%* Update to your own locations           ;
options set=MAS_PYPATH="&project_folder/.venv/Scripts/python.exe";
options set=MAS_M2PATH="%sysget(SASROOT)/tkmas/sasmisc/mas2py.py";

options cmplib=macros.core_funcs;

data _null_;
  core_version = core_version();
  call symputx('core_version', core_version);
run;

%let core_path = %sysfunc(sysget(CORE_PATH));
%put NOTE: %str(CORE_PATH: &core_path);
%put NOTE: %str(CORE_VERSION: &core_version);
%put;

%* This code assumes that your SAS environment is able to run Python objects. ;
%* Check the programs/config.sas file for the Python configuration.           ;

%* update this macro variable to your own location;
%let project_folder = /_github/lexjansen/cdisc-core-sas;

%include "&project_folder/programs/config.sas";

filename rulesets "&project_folder/json/core_rule_sets.json";

%core_list_rule_sets(
  output =  %sysfunc(pathname(rulesets)),
  cache_path = &project_folder/resources/cache
  );

data _null_;
   rc = jsonpp('rulesets','log');
run;

libname jsonfile json fileref=rulesets;

data metadata.core_rulesets(keep=standard version);
  length standard $32 version $16;
  set jsonfile.alldata;
  standard = strip(scan(value, 1, ','));
  version = strip(scan(value, 2, ','));
run;

proc sort data = metadata.core_rulesets;
  by standard version;
run;

libname metadata clear;
filename rulesets clear;
libname jsonfile clear;

%* This code assumes that your SAS environment is able to run Python objects. ;
%* Check the programs/config.sas file for the Python configuration.           ;

%* update this macro variable to your own location;
%let project_folder = /_github/lexjansen/cdisc-core-sas;

%include "&project_folder/programs/config.sas";

filename ct "&project_folder/json/core_ct.json";

%core_list_ct(
  subsets =,
  output =  %sysfunc(pathname(ct)),
  cache_path = &project_folder/resources/cache
  );

data _null_;
   rc = jsonpp('ct','log');
run;

libname jsonfile json fileref=ct;

data metadata.core_ct(keep=value rename=(value=ct_package));
  set jsonfile.alldata;
run;

filename ct clear;
libname jsonfile clear;

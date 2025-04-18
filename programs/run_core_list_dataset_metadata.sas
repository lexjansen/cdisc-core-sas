%* This code assumes that your SAS environment is able to run Python objects. ;
%* Check the programs/config.sas file for the Python configuration.           ;

%* update this macro variable to your own location;
%let project_folder = /_github/lexjansen/cdisc-core-sas;

%include "&project_folder/programs/config.sas";

filename meta "&project_folder/json/core_dataset_metadata.json";

%core_list_dataset_metadata(
  dataset_path = %str
    (&project_folder/testdata/sdtm/dm.xpt, 
     &project_folder/testdata/sdtm/ae.xpt, 
     &project_folder/testdata/sdtm/ex.xpt, 
     &project_folder/testdata/sdtm/lb.xpt),
    output =  %sysfunc(pathname(meta))
  );

data _null_;
   rc = jsonpp('meta','log');
run;

libname jsonfile json fileref=meta ordinalcount=none;

data metadata.core_dataset_metadata;
  set jsonfile.root;
run;

filename meta clear;
libname jsonfile clear;

ods listing close;
ods html5 file = "&project_folder/reports/core_dataset_metadata.html";
ods excel file = "&project_folder/reports/core_dataset_metadata.xlsx" 
  options(sheet_name = "Datasets Metadata %sysfunc(date(), e8601da.)" flow = "tables" autofilter = 'all');

  proc print data = metadata.core_dataset_metadata;
    title "Datasets Metadata %sysfunc(date(), e8601da.)";
  run;

ods excel close;
ods html5 close;
ods listing;

libname metadata clear;

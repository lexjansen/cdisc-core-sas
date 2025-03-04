%* This code assumes that your SAS environment is able to run Python objects. ;
%* Check the programs/config.sas file for the Python configuration.           ;

%* update this macro variable to your own location;
%let project_folder = /_github/lexjansen/cdisc-core-sas;

%include "&project_folder/programs/config.sas";


filename rules "&project_folder/json/core_rules_sdtmig-3-2-custom.json";

%core_list_rules(
  output =  %sysfunc(pathname(rules)),
  standard = %str(sdtmig),
  version = %str(3-2),
  cache_path = &project_folder/resources/cache,
  local_rules = 1,
  local_rules_id = CUSTOM123
);

proc sql;
  create table metadata.core_rules
    (
     core_standard char(32),
     core_standard_version char(32),
     core_id char(32),
     custom_id char(32),
     author char(64),
     sensitivity char(32),
     executability char(64),
     description char(1024),
     rule_type char(64),
     message char(1024),
     standards char(256),
     classes_include char(256),
     classes_exclude char(256),
     domains_include char(256),
     domains_exclude char(256),
     datasets char(256)
    );
quit;

ods listing close;
ods html5 file = "&project_folder/reports/core_rules.html";
ods excel file = "&project_folder/reports/core_rules.xlsx";

data _null_;
  set metadata.core_rulesets;
  length code $ 1024;
  if upcase(standard) = "DDF" then
  %* For DDF only get JSON ;
    code = cats('%nrstr(%get_core_rules(core_standard=', lowcase(standard), ', core_standard_version=', version, ', dsout=));');
  else
    code = cats('%nrstr(%get_core_rules(core_standard=', lowcase(standard), ', core_standard_version=', version, '));');
  put code=;
  call execute(code);
run;

ods excel close;
ods html5 close;
ods listing;


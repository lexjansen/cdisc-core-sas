%* update this location to your own location;
%let project_folder=/_github/lexjansen/cdisc-core-sas;
%include "&project_folder/programs/config.sas";

/*
This program assumes that your SAS environment is able to run Python objects.
Check the programs/config.sas file for the Python configuration.

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


filename rules "&project_folder/reports/core_rules.json";

%core_list_rules(
  output =  %sysfunc(pathname(rules)),
  standard = sdtmig,
  version = 3-3,
  cache_path = &project_folder/resources/cache
  );


* libname out "&project_folder/programs/out";
libname out "%sysfunc(pathname(work))";
filename mapfile "%sysfunc(pathname(out))/rules.map";

libname jsonfile json map=mapfile automap=create fileref=rules noalldata  /* ordinalcount=none */;
proc copy in=jsonfile out=out;
run;


data work.datasets;
  set out.datasets;
  by ordinal_root notsorted;
  length _datasets $ 256;
  retain _datasets;
  if first.ordinal_root then _datasets = domain_name;
                        else _datasets = catx(";", _datasets, domain_name);
  if last.ordinal_root;
run;

data work.domains_include;
  set out.domains_include;
  length _include $ 256;
  array include_{*} $ 32 include:;
  _include = catx(";", OF include_{*});
run;

data work.domains_exclude;
  set out.domains_exclude;
  length _exclude $ 256;
  array exclude_{*} $ 32 exclude:;
  _exclude = catx(";", OF exclude_{*});
run;

proc sql;
  create table data.core_rules(drop=ordinal_root)
  as select
    root.*
    , standards.name as standard_name
    , standards.version as standard_version
    , domains_include._include as domains_include
    , domains_exclude._exclude as domains_exclude
    , datasets._datasets as datasets
  from
    out.root root
      left join out.standards standards
    on (standards.ordinal_root=root.ordinal_root)
      left join work.domains_include domains_include
    on (domains_include.ordinal_domains=root.ordinal_root)
      left join work.domains_exclude domains_exclude
    on (domains_exclude.ordinal_domains=root.ordinal_root)
      left join work.datasets datasets
    on (datasets.ordinal_root=root.ordinal_root)
  where standards.name = "SDTMIG" and standards.version = "3.3"
  ;
run;

* ods listing close;
ods html5 file="&project_folder/reports/run_core_list_rules.html";
ods excel file="&project_folder/reports/run_core_list_rules.xlsx" options(sheet_name="Rules" flow="tables" autofilter = 'all');

  proc print data=data.core_rules;
  run;

ods excel close;
ods html5 close;
* ods listing;

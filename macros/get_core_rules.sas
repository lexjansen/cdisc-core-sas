%macro get_core_rules(core_standard=, core_standard_version=, dsout=metadata.core_rules, json_folder=&project_folder/json);

  filename rules "&json_folder/core_rules_&core_standard.-&core_standard_version..json";

  %core_list_rules(
    output =  %sysfunc(pathname(rules)),
    standard = &core_standard,
    version = &core_standard_version,
    cache_path = &project_folder/resources/cache
    );

  filename mapfile temp;
  libname jsonfile json map=mapfile automap=create fileref=rules;

  %* When DSOUT is empty do not create data;
  %if %sysevalf(%superq(dsout)=, boolean) %then %goto exit_macro;

  data work.standards;
    set jsonfile.standards(drop=ordinal_standards);
  run;
  proc sort data=work.standards nodupkey;
    by ordinal_root name version;
  run;

  data work.standards;
    set work.standards;
    by ordinal_root notsorted;
    length _standards $ 256;
    retain _standards;
    if first.ordinal_root then _standards = catx(' ', name, version);
                          else _standards = catx(";", _standards, catx(' ', name, version));
    if last.ordinal_root;
  run;

  %if %sysfunc(exist(jsonfile.datasets)) %then %do;
    data work.datasets(keep=_datasets ordinal_root);
      set jsonfile.datasets;
      by ordinal_root notsorted;
      length _datasets $ 256;
      retain _datasets;
      if first.ordinal_root then _datasets = domain_name;
                            else _datasets = catx(";", _datasets, domain_name);
      if last.ordinal_root;
    run;
  %end;
  %else %do;
    data work.datasets;
      length _datasets $ 256 ordinal_root 8;
      call missing(of _all_);
    run;
  %end;  
   
  %if %sysfunc(exist(jsonfile.domains_include)) %then %do;
    data work.domains_include;
      set jsonfile.domains_include;
      length _include $ 256;
      array include_{*} $ 32 include:;
      _include = catx(";", OF include_{*});
    run;
  %end;
  %else %do;
    data work.domains_include;
      length _include $ 256 ordinal_domains 8;
      call missing(of _all_);
    run;
  %end;  

  %if %sysfunc(exist(jsonfile.domains_exclude)) %then %do;
    data work.domains_exclude;
      set jsonfile.domains_exclude;
      length _exclude $ 256;
      array exclude_{*} $ 32 exclude:;
      _exclude = catx(";", OF exclude_{*});
    run;
  %end;
  %else %do;
    data work.domains_exclude;
      length _exclude $ 256 ordinal_domains 8;
      call missing(of _all_);
    run;
  %end;  

  %if %sysfunc(exist(jsonfile.classes_include)) %then %do;
    data work.classes_include;
      set jsonfile.classes_include;
      length _include $ 256;
      array include_{*} $ 32 include:;
      _include = catx(";", OF include_{*});
    run;
  %end;
  %else %do;
    data work.classes_include;
      length _include $ 256 ordinal_classes 8;
      call missing(of _all_);
    run;
  %end;  

  %if %sysfunc(exist(jsonfile.classes_exclude)) %then %do;
    data work.classes_exclude;
      set jsonfile.classes_exclude;
      length _exclude $ 256;
      array exclude_{*} $ 32 exclude:;
      _exclude = catx(";", OF exclude_{*});
    run;
  %end;
  %else %do;
    data work.classes_exclude;
      length _exclude $ 256 ordinal_classes 8;
      call missing(of _all_);
    run;
  %end;  

  proc sql;
    create table work._core_rules(drop=ordinal_root)
    as select
      "&core_standard" as core_standard length = 32,
      "&core_standard_version" as core_standard_version length = 32,
      root.*
      , params.message
      , standards._standards as standards
      , classes_include._include as classes_include
      , classes_exclude._exclude as classes_exclude
      , domains_include._include as domains_include
      , domains_exclude._exclude as domains_exclude
      , datasets._datasets as datasets
    from
      jsonfile.root root
        left join work.standards standards
      on (standards.ordinal_root = root.ordinal_root)
        left join work.domains_include domains_include
      on (domains_include.ordinal_domains = root.ordinal_root)
        left join work.domains_exclude domains_exclude
      on (domains_exclude.ordinal_domains = root.ordinal_root)
        left join work.classes_include classes_include
      on (classes_include.ordinal_classes = root.ordinal_root)
        left join work.classes_exclude classes_exclude
      on (classes_exclude.ordinal_classes = root.ordinal_root)
        left join work.datasets datasets
      on (datasets.ordinal_root = root.ordinal_root)
        left join jsonfile.actions actions
      on (actions.ordinal_root = root.ordinal_root)
        left join jsonfile.actions_params params
      on (params.ordinal_actions = actions.ordinal_actions)
    order by core_id, core_standard, core_standard_version  
    ;
  run;

  data &dsout;
    set &dsout work._core_rules;
  run;  
  
  ods excel options(sheet_name = "&core_standard &core_standard_version" flow = "tables" autofilter = 'all');
  
  proc print data = work._core_rules;
    title "CORE Rules %sysfunc(date(), e8601da.)";
  run;

  proc delete data = 
    work._core_rules work.standards 
    work.domains_include work.domains_exclude
    classes_include classes_exclude  
    work.datasets; 
  run;

  %exit_macro:

  filename rules clear;
  filename mapfile clear;
  libname jsonfile clear;
  
%mend get_core_rules;

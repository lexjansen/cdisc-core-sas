%* This code assumes that your SAS environment is able to run Python objects. ;
%* Check the programs/config.sas file for the Python configuration.           ;

%* update this macro variable to your own location;
%let project_folder=/_github/lexjansen/cdisc-core-sas;

%include "&project_folder/programs/config.sas";

%let report_name = CORE-Report-%sysfunc(translate(%sysfunc(datetime(), e8601dt.), %str(-), %str(:)));

/* Example of selecting rules */
proc sql noprint;
  select trim(left(core_id)) into :core_rules separated by ','
  from data.core_rules
  where (domains_include in ('ALL' 'AE' 'DM')) and (domains_exclude ne 'DM') and (domains_exclude ne 'AE')
         and (core_standard = "sdtmig" and core_standard_version =  "3-3")
  order by core_id;
quit;

%put &=core_rules;

%core_validate_data(
  cache_path = &project_folder/resources/cache,
  pool_size = 10,
  /*
  data= &project_folder/testdata/sdtm,
  */
  dataset_path = %str
    (&project_folder/testdata/sdtm/dm.xpt, &project_folder/testdata/sdtm/ae.xpt),
  standard = sdtmig,
  version = 3-3,
  controlled_terminology_package = %str(sdtmct-2023-12-15),
  output= &project_folder/reports/&report_name._sdtmig_3-3,
  output_format = %str(XLSX, JSON),
  raw_report = 0,
  data_format = XPT,
  define_xml_path = &project_folder/testdata/sdtm/define.xml,
  whodrug = &project_folder/tests/resources/dictionaries/whodrug,
  meddra = &project_folder/tests/resources/dictionaries/meddra,
  rules = "&core_rules"
  );

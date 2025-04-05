%* This code assumes that your SAS environment is able to run Python objects. ;
%* Check the programs/config.sas file for the Python configuration.           ;

%* update this macro variable to your own location;
%let project_folder = /_github/lexjansen/cdisc-core-sas;

%include "&project_folder/programs/config.sas";

%let report_name = CORE-Report-%sysfunc(translate(%sysfunc(datetime(), e8601dt.), %str(-), %str(:)));

/* Example of selecting rules */
proc sql noprint;
  select distinct core_id into :core_rules separated by ','
  from metadata.core_rules
  where (domains_include in ('ALL' 'AE' 'DM')) and (domains_exclude ne 'DM') and (domains_exclude ne 'AE')
         and (core_standard = "sdtmig" and core_standard_version =  "3-3")
  order by core_id;
quit;

%put &=core_rules;

options noquotelenmax;
%core_validate_data(
  cache_path = &project_folder/resources/cache,
  pool_size = 10,
  dataset_path = %str
    (&project_folder/testdata/sdtm/dm.xpt, 
     &project_folder/testdata/sdtm/ae.xpt),
  standard = sdtmig,
  version = 3-3,
  output= &project_folder/reports/&report_name._sdtmig_3-3_select,
  output_format = %str(XLSX, JSON),
  raw_report = 0,
  define_xml_path = &project_folder/testdata/sdtm/define.xml,
  validate_xml = y,
  whodrug = &project_folder/testdata/dictionaries/whodrug,
  meddra = &project_folder/testdata/dictionaries/meddra,
  loinc = &project_folder/testdata/dictionaries/loinc,
  medrt = &project_folder/testdata/dictionaries/medrt,
  unii = &project_folder/testdata/dictionaries/unii,
  snomed_version = 2024-09-01,
  snomed_edition = SNOMEDCT-US,
  rules = "&core_rules"
  );

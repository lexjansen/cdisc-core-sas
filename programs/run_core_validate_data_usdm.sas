%* This code assumes that your SAS environment is able to run Python objects. ;
%* Check the programs/config.sas file for the Python configuration.           ;

%* update this macro variable to your own location;
%let project_folder = /_github/lexjansen/cdisc-core-sas;

%include "&project_folder/programs/config.sas";

%let report_name = CORE-Report-%sysfunc(translate(%sysfunc(datetime(), e8601dt.), %str(-), %str(:)));

%core_validate_data(
  cache_path = &project_folder/resources/cache,
  pool_size = 10,
  dataset_path= &project_folder/testdata/usdm_data/USDM_Test_Suite_positive.json,
  report_template=&project_folder/resources/templates/usdm-report-template.xlsx,
  standard = usdm,
  version = 3-0,
  output= &project_folder/reports/&report_name._usdm_3-0,
  output_format = %str(XLSX, JSON),
  raw_report = 0,
  rules =
  );

%core_validate_data(
  cache_path = &project_folder/resources/cache,
  pool_size = 10,
  dataset_path= &project_folder/testdata/usdm_data/USDM_Test_Suite_negative.json,
  report_template=&project_folder/resources/templates/usdm-report-template.xlsx,
  standard = usdm,
  version = 4-0,
  output= &project_folder/reports/&report_name._usdm_4-0,
  output_format = %str(XLSX, JSON),
  raw_report = 0,
  rules =
  );

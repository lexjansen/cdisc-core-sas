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


%let report_name = CORE-Report-%sysfunc(translate(%sysfunc(datetime(), e8601dt.), %str(-), %str(:)));

%core_validate_data(
  cache_path = &project_folder/resources/cache,
  pool_size = 10,
  /*
  data= &project_folder/../data/sdtm,
  */
  dataset_path = %str
    (&project_folder/testdata/sdtm/dm.xpt, &project_folder/testdata/sdtm/ae.xpt),
  standard = sdtmig,
  version = 3-3,
  controlled_terminology_package = %str(sdtmct-2023-12-15),
  output= &project_folder/reports/&report_name._sdtmig_3-3,
  output_format = %str(XLSX, JSON),
  raw_report = 0,
  define_xml_path = &project_folder/testdata/sdtm/define.xml,
  whodrug = &project_folder/tests/resources/dictionaries/whodrug,
  meddra = &project_folder/tests/resources/dictionaries/meddra,
  rules =
  );


%* This code assumes that your SAS environment is able to run Python objects. ;
%* Check the programs/config.sas file for the Python configuration.           ;

%* update this macro variable to your own location;
%let project_folder = /_github/lexjansen/cdisc-core-sas;

%include "&project_folder/programs/config.sas";

%*  This macro call assumes that you have an environment variable CDISC_LIBRARY_API_KEY. ;
%*  If not, you can specify the API key in the macro call.                               ;
%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache,
  local_rules =, 
  local_rules_id =, 
  remove_rules =
  );

%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache,
  local_rules =, 
  local_rules_id = , 
  remove_rules = CUSTOM123
  );

%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache,
  local_rules = &project_folder/testdata/rules, 
  local_rules_id = CUSTOM123, 
  remove_rules =
  );

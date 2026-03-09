%* This code assumes that your SAS environment is able to run Python objects. ;
%* Check the programs/config.sas file for the Python configuration.           ;

%* update this macro variable to your own location;
%let project_folder = /_github/lexjansen/cdisc-core-sas;

%include "&project_folder/programs/config.sas";

%*  This macro call assumes that you have an environment variable CDISC_LIBRARY_API_KEY. ;
%*  If not, you can specify the API key in the macro call.                               ;
%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache
  );

/* Add custom rules */
%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache,
  custom_rules_directory = &project_folder/testdata/rules
  );

/* Update custom rule */
%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache,
  update_custom_rule= &project_folder/testdata/rules/CUSTOM-001.yml
  );

/* Add custom standard */
%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache,
  custom_standard = &project_folder/testdata/standards/custom_standard.json
  );

/* Removed custom rule */
%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache,
  remove_custom_rules = 'CUSTOM-001'
  );
  
/* Removed custom rules */
%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache,
  remove_custom_rules = ALL
  );

/* Removed custom standard */
%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache,
  remove_custom_standard = "mycustom/1-0"
  );

/* Add custom rules */
%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache,
  custom_rules_directory = &project_folder/testdata/rules
  );

/* Add custom standard */
%core_update_cache(
  /* apikey= <your API key>, */
  cache_path = &project_folder/resources/cache,
  custom_standard = &project_folder/testdata/standards/custom_standard.json
  );

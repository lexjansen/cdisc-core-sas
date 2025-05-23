/**

@param apikey - optional - CDISC Library api key. Can also be provided in the OS environment variable CDISC_LIBRARY_API_KEY
@param cache_path - required - Relative path to cache files containing pre loaded metadata and rules
@param custom_rules_directory - optional - Relative path to directory containing local rules in yaml or JSON formats to be added to the cache.
@param custom_rule - optional - Relative path to rule file in yaml or JSON formats to be added to the cache.
@param remove_custom_rules -optional - Remove rules from the cache. Can be a single rule ID, a comma-separated list of IDs, or 'ALL' to remove all custom rules.                             
@param update_custom_rule -optional - Relative path to rule file in yaml or JSON formats Rule will be updated in cache with this file.
@param custom_standard -optional - Relative path to JSON file containing custom standard details. Will update the standard if it already exists.                  
@param remove_custom_standard -optional - Removes a custom standard and version from the cache.                                   
**/

%macro core_update_cache(
  apikey =,
  cache_path = %sysfunc(sysget(CORE_PATH))/resources/cache,
  custom_rules_directory =, 
  custom_rule =, 
  remove_custom_rules =, 
  update_custom_rule =, 
  custom_standard =, 
  remove_custom_standard =
  );

  %local
    _Missing;

  %******************************************************************************;
  %* Parameter checks                                                           *;
  %******************************************************************************;

  %* Check for missing parameters ;
  %let _Missing =;
  %if %sysevalf(%superq(cache_path)=, boolean) %then %let _Missing = &_Missing cache_path;

  %if %length(&_Missing) > 0
    %then %do;
      %put ERR%str(OR): [&sysmacroname] Required macro parameter(s) missing: &_Missing..;
      %goto exit_macro;
    %end;

  %* Check if CACHE_PATH is a directory;
  %if %sysevalf(%superq(cache_path)=, boolean) = 0 %then %do;
    %if %direxist(&cache_path) = 0 %then %do;
      %put ERR%str(OR): [&sysmacroname] Path &cache_path is not a directory.;
      %goto exit_macro;
    %end;
  %end;
  %******************************************************************************;
  %* End of parameter checks                                                    *;
  %******************************************************************************;

  data _null_;
    call core_update_cache("&apikey", "&cache_path", 
                           "&custom_rules_directory", "&custom_rule", "&remove_custom_rules", "&update_custom_rule", 
                           "&custom_standard", "&remove_custom_standard");
  run;

  %exit_macro:

%mend core_update_cache;

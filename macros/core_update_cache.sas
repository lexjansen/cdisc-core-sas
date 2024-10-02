/**

@param apikey - optional - CDISC Library api key. Can also be provided in the OS environment variable CDISC_LIBRARY_API_KEY
@param cache_path - required - Relative path to cache files containing pre loaded metadata and rules
@param local_rules - optional - Relative path to folder containing local rules in yaml or JSON format to be added to the cache.  
                                Must be provided in conjunction with -lri.
@param local_rules_id - optional - Custom ID attached to local rules added to the cache used for granular control of local rules 
                                   when removing and validating from the cache.  Must be given when adding local rules to the cache.
@param remove_rules -optional - removes all local rules from the cache                                   
**/

%macro core_update_cache(
  apikey =,
  cache_path = %sysfunc(sysget(CORE_PATH))/resources/cache,
  local_rules =, 
  local_rules_id =, 
  remove_rules =
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
    call core_update_cache("&apikey", "&cache_path", "&local_rules", "&local_rules_id", "&remove_rules");
  run;

  %exit_macro:

%mend core_update_cache;

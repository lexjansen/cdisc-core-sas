/**

@param output - required - JSON output file destination
@param standard - optional - CDISC standard to get rules for
@param version - optional - Standard version to get rules for
@param cache_path - required - Relative path to cache files containing pre loaded metadata and rules
@param custom_rules - optional - flag to list local rules in the cache (0/1)
@param local_rules_id - optional - local rule id to list from the local rules cache

**/

%macro core_list_rules(
  output =, 
  standard =,
  version =, 
  substandard =,
  cache_path = %sysfunc(sysget(CORE_PATH))/resources/cache,
  custom_rules = 0,
  rule_id =,
  ) / minoperator;

  %local
    _Missing;

  %******************************************************************************;
  %* Parameter checks                                                           *;
  %******************************************************************************;

  %* Check for missing parameters ;
  %let _Missing =;
  %if %sysevalf(%superq(output)=, boolean) %then %let _Missing = &_Missing output;
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

  %* Check local_rules;
  %if not(&custom_rules in (0 1)) %then %do;
    %put ERR%str(OR): [&sysmacroname] Macro parameter &=custom_rules must be 0 or 1.;
    %goto exit_macro;
  %end;

  %******************************************************************************;
  %* End of parameter checks                                                    *;
  %******************************************************************************;

  data _null_;
    call core_list_rules("&output", "&standard", "&version", "&substandard", "&cache_path", &custom_rules, "&rule_id");
  run;

  %exit_macro:

%mend core_list_rules;

/**

@param apikey - required - CDISC Library api key. Can be provided in the environment variable CDISC_LIBRARY_API_KEY
@param cache_path - required - Relative path to cache files containing pre loaded metadata and rules

**/

%macro core_update_cache(
  apikey= %sysfunc(sysget(CDISC_LIBRARY_API_KEY)),
  cache_path = %sysfunc(sysget(CORE_PATH))/resources/cache
  );

  %local
    _Missing;

  %******************************************************************************;
  %* Parameter checks                                                           *;
  %******************************************************************************;

  %* Check for missing parameters ;
  %let _Missing =;
  %if %sysevalf(%superq(apikey)=, boolean) %then %let _Missing = &_Missing apikey;
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
    call core_update_cache("&apikey", "&cache_path");
  run;

  %exit_macro:

%mend core_update_cache;

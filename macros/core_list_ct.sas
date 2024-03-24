/**

@param subsets - optional - CT package subset type. Ex: sdtmct. Multiple values allowed
@param output - required - JSON output file destination
@param cache_path - required - Relative path to cache files containing pre loaded metadata and rules

**/

%macro core_list_ct(
  subsets =,
  output =,
  cache_path = %sysfunc(sysget(CORE_PATH))/resources/cache
  );

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
  %******************************************************************************;
  %* End of parameter checks                                                    *;
  %******************************************************************************;

  data _null_;
    call core_list_ct("&subsets", "&output", "&cache_path");
  run;

  %exit_macro:

%mend core_list_ct;

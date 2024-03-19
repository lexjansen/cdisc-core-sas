/**

@param dataset_path - optional - Absolute path to dataset file. Multiple values allowed
@param output - required - JSON output file destination

**/

%macro core_list_dataset_metadata(
  dataset_path =,
  output =
  );

  %local
    i
    _Missing
    _Dataset
    ;

  %******************************************************************************;
  %* Parameter checks                                                           *;
  %******************************************************************************;

  %* Check for missing parameters ;
  %let _Missing =;
  %if %sysevalf(%superq(output)=, boolean) %then %let _Missing = &_Missing output;

  %if %length(&_Missing) > 0
    %then %do;
      %put ERR%str(OR): [&sysmacroname] Required macro parameter(s) missing: &_Missing..;
      %goto exit_macro;
    %end;

  %* Check dataset_path;
  %if %sysevalf(%superq(dataset_path)=, boolean) = 0 %then %do;
    %let i = 1;
    %let _Dataset = %scan(&dataset_path, &i, %str(,;));
    %do %while (%length(&_Dataset));    
      %if not %sysfunc(fileexist(&_Dataset)) %then %do;
        %put ERR%str(OR): [&sysmacroname] Dataset &_Dataset in dataset_path parameter does not exist.;
        %goto exit_macro;
      %end;  
      %let i = %eval(&i + 1);
      %let _Dataset = %scan(&dataset_path, &i, %str(,;));
    %end;
  %end;  

  %******************************************************************************;
  %* End of parameter checks                                                    *;
  %******************************************************************************;

  data _null_;
    call core_list_dataset_metadata("&dataset_path", "&output");
  run;

  %exit_macro:

%mend core_list_dataset_metadata;

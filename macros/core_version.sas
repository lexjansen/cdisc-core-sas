%macro core_version();

  %local
    _version;

    %let _version = %sysfunc(core_version());
    %*;&_version%*;
    
%mend core_version;

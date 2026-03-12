%* This code assumes that your SAS environment is able to run Python objects. ;
%* Check the programs/config.sas file for the Python configuration.           ;

%* update this macro variable to your own location;
%let project_folder = /_github/lexjansen/cdisc-core-sas;

%include "&project_folder/programs/config.sas";

%macro list_metadata(file_type=, sub_folder=);

    filename meta "&project_folder/json/core_dataset_metadata_&file_type..json";

    %core_list_dataset_metadata(
        dataset_path = %str
            (
                &project_folder/testdata/&sub_folder/dm.&file_type,
                &project_folder/testdata/&sub_folder/ae.&file_type,
                &project_folder/testdata/&sub_folder/ex.&file_type,
                &project_folder/testdata/&sub_folder/lb.&file_type
            ),
        output =  %sysfunc(pathname(meta))
    );

    data _null_;
      rc = jsonpp('meta','log');
    run;

    libname jsonfile json fileref=meta ordinalcount=none;

    data metadata.core_dataset_metadata_&file_type;
      set jsonfile.root;
    run;

    filename meta clear;
    libname jsonfile clear;

    ods listing close;
    ods html5 file = "&project_folder/reports/core_dataset_metadata_&file_type..html";
    ods excel file = "&project_folder/reports/core_dataset_metadata_&file_type..xlsx"
      options(sheet_name = "Datasets Metadata %sysfunc(date(), e8601da.)" flow = "tables" autofilter = 'all');

      proc print data = metadata.core_dataset_metadata_&file_type;
        title "Datasets Metadata %sysfunc(date(), e8601da.)";
      run;

    ods excel close;
    ods html5 close;
    ods listing;

%mend list_metadata;

%list_metadata(file_type=xpt, sub_folder=sdtm);
%list_metadata(file_type=json, sub_folder=sdtm_json);

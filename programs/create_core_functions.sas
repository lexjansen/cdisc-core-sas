%* This code assumes that your SAS environment is able to run Python objects. ;
%* Check the programs/config.sas file for the Python configuration.           ;

%* update this macro variable to your own location;
%let project_folder = /_github/lexjansen/cdisc-core-sas;

options sasautos =
  (%qsysfunc(compress(%qsysfunc(getoption(SASAUTOS)),%str(%()%str(%))))
  "&project_folder/macros");
libname macros "&project_folder/macros";

%if %sysfunc(exist(macros.core_funcs)) %then %do;
  proc datasets library = macros nolist;
     delete core_funcs;
  run;
%end;

proc fcmp outlib = macros.core_funcs.python;

  function core_version() $ 32;
    length message $ 128;
    declare object py(python);
    submit into py("&project_folder/python/core_version.py");
    rc = py.publish();
    rc = py.call('core_version');
    message = py.results['message_return_value'];
    return(message);
  endfunc;

  function core_validate_data(
    cache $, pool_size, data $, dataset_path $, log_level $, report_template $,
    standard $, version $, substandard $, output $, output_format $, raw_report,
    controlled_terminology_package $, define_version $, define_xml_path $, validate_xml $,
    whodrug $, meddra $, loinc $, medrt $, unii $, snomed_version $, snomed_edition $, snomed_url $,
    rules $, local_rules $, local_rules_cache, local_rules_id $) $ 128;
    length message $ 128;
    declare object py(python);
    submit into py("&project_folder/python/core_validate_data.py");
    rc = py.publish();
    rc = py.call('core_validate_data',
      cache, pool_size, data, dataset_path, log_level, report_template, standard,
      version, substandard, output, output_format, raw_report, controlled_terminology_package,
      define_version, define_xml_path, validate_xml, whodrug, meddra, loinc, medrt, unii, snomed_version, snomed_edition, snomed_url,
      rules, local_rules, local_rules_cache, local_rules_id);
    message = py.results['message_return_value'];
    return(message);
  endfunc;

  subroutine core_update_cache(apikey $, cache_path $, local_rules $, local_rules_id $, remove_rules $);
    declare object py(python);
    submit into py("&project_folder/python/core_update_cache.py");
    rc = py.publish();
    rc = py.call('core_update_cache', apikey, cache_path, local_rules, local_rules_id, remove_rules);
  endsub;

  subroutine core_list_ct(subsets $, output $, cache_path $);
    declare object py(python);
    submit into py("&project_folder/python/core_list_ct.py");
    rc = py.publish();
    rc = py.call('core_list_ct', subsets, output, cache_path);
  endsub;

  subroutine core_list_dataset_metadata(dataset_path $, output $);
    declare object py(python);
    submit into py("&project_folder/python/core_list_dataset_metadata.py");
    rc = py.publish();
    rc = py.call('core_list_dataset_metadata', dataset_path, output);
  endsub;

  subroutine core_list_rules(output $, standard $, version $, cache_path $, local_rules, local_rules_id $);
    declare object py(python);
    submit into py("&project_folder/python/core_list_rules.py");
    rc = py.publish();
    rc = py.call('core_list_rules', output, standard, version, cache_path, local_rules, local_rules_id);
  endsub;

  subroutine core_list_rule_sets(output $, cache_path $);
    declare object py(python);
    submit into py("&project_folder/python/core_list_rule_sets.py");
    rc = py.publish();
    rc = py.call('core_list_rule_sets', output, cache_path);
  endsub;

run;

libname macros clear;


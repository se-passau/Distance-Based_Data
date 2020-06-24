#!/usr/bin/env python3

import sys
import os
import math
import re

# The sampling strategies that should be analyzed
# TYPES = ["distBased_", "divDistBased_", "solvBased_", "rand", "henard", "grammar-based_"]
from typing import Dict, List, Any, Tuple

TYPES = ["grammarBased_", "rand", "henard"]
CASE_STUDIES = ["7z", "BerkeleyDBC", "Dune", "Hipacc", "JavaGC", "LLVM", "lrzip", "Polly", "VP9", "x264"]
# CASE_STUDIES = ["7z", "BerkeleyDBC", "Dune", "Hipacc", "LLVM", "lrzip", "Polly"]
# CASE_STUDIES = ["lrzip"]

SEPARATOR = "/"
SPL_CONQUEROR_PREFIX = "out_"
ALL_RESULTS_PREFIX = "all_"
ERROR_PREFIX = "error_"
STANDARD_DEVIATION_PREFIX = "sd_"
T_TEST_PREFIX = "ttest_"
KOLMOGOROV_SMIRNOV_PREFIX = "kstest_"
WHOLE_POPULATION = "wp"
VARIANCE_RESULT_PREFIX = "var_"
OTHER_FILE_PREFIXES = ["dist_", "measurement_", "point_"]
OTHER_FILE_SUFFIX = ".txt"
SAMPLED_CONFIGURATIONS_FILE = ["sampledConfigurations"]
SAMPLED_CONFIGURATIONS_FILE_SUFFIX = ".csv"
CSV_SEPARATOR = ";"
TOTAL = "total"
SAMPLED_CONFIGURATIONS_STATS_SUFFIX = "_stat"
PERCENT = "%"


def print_usage() -> None:
    """
    Prints the usage of this script.
    """
    print("Usage: <RunDirectory> <SummaryDirectory>")
    print("RunDirectory\t\t The directory containing the data of all runs.")
    print("SummaryDirectory\t The directory where the average run should be copied to.")


def list_directories(path: str) -> List[str]:
    """
    Returns the subdirectories of the given path.
    :param path: the path to find the subdirectories from.
    :return: the subdirectories as list.
    """
    for root, dirs, files in os.walk(path):
        return dirs


def get_specific_files_from_directory(path: str, prefixes: str, suffix: str, contains: List[str] = None,
                                      excludes: List[str] = None) -> List[str]:
    """
    Returns all files that begin with one of the given prefixes.
    :param path: the path to check the files from
    :param prefixes: the prefixes of the wanted files
    :param suffix: the suffix of the file
    :param contains: the string that must be included
    :param excludes: the string that must not be included
    :return: a list containing the files
    """
    result: List[str] = []
    for root, dirs, files in os.walk(path):
        for file in files:
            found: bool = False
            for prefix in prefixes:
                if prefix in file and file.endswith(suffix):
                    found = True
                    break
            if not found:
                continue

            if contains is not None:
                found = False
                for containedString in contains:
                    if containedString in file:
                        found = True
                        break
                if not found:
                    continue

            if excludes is not None:
                skip: bool = False
                for excludedString in excludes:
                    if excludedString in file:
                        skip = True
                        break
                if skip:
                    continue
            result.append(file)
    return result


def add_to_dictionary(dictionary: Dict[str, Dict[int, Any]], file_name: str, number_run: int, value: Any) -> None:
    """
    Adds the given data to the dictionary.
    :param dictionary: the dictionary to add to
    :param file_name: the file name
    :param number_run: the number of the random seed run
    :param value: the value to add to the dictionary
    """
    if file_name not in dictionary:
        dictionary[file_name] = {}
    dictionary[file_name][number_run] = value


def add_bucket_to_dictionary(dictionary: Dict[str, Dict[int, int]], bucket: str, number_run: int, value: str) -> None:
    """
    Adds the given bucket to the dictionary
    :param dictionary: the dictionary to add to
    :param bucket: the bucket (key)
    :param number_run: the number of run
    :param value: the value to add
    """
    if bucket not in dictionary:
        dictionary[bucket] = {}
    dictionary[bucket][number_run] = int(value)


def analyze_sampling_log_file(path: str) -> int:
    """
    Analyzes the sampling log files of SPL Conqueror.
    :param path: the path to the log file
    :return: the performance in ms
    """
    file = open(path, 'r')
    for line in file:
        if "ConfigurationSampling done " in line:
            return int(line.split()[3])


def analyze_learning_log_file(path: str) -> Tuple[str, float]:
    """
    Analyzes the learning log files of SPL Conqueror.
    :param path: the path to the log file
    :return: the error rate
    """
    error_rate: float = sys.float_info.max
    optimal_parameters: str = ""
    python_learner: bool = False

    file = open(path, 'r')

    for line in file:
        if "Error of optimal parameters" in line:
            split_line: List[str] = line.strip().split(":")
            current_error_rate: float = float(split_line[-1])
            if current_error_rate < error_rate:
                error_rate = current_error_rate
        elif "Optimal parameters " in line:
            optimal_parameters = line.split()[2]
            if not python_learner:
                return optimal_parameters, error_rate
        elif "command: learn-python" in line:
            python_learner = True
        elif python_learner and "Error rate" in line:
            error_rate = float(line.strip().split(" ")[-1]) * 100
            return optimal_parameters, error_rate
    file.close()

    return optimal_parameters, error_rate


def add_to_sum_dict(dictionary: Dict[str, int], file: str, value: int) -> None:
    """
    Adds the given value to the dictionary.
    :param dictionary: the dictionary to add up to
    :param file: the file (key)
    :param value: the value to add
    """
    if file not in dictionary:
        dictionary[file] = 0
    dictionary[file] += value


def copy_file_content(opened_file, target: str, run: int) -> None:
    """
    Copies the file content
    :param opened_file: the file stream
    :param target: the targeted file to read from
    :param run: the run to write
    """
    target_file = open(target, 'r')
    # Skip the header
    next(target_file)
    for line in target_file:
        opened_file.write(str(run) + ";" + line)
    target_file.close()


def get_header_of(file: str) -> str:
    """
    Returns the header of the file
    :param file: the file to read the header from
    :return: the header of the file
    """
    f = open(file, 'r')
    result = next(f)
    return result


def add_values_from_file_to_dict(dictionary: Dict[str, Dict[int, int]], run: int, file_path) -> None:
    """
    Reads in the current content of the file into the dictionary
    :param dictionary: the dictionary to save the content of the file into
    :param run: the random seed run
    :param file_path: the path to the file
    """
    value_file = open(file_path, 'r')

    # Skip the header
    next(value_file)

    # The files have to be written in a csv-like manner, where ';' is taken as element separator and
    # '\n' as row separator
    for line in value_file:
        elements = line.split(';')
        add_bucket_to_dictionary(dictionary, elements[0], run, elements[1])


def convert_dict_to_list(dictionary: Dict[Any, Any]) -> List[Any]:
    """
    Converts the given dictionary to a list.
    :param dictionary: the dictionary to convert
    :return: the dictionary as list
    """
    result = []
    for key in dictionary.keys():
        result.append(dictionary[key])
    return result


def extract_name(file_name: str) -> str:
    return file_name[0:file_name.rfind('_t') + 3]


############
#   MAIN   #
############
def main() -> None:
    """
    This is the main method, which (1) gathers and (2) processes the information of all the runs.
    The accumulated information is stored in another directory.
    """
    if len(sys.argv) != 3:
        print_usage()
        exit(0)

    run_directory: str = sys.argv[1]
    original_directory = sys.argv[2]

    if not run_directory.endswith(SEPARATOR):
        run_directory = run_directory + SEPARATOR

    if not original_directory.endswith(SEPARATOR):
        original_directory = original_directory + SEPARATOR

        # Precompute the prefixes of the files to analyze
    prefixes = []
    for type in TYPES:
        prefixes.append(SPL_CONQUEROR_PREFIX + type[:len(type) - 1])
    suffix = ".log"

    for case_study in CASE_STUDIES:
        print("Analyzing " + case_study + ".")

        run_statistic: Dict[str, Dict[str, Dict[int, float]]] = {}
        performance_statistic: Dict[str, Dict[int, int]] = {}
        optimal_parameters: Dict[str, Dict[int, str]] = {}

        directories: List[str] = list_directories(run_directory + case_study + SEPARATOR)
        average_values: Dict[str, Dict[str, float]] = {}
        for directory in sorted(directories):
            split_name: List[str] = directory.split("_")
            tmp_name: str = ""
            print("Scanning " + split_name[len(split_name) - 1] + ". directory.")

            for i in range(0, len(split_name) - 1):
                if i != 0:
                    tmp_name += "_"
                tmp_name += split_name[i]

            number_run: int = int(split_name[len(split_name) - 1])
            files = get_specific_files_from_directory(run_directory + case_study + SEPARATOR + directory, prefixes,
                                                      suffix)
            for file in sorted(files):
                # We distinguish between two types of log files.
                # Either the log file is related to the sampling process -> save the performance data
                # Or the log file is related to the learning process -> save the error rate
                # The decision whether it is of one type or another is extracted from the name
                file_type = re.split('_t\d+', file.replace('.log', ''))[1]
                file_name = extract_name(file)
                if file_type == '':
                    # In this case, the file contains the sampling results
                    if case_study not in performance_statistic.keys():
                        performance_statistic[case_study] = {}
                    performance: int = analyze_sampling_log_file(
                        run_directory + case_study + SEPARATOR + directory + SEPARATOR + file)
                    performance_statistic[case_study][file_name] = performance
                else:
                    # In this case, the file contains the learning results
                    if file_type not in average_values.keys():
                        average_values[file_type] = {}
                        run_statistic[file_type] = {}
                    (optimal_parameter, error) = analyze_learning_log_file(
                        run_directory + case_study + SEPARATOR + directory + SEPARATOR + file)
                    add_to_sum_dict(average_values[file_type], file_name, error)
                    add_to_dictionary(run_statistic[file_type], file_name, number_run, error)
                    add_to_dictionary(optimal_parameters[file_type], file_name, number_run, optimal_parameters)

        for mode in average_values.keys():
            for directory in average_values[mode].keys():
                average_values[mode][directory] = average_values[mode][directory] / len(run_statistic[mode][directory])

        # Retrieve the most average runs, print the error rates into a file
        avg_runs = {}
        best_runs = {}
        worst_runs = {}
        best_score = {}
        worst_score = {}
        standard_deviation = {}
        for file in run_statistic.keys():
            best_score[file] = 1000
            worst_score[file] = 0

            min_deviation = sys.float_info.max

            standard_deviation[file] = 0

            # Save the error rates in the following file (needed for box-plots)
            mid_file_name = file[len(SPL_CONQUEROR_PREFIX):len(file) - len(suffix)]
            directory = original_directory + case_study
            if not os.path.exists(directory):
                os.makedirs(directory)
            error_rate_file = open(directory + os.path.sep + ALL_RESULTS_PREFIX + ERROR_PREFIX + mid_file_name +
                                   OTHER_FILE_SUFFIX, 'w')
            error_rate_file.write("Run;Error\n")

            for run in run_statistic[file].keys():
                error = run_statistic[file][run]

                # Ignore runs where the error rate is Inf (in C#)
                if error >= 1.79769313486e+308:
                    continue

                if error < best_score[file]:
                    best_score[file] = error
                    best_runs[file] = run
                if error > worst_score[file]:
                    worst_score[file] = error
                    worst_runs[file] = run

                try:
                    standard_deviation[file] += (average_values[file] - error) ** 2
                except Exception as b:
                    print("Error of run " + str(run) + " too high ( in case study " + case_study + ").", b)
                    continue

                error_rate_file.write(str(run) + ";" + str(error) + "\n")

                deviation = abs(average_values[file] - error)
                if deviation < min_deviation:
                    min_deviation = deviation
                    avg_runs[file] = run

            error_rate_file.close()

            # Compute the relative standard deviation
            standard_deviation[file] /= len(run_statistic[file].keys())
            standard_deviation[file] = math.sqrt(standard_deviation[file])
            standard_deviation[file] /= average_values[file]

            standard_deviation_file = open(original_directory + case_study + os.path.sep + ALL_RESULTS_PREFIX + STANDARD_DEVIATION_PREFIX +
                                           mid_file_name + OTHER_FILE_SUFFIX, 'w')
            standard_deviation_file.write(str(standard_deviation[file]) + "\n")
            standard_deviation_file.close()

            # TODO: Write performance data into a csv file

            # TODO: Write optimal parameters in a csv file


if "__main__" == __name__:
    main()

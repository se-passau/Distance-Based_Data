#!/usr/bin/python3

import time
import subprocess
import sys
from typing import List

RUNS_FROM = 1
RUNS_TO = 100
CLUSTERS = [("eku", "i5"), ("kine", ""), ("zeus", "")]
CASE_STUDIES = [# ("BerkeleyDBC", 1000),
                # ("LLVM", 1000),
                ("lrzip", 1),
                # ("x264", 1000),
                #("Dune", 1),
                #("7z", 1),
                #("Hipacc", 1000),
                # ("Polly", 1000),
                # ("JavaGC", 1000),
                # ("VP9", 1000)
                ]

JOB_ID = int(time.time() * 1000)

HOME = "/scratch/kallistos/"
# Prefix is to specify where the scripts to execute are located
PREFIX = HOME + ""

SBATCH = "sbatch"
# --exclusive --exclude='chimaira[13-17]'
SBATCH_OPTIONS = " -n 1 -c 1 --mem=20000M --time='24:00:00' " \
                 "--output=/scratch/kallistos/Grammar-Based/slurm_out.log "
SBATCH_SCRIPT = PREFIX + "runDistributionAware.sh"

JOB_DIR = HOME + "Jobs/"
JOB_FILE_PREFIX = "_jobs_"
JOB_FILE_SUFFIX = ".txt"
JOB_SCRIPT = PREFIX + "runRandomHundredTimes.sh "
# JOB_SCRIPT = PREFIX + "benchmarkSamplingHundredTimes.sh "

ALLOWED_TYPES = ["semi", "solv", "henard", "binom", "geom", "invgeom", "twogeom", "norm", "rand", "all", "local", "global", "grammar-based", "divDistBased"]


def printUsage():
    print("Usage:")
    print("./JobSubmitter <cluster> <solv/semi/random/grammar-based>")
    print("cluster\t The cluster to use")
    print("solv/semi/random/all\t Specifies if distribution-aware (solv) sampling, semi-random sampling, " +
          " random sampling should be executed or all configurations should be used.")


def executeCommand(command: str) -> str:
    output = subprocess.getstatusoutput(command)
    statusCode = output[0]
    message = output[1]

    # Throw an error if the command was not successfully executed
    if (statusCode != 0):
        raise RuntimeError(message)

    return message


def writeToFile(filePath: str, linesToWrite: List[str]):
    with open(filePath, 'w') as file:
        for line in linesToWrite:
            file.write(line + "\n")


def main():
    global SBATCH_OPTIONS
    if (len(sys.argv) != 3):
        printUsage()
        exit(-1)

    type = sys.argv[2]

    if type not in ALLOWED_TYPES:
        raise KeyError("The type " + type + " is not allowed.")

    # Select the cluster
    cluster = sys.argv[1]

    found = False
    for c in CLUSTERS:
        if c[0] == cluster:
            optionsToAdd = "-A ls-apel "
            optionsToAdd += " --constraint=\"" + c[0]
            if (len(c) == 2 and c[1] != ""):
                optionsToAdd += "&" + c[1]
            optionsToAdd += "\""
            SBATCH_OPTIONS = optionsToAdd + SBATCH_OPTIONS
            found = True
            break

    if (not found):
        raise KeyError("Could not find " + cluster + " as cluster.")

    SBATCH_OPTIONS = SBATCH_OPTIONS + " -J " + type;

    # Construct the jobs for the job-file
    jobs = []
    for caseStudy in CASE_STUDIES:
        for run in range(RUNS_FROM, RUNS_TO + 1):
            jobString = "export LD_LIBRARY_PATH=/scratch/kallistos/:$LD_LIBRARY_PATH && "
            jobString += JOB_SCRIPT + caseStudy[0] + " " + str(caseStudy[1]) + " " + type + " " + str(run) + \
                         " " + str(run)
            jobs.append(jobString)

    # Write to the job file
    jobFile = JOB_DIR + "anywhere" + JOB_FILE_PREFIX + str(JOB_ID) + JOB_FILE_SUFFIX
    writeToFile(jobFile, jobs)

    # Submit the array job
    SBATCH_OPTIONS = SBATCH_OPTIONS + " --array=1-" + str(len(jobs)) + " "
    commandToSubmit = SBATCH + " " + SBATCH_OPTIONS + SBATCH_SCRIPT + " " + str(JOB_ID)
    outputString = executeCommand(commandToSubmit)
    print(outputString)


if __name__ == "__main__":
    main()

#!/usr/bin/python3

import time
import subprocess
import sys
from typing import List

RUNS_FROM = 1
RUNS_TO = 100
CLUSTERS = [("eku", "i5"), ("kine", ""), ("zeus", ""), ("anywhere", "")]
CASE_STUDIES = [("BerkeleyDBC", 1000),
                ("LLVM", 1000),
                ("lrzip", 1),
                ("x264", 1000),
                ("Dune", 1),
                ("7z", 1),
                ("Hipacc", 1000),
                ("Polly", 1000),
                ("JavaGC", 1000),
                ("VP9", 1000)
                ]

JOB_ID = int(time.time() * 1000)

HOME = "/scratch/kallistos/"
# Prefix is to specify where the scripts to execute are located
PREFIX = HOME + "Distance-Based_Data/Scripts/cluster/"

SBATCH = "sbatch"
# --exclusive --exclude='chimaira[13-17]'
SBATCH_OPTIONS = " -n 1 -c 1 --mem=20000M --time='24:00:00' " \
                 "--output=/scratch/kallistos/Distance-Based_Data/Results/slurm_out.log "
SBATCH_SCRIPT = PREFIX + "runDistributionAware.sh"

JOB_DIR = HOME + "Jobs/"
JOB_FILE_PREFIX = "_jobs_"
JOB_FILE_SUFFIX = ".txt"
JOB_SCRIPT_PREDICTIONS = PREFIX + "runRandomHundredTimes.sh "
JOB_SCRIPT_PREDICTIONS_SVR = PREFIX + "runSVRRandomHundredTimes.sh "
JOB_SCRIPT_PREDICTIONS_FOREST_REGRESSOR = PREFIX + "runForestRegressorRandomHundredTimes.sh "
JOB_SCRIPT_SAMPLING = PREFIX + "sampleRandomHundredTimes.sh "
JOB_SCRIPT_FAILURE_RATE = PREFIX + "failureRateRandomHundredTimes.sh "

ALLOWED_TYPES = ["semi", "twise", "solvBased", "henard", "binom", "geom", "invgeom", "twogeom", "norm", "rand", "all", "local", "global", "grammar-based", "divDistBased"]


def printUsage():
    print("Usage:")
    print("./JobSubmitter <cluster> <solv/semi/random/grammar-based> <sampling/predicting/failureRate>")
    print("cluster\t The cluster to use")
    print("solv/semi/random/all\t Specifies if distribution-aware (solv) sampling, semi-random sampling, random sampling should be executed or all configurations should be used.")
    print("sampling/predicting/predictingDT/predictingFR/failureRate specifies wheter splconqueror should predict or sample")


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
    if (len(sys.argv) != 4):
        printUsage()
        exit(-1)

    type = sys.argv[2]

    if type not in ALLOWED_TYPES:
        raise KeyError("The type " + type + " is not allowed.")

    # Select the cluster
    cluster = sys.argv[1]

    found = False
    if (cluster == "anywhere"):
        found = True
    else:
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

    SBATCH_OPTIONS = SBATCH_OPTIONS + " -J " + type

    # Construct the jobs for the job-file
    jobs = []
    sampling = str(sys.argv[3]) == "sampling"
    failureRate = str(sys.argv[3]) == "failureRate"
    predicting = str(sys.argv[3]) == "predicting"
    predictingSVR = str(sys.argv[3]) == "predictingSVR"
    predictingFR = str(sys.argv[3]) == "predictingFR"
    if sampling:
        SBATCH_OPTIONS = SBATCH_OPTIONS + " --exclusive "
        for caseStudy in CASE_STUDIES:
            for run in range(RUNS_FROM, RUNS_TO + 1):
                jobString = "export LD_LIBRARY_PATH=/scratch/kallistos/:$LD_LIBRARY_PATH && "
                jobString += JOB_SCRIPT_SAMPLING + caseStudy[0] + " " + str(caseStudy[1]) + " " + type + " " + str(run) + " " + str(run)
                jobs.append(jobString)

    elif failureRate:
        for caseStudy in CASE_STUDIES:
            for run in range(RUNS_FROM, RUNS_TO + 1):
                jobString = "export LD_LIBRARY_PATH=/scratch/kallistos/:$LD_LIBRARY_PATH && "
                jobString += JOB_SCRIPT_FAILURE_RATE + caseStudy[0] + " " + str(caseStudy[1]) + " " + type + " " + str(run) + " " + str(run)
                jobs.append(jobString)
    elif predicting:
        for caseStudy in CASE_STUDIES:
            for run in range(RUNS_FROM, RUNS_TO + 1):
                jobString = "export LD_LIBRARY_PATH=/scratch/kallistos/:$LD_LIBRARY_PATH && "
                jobString += JOB_SCRIPT_PREDICTIONS + caseStudy[0] + " " + str(caseStudy[1]) + " " + type + " " + str(run) + " " + str(run)
                jobs.append(jobString)
    elif predictingSVR:
        for caseStudy in CASE_STUDIES:
            for run in range(RUNS_FROM, RUNS_TO + 1):
                jobString = "export LD_LIBRARY_PATH=/scratch/kallistos/:$LD_LIBRARY_PATH && "
                jobString += JOB_SCRIPT_PREDICTIONS_SVR + caseStudy[0] + " " + str(caseStudy[1]) + " " + type + " " + str(run) + " " + str(run)
                jobs.append(jobString)
    elif predictingFR:
        for caseStudy in CASE_STUDIES:
            for run in range(RUNS_FROM, RUNS_TO + 1):
                jobString = "export LD_LIBRARY_PATH=/scratch/kallistos/:$LD_LIBRARY_PATH && "
                jobString += JOB_SCRIPT_PREDICTIONS_FOREST_REGRESSOR + caseStudy[0] + " " + str(caseStudy[1]) + " " + type + " " + str(run) + " " + str(run)
                jobs.append(jobString)
    else:
        raise KeyError("The operation " + sys.argv[3] + " is not allowed!")

    # Write to the job file
    jobFile = JOB_DIR + "anywhere" + JOB_FILE_PREFIX + str(JOB_ID) + JOB_FILE_SUFFIX
    writeToFile(jobFile, jobs)

    # Submit the array job
    SBATCH_OPTIONS = SBATCH_OPTIONS + " --array=1-" + str(len(jobs)) + " "
    commandToSubmit = SBATCH + " " + SBATCH_OPTIONS + SBATCH_SCRIPT + " " + str(JOB_ID)
    print(commandToSubmit)
    outputString = executeCommand(commandToSubmit)
    print(outputString)


if __name__ == "__main__":
    main()

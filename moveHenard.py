#!/usr/bin/env python3


if __name__ == "__main__":
    import os
    import re
    myFolder = "old_Results/"
    newFolder = "Results"
    fileSet = set()

    for root, dirs, files in os.walk(myFolder):
        for fileName in files:
            if re.match(r"sampledConfigurations_henard_t[1-3].csv", fileName):
                found_file = str(os.path.join(root[len(myFolder):], fileName))
                os.rename('old_Results/' + found_file, 'Results/' + found_file)

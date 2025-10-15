#!/usr/bin/python3

import os, time, calendar, datetime, sys

from datetime import date, timedelta, datetime

from changeto_testlocation import change_to_test_location, locate_exe
from lab_grade import lab_grade_file, lab_missing_file_check, lab_help_message_check
from get_id import get_id
import operator

#
# Configuration directions
#
# 1. Set the base_name to point to the directory above the current directory.
#    In python terms, base_nane should be set so that base_name + "auto_grade/"
#    is the path to the directory that contains this file.
#
# 2. Change normal_deadline, if necessary
#
#

# base_name contains the path to the directory where this file tree is installed
# It should be one level above the directory that holds this code.

base_name = "/storage-home/k/kzz1/comp412/auto1/"

# Stuff after this point should be set on an annual basis to conform
# with the lab handout and/or the current state of the autograder software.
#

# Locations for test blocks (blocks) and timing blocks (timing)
# These are relative to the directory in base_name

blocks_dir = "auto_grade/blocks/"
timing_dir = "auto_time/timing_blocks/"

# The on-time due date for the assignment

normal_deadline = date(2025,9,15)        # set annually

# various limits and values related to deciding that a lab is
# early, on time, or late
#
early_day_limit = timedelta(days=2)       # grading rubric determines it
late_day_limit = timedelta(days=5)        # grading rubric determines it
archive_date = date(2100,1,1)             # impossibly far in the future

# Points allotted, out of 100, for Conformance to Specifications,
# Correctness, and Efficiency
#
# These should sum to 100 
#

# Set to match 2024 Handout -- KDC 08/2024
CONFORMS_SCORE = 30
CORRECT_SCORE  = 40
SCALE_SCORE = 30

def run_test(submission,path):
    global readme_points
    global sorted_tests
    
    # have already found and built the executable
    # record name and netid in result file
    result_file.write(current_id +'\t' + current_name + '\t')

    print("Testing Correctness\n")

    sum_extras   = 0
    sum_misses   = 0
    sum_expected = 0

    sum_conforms_errors = 0
    timeouts = 0
    num_tests = 0
    
    for test in sorted_tests:
        if not '.i' in test:
            continue
        extras,found,missed,total,conforms = lab_grade_file(path,test)

        num_tests += 1
        if extras == -1 and found == -1:
            if len(test) < 8:
                print("\t"+test+"\t\tSubmission timed out.")
            else:
                print("\t"+test+"\tSubmission timed out.")

            print("\t\t\tNo credit for this test.")
            timeouts += 1

        else:
            sum_expected += total
            sum_conforms_errors += conforms
            if len(test) < 8:
                print("\t"+test+"\t",end="")
            else:
                print("\t"+test,end="")
                
            print("\t"+str(extras)+" correct lines identified as errors")
            sum_extras += extras
            print("\t\t\t"+str(found)+" errors found, "+str(total)+" expected")
            sum_misses += missed
        print(" ")

    print("\t-------------------------")
    print("\t"+str(sum_extras)+" correct lines identified as errors")
    print("\t"+str(sum_misses)+" lines with errors missed\n")

    # Reduce possible points for any test that timed out
    possible = 100 - 100 * timeouts / num_tests

    correct = possible - possible * (sum_extras + sum_misses) / sum_expected
    
    # conformance testing
    # they get 50% if the tar file unpacks and runs ... that is,
    # they got this far in the autograder

    print("Testing Conformance\t(If we got this far, the tar file worked.)\n")
    if sum_conforms_errors < 0:
        sum_conforms_errors = -5
        print("\tMissing colon in one or more error messages.")
        print("\tWill also cause those messages to be missed.\n")

    conforms = 50 + sum_conforms_errors + readme_points
    
    # test for graceful handling of a bad file name
    missing_file = lab_missing_file_check(result_file)
    if missing_file == 0:
        print("\tNo 'ERROR' message on missing or bad file name")
    elif missing_file > 0:
        print("\tProduced 'ERROR' message on missing or bad file name")
        conforms += (25 * missing_file)   # 50% of points off is ERROR is not uppercase
    else:
        print("\tUnexpected corner case")

    # test for a helpmessage on the '-h' command-line option
    help = lab_help_message_check(result_file)
    if help == 0:
        print("\tNo help message found for '-h option")
    elif help < 4:
        print("\tHelp message is missing some mandated options  ("+str(help)+")")
    elif help == 4:
        print("\tHelp message check found all options")
    else:
        print("\tHelp message check found duplicate explanations")

    conforms += (help * 6.25)

    # Report results
    #
    # Stopped reporting scalability points and (thus) total points here
    # because of the difficulty in getting good timing results.
    # The "timer" is much more careful and, I hope, more accurate.
    print("\nScoring (on the provided test blocks):\n")
    if len(str(correct)) > 6:
        print("\tCorrectness:\t"+str(correct)[0:5]+"%")
    else:
        print("\tCorrectness:\t"+str(correct)+"%")
    if len(str(conforms)) > 6:
        print("\tConformance:\t"+str(conforms)[0:5]+"%")
    else:
        print("\tConformance:\t"+str(conforms)+"%")
        
    result_file.write(str(conforms)+"\t"+str(correct))

    # early/late day calculation.
    # negaive is early, positive is late
    diff = archive_date - normal_deadline
    if diff < -early_day_limit:
        diff = -early_day_limit
    elif diff > late_day_limit:
        diff = late_day_limit

    result_file.write("\t"+str(archive_date)+"\t"+str(diff.days)+"\n")
    
    return 0


def main():
    global root
    global sorted_tests
    global blocks_dir
    global base_name
    global current_name
    global current_id
    global result_file
    global failed_file
    global archive_date
    global readme_points
    
    root = os.getcwd()

    #for each submission:
    #1. make a tmp dir
    #2. cp the tar ball to the dir
    #3. extract and the tar ball
    #4. locate the makefile or the executable
    #5. ready to run with the executable

    print('Auto-grader Configuration:')
    print('  blocks found in :\t',blocks_dir)
    print('  normal deadline is:\t',str(normal_deadline))
    print(' ')

    if not os.path.isdir(base_name):
        print('\nNeed to set "base_name" in auto_grade/auto_grade.py\n\n')
        exit(-1)
            
    # set up the output files
    result_path = base_name + 'results/'

    result_file = open(result_path + "grader-points.txt",'w')
    failed_file = open(result_path + "grader-failed.txt",'w')

    # write file headers
    result_file.write('NetID\tName\tConform\tCorrect\tDate\tLate Days\n')
    failed_file.write('NetID\tName\n')

    path = base_name + blocks_dir
    sorted_tests = sorted(os.listdir(path))
    
    print('=======================================================================')
    
    for submission in sorted(os.listdir('./')):
        if os.path.isdir(submission):
            continue

        print('Testing submission: ' + submission)
        archive_date = change_to_test_location(submission)
                
        current_name, current_id, readme_points, keep_processing = get_id()

        if current_id == "":
            current_id   = submission.split('_', 1)[0]
        if current_name == "":
            current_name = current_id

        if keep_processing:

            print('Name: ' + current_name + ', NetId: ' + current_id,end="")
            print('\tDate From Files: ' + str(archive_date) + '\n')

            if not locate_exe(submission) == -1:
                dummy = run_test(submission,path)
            else:
                print('submission failed to build correctly')
                print('likely a problem with tar file, make file, or script')
                failed_file.write(current_id + '\t' + current_name+"\t(failed to build)\n")

        else:
            failed_file.write(current_name + '\t' + current_id+"\t(format of submission)\n")

        print('\nfinished testing submission ' + submission)
        print('=======================================================================')

        #clean up everything that was created during testing
        os.chdir(root)
        fixed_submission = submission.replace(" ", "\ ").replace("(", "\(").replace(")", "\)").replace("'", "\\'")
        folder = submission.split('.', 1)[0]
        fixed_folder = fixed_submission.split('.', 1)[0]
        os.system('rm -rf ' + fixed_folder)


    # close the grading files
    result_file.close()
    failed_file.close()

    print('\nGrading run complete.\n')
    exit(0)
    
if __name__ == "__main__":
    main()

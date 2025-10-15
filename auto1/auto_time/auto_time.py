#!/usr/bin/python3

import os, time, calendar, datetime, sys

from datetime import datetime
from time import process_time
from changeto_testlocation import change_to_test_location, locate_exe, get_language

from get_id import get_id
from lab_grade import get_ref_number, check_for_correctness
import operator

#
# Code to take timing measurements on the lab submission, using the SLOCs test set
# Runs each submission multiple times.
# Runs blocks in decreasing size, which seems to improve accuracy.
#    (seems mystical, but may be a memory hierarcy effect -- kdc)
#


#
# Configuration parameters
#

# base_name contains the path to the directory where this file tree is installed
# It should be one level above the directory that holds this code.

base_name = "/storage-home/k/kzz1/comp412/auto1/"

# These values determine the points (out of 100 for the total lab) 
# assigned to Efficiency and Scalabiliity. They should be checked
# annually against the lab handout.
#
EFF_SCORE   = 15
SCALE_SCORE = 15

# Locations for test blocks (blocks) and timing blocks (timing)
# These are relative to the directory in base_name

blocks_dir = "auto_grade/blocks/"
timing_dir = "auto_time/timing_blocks/"

def run_timing_block(block_name,block_num,check):
    global l1r_numbers
    
    path = base_name + timing_dir

    if check == False:
        command_line = "timeout 60.0s ./412fe -p "+path+block_name+" >&/dev/null"
    else:
        tmpname = "./"+current_id+"-"+block_name+".out"
        command_line = "timeout 60.0s ./412fe -p "+path+block_name+" >&"+tmpname
        
    start_tic = time.perf_counter()
    os.system(command_line)
    stop_tic  = time.perf_counter()
    elapsed = stop_tic - start_tic 

    if check:
        result = check_for_correctness(block_name,tmpname,l1r_numbers[block_num])
        os.system("rm "+tmpname)

        if result == False:  # pass failure signal back up chain of calls
            elapsed = -1

    return elapsed
        
def run_test(submission):
    global scaling
    global t_names
    global t_sizes

    # have already found and built the executable
    #record name and netid in result file
    result_file.write(current_id + '\t' + current_name)

    # Scalability testing
    scales = 0

    t_times =  [1000000, 1000000, 1000000, 1000000,  1000000,  1000000,  1000000,  1000000]
    timeout = [False, False, False, False, False, False, False, False]
    n_trials = 5
    
    print("Testing Scalability:\t(minimum time of "+str(n_trials)+" runs)\n")

    # To change the number of repeats of each file, adjust n_trials, above
    for i in range(0,n_trials):
        n = 7
        while n > -1:
            if timeout[n] == False:
                if i == 0:   # check correctness on 1st run of big block
                    seconds = run_timing_block(t_names[n],n,True)
                else:
                    seconds = run_timing_block(t_names[n],n,False)
            else:
                seconds = 60

            if seconds == -1: # failed correctness check
                t_times[n] = 60
                timeout[n] = True
                
            elif seconds < t_times[n]:
                t_times[n] = seconds

            elif seconds > 59 and timeout[n] == False:  # timeout
                timeout[n] = True
                print("\n\tTimed out on block "+t_names[n])

            n = n -1

    for i in range(0,8):
        print("\t"+t_names[i]+":  \t"+str(t_times[i])[0:6]+" seconds")
        result_file.write("\t"+str(t_times[i])[0:6])

    print(" ")  # pretty up the output

    # analyze scaling
    linear_ct = 0
    noninc_ct = 0
    quad_ct   = 0
    timed_out = 0

    scaling   = ""
    language  = "\t"
    
    for i in range(0,7):
        if t_times[i] == 60:
            timed_out = 1
        ratio = t_times[i+1]/t_times[i]
        if ratio < 1:
            noninc_ct +=1
        if ratio < 2.3:
            linear_ct += 1
        elif ratio > 3.6:
            quad_ct   += 1
        else:
           noninc_ct  += 1

    if timed_out == 1:
        scaling       = " timed-out "
        language      = "timed-out"
        scale_points  = 0
        eff_points    = 0

    elif noninc_ct == 0:
        scaling      += " linear"
        scale_points  = 100
    elif noninc_ct == 1:
        scaling      += " linear-w-1-jump"
        scale_points  = 100
    elif quad_ct > 2: 
        scaling       = " quadratic"
        scale_points  = 0
    else:
        scaling       = " anomaly"
        scale_points  = 0

    if timed_out == 0:
        # analyze efficiency

        time = t_times[7] 
        language = get_language()

        if language.find("python") > -1:
            if time <= 2.5:
                eff_points = 100
            elif time > 5.0:
                eff_points = 0
            else:
                eff_points = 100 - (time - 2.5) / 0.025  # 0.025 is (5 - 2.5) / 100

        elif language.find("java") > -1:
            if time <= 1.5:
                eff_points = 100
            elif time > 2.5:
                eff_points = 0
            else:
                eff_points = 100 - (time - 1.0) / 0.01
            
        else:  # others are all 1 sec and 2 sec
            if time <= 1.0:
                eff_points = 100
            elif time > 2.0:
                eff_points = 0
            else:
                eff_points = 100 - (time - 1.0) / 0.01    

    # make zeros print as 0.0
    scale_points = round(scale_points * SCALE_SCORE / 100.0,2)
    eff_points   = round(eff_points * EFF_SCORE /100.0,2)

    if len(str(scale_points)) > 6:
        print("Scaling score is \t"+str(scale_points)[0:5])
    else:
        print("Scaling score is \t"+str(scale_points))

    if scale_points == 0.0:
        print("\tTiming results need to be examined manually.\n")
        
    if len(str(eff_points)) > 6:
        print("Efficiency score is \t"+str(eff_points)[0:5]+"\t( "+language+")")
    else:
        print("Efficiency score is \t"+str(eff_points)+"\t( "+language+")")

    # record scaling and efficiency points in results file
    if noninc_ct > 0:
        scaling += " anomaly"
        print("\n\tAnomalous behavior: "+str(noninc_ct)+" inputs showed no growth")
        result_file.write("\t"+language+"\t"+scaling+"\t"+str(scale_points)+"\t"+str(eff_points)+"\t*\n")
    else:
        result_file.write("\t"+language+"\t"+scaling+"\t"+str(scale_points)+"\t"+str(eff_points)+"\n")
    
    return 0


def main():
    global root
    global tests
    global blocks_dir
    global base_name
    global current_name
    global current_id
    global result_file
    global failed_file
    global scaling
    global t_names, t_times, l1r_numbers
    

    root = os.getcwd()

    #for each submission:
    #1. make a tmp dir
    #2. cp the tar ball to the dir
    #3. extract and the tar ball
    #4. locate the makefile or the executable
    #5. ready to run with the executable

    print('Lab 1 Autotimer: using Scalability SLOCs blocks\n')

    if not os.path.isdir(base_name):
        print('\nNeed to set "base_name" in auto_time/auto_time.py\n\n')
        exit(-1)
    
    # set up the output files
    result_path = base_name + 'results/'

    try: 
        result_file = open(result_path + "timer-points.txt",'w')
        failed_file = open(result_path + "timer-failed.txt",'w')
    except:
        print("Failed to open result file.")
        print("autotimer terminates.")
        exit(-1)

    # write file headers
    result_file.write('NetId\tName\tT1k\tT2k\tT4k\tT8k\tT16k\tT32k\tT64k\tT128k\tLang.\tScaling\tScal Pts\tEff Pts\n')
    failed_file.write('NetID\tName\n')

    # test-set specific initializations
    t_names =  ["T1k.i","T2k.i","T4k.i","T8k.i","T16k.i","T32k.i","T64k.i","T128k.i"]
    t_sizes =  [1, 2, 4, 8, 16, 32, 64, 128]

    # get number of lines processed by lab1_ref for each block
    print("Gathering operation counts with lab1_ref.")
    l1r_numbers = [0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(0,len(l1r_numbers)):
        l1r_numbers[i] = get_ref_number(base_name+timing_dir,t_names[i])

    print('\n=======================================================================')
        
    for submission in sorted(os.listdir('./')):
        if os.path.isdir(submission):
            continue

        print('Testing submission: ' + submission)
        submission_date = change_to_test_location(submission)
                
        current_name, current_id, deduct, keep_processing = get_id()

        if current_id == "":
            current_id   = submission.split('_', 1)[0]
        if current_name == "":
            current_name = current_id

        if keep_processing:
            
            print('Name: ' + current_name + ', NetID: ' + current_id,end="")
            print('\tDate From Files: ' + str(submission_date) + '\n')

            if not locate_exe(submission) == -1:
                dummy = run_test(submission)
            else:
                print('submission failed to build correctly')
                print('likely a problem with tar file, make file, or script')
                failed_file.write(current_id + '\t' + current_name+"\t(failed to build)\n")
        else:
            failed_file.write(current_name + '\t' + current_id+"\t(format of submission)\n")

        print('\nfinished timing run on submission ' + submission )
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

    print('\nTiming run complete.\n')
    exit(0)
    
if __name__ == "__main__":
    main()

# Part of the COMP 412 autotimer (and autograder)

import os, time

global ref_number

def get_ref_number(path,block):
    
    command = "~comp412/students/lab1/lab1_ref -e "+path+block+">& ./"+"ref_output"
    os.system(command)
    
    # open the output file from lab1_ref
    no_output = 1
    try:
        ref_file = open("./ref_output",'r')
        no_output = 0;
    except:
        print("***\tlab1_ref failed to produce output for")
        print("\t"+path+block+"\n")
        print("***\tTimer halts.")
        exit(-1)
        
    line = ref_file.readline()
    while line != "":
        pos = line.find("Processed ")
        if pos != -1:
            break
        line = ref_file.readline()
        
    while line[pos] != ' ':
        pos += 1

    pos += 1  # pos should be index of 1st digit
    end = pos
    while line[end].isdigit():
        end += 1

    n = int(line[pos:end])        
    os.system("rm ./ref_output")
    return n

def check_for_correctness(block,output,l1r_num):

    result = True  # False indicates something went awry

    no_output = 1
    try:
        test_file = open(output,'r')
        no_output = 0
    except:
        print("***\tNo output file for test block",block)
        return False


    line = test_file.readline()
    found = 0
    while line != "":
        pos = line.find("Processed ")
        if pos != -1:
            found = 1
            break
        line = test_file.readline()

    if found == 1:
        while line[pos] != ' ':
            pos += 1

        pos += 1 # pos should be index of 1st digit
        end = pos
        while line[end].isdigit():
            end += 1

        n = int(line[pos:end])
    else:
        n = -1
        
    if n == l1r_num:
        result = True
    else:
        result = False
        print("-->\tFailed correctness check on block",block)
        print("\tOutput from submission was:\n\t------------------------------")
        test_file.seek(0) # rewind file
        line = test_file.readline()
        while line != "":
            print("\t",line)
            line = test_file.readline()
        print("\t------------------------------")

    return result



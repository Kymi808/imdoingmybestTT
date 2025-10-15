# Part of the COMP 412 autograder

import os, time
from time import process_time, perf_counter

def check_output(file_name,line_nums):
    #print('\nIn \'check_output('+file_name+', ('+line_nums+'))\'')

    if not os.path.isfile(file_name):
        print('check_output() called with bogus file name \'' + file_name +'\'')
        exit(0)

    o_file = open(file_name,'r');

    # build a list of the correct lines
    correct_lines = [int(i) for i in line_nums.split() if i.isdigit()]

    conforms = 0
    
    # build a list of the lines from the output file being scored
    output_lines = [ ] + [-1]
    while True:
        o_line = o_file.readline().strip(' ')
        if o_line == '':
            break

        if o_line.find("ERROR") != -1:
            # found the ERROR at the head of the line
            t_line = o_line[6:].strip(' ')

            if t_line[:1].isdigit():
                if t_line.find(':') == -1:  # no colon
                    conforms = -5
                else:
                    t_line = t_line.split(':',1)[0]
                    if not int(t_line) == output_lines[-1]:
                        output_lines = output_lines + [int(t_line)]

    o_file.close() # clean up

    # check for two kinds of errors
    error_count   = 0
    extra_lines   = 0
    missing_lines = 0
    found_lines   = 0
    
    #print("\noutput_lines")
    #print(output_lines[1:])
    #print("\ncorrect_lines")
    #print(correct_lines)

    for out in output_lines[1:]:
        if not out in correct_lines:
            #print('extra line: ' + str(out))
            extra_lines += 1

    for cor in correct_lines:
        if not cor in output_lines:
            missing_lines += 1
        if cor in output_lines:
            found_lines +=1


    #print('Found ' + str(error_count) + ' errors')
    #print('Correct \# of bad lines was ' + str(len(correct_lines)))

    return extra_lines, found_lines, missing_lines, len(correct_lines), conforms

def check_missing_file_name(file_name,res):
    if not os.path.isfile(file_name):
        print("Check for missing file name produced no output")
        return 0

    o_file = open(file_name,'r');

    #look for "ERROR" in the file
    error_message_found = 0;
    while True:
        o_line = o_file.readline().strip(' ')

        if o_line == '':
            break;

        if o_line.find("Traceback") != -1:
            print("Missing file test produced a Traceback.")
            error_message_found = 0
            break

        if o_line.find("ERROR") != -1:
            error_message_found = 1

        o_line = o_line.lower()
        if error_message_found == 0 and o_line.find("error") != -1:
            error_message_found = 0.5
            print("\tProduced 'file not found' message, but ERROR was not in uppercase (1)")

    return error_message_found


def check_for_help_message(file_name,res):
    if not os.path.isfile(file_name):
        print("Check for missing help message check produced no output")
        return 0

    o_file = open(file_name,'r');

    #look for "-h" in the file
    found_h = 0
    found_s = 0
    found_p = 0
    found_r = 0
    while True:
        o_line = o_file.readline()  #.strip(' ')
        if o_line == '':
            break
        
        if o_line.find("-h"):
            found_h = 1

        if o_line.find("-s"):
            found_s = 1

        if o_line.find("-p"):
            found_p = 1

        if o_line.find("-r"):
            found_r = 1

    return found_h + found_s + found_p + found_r


# grade a file that may contains errors
def lab_grade_file(path,file):

    # build list of line numbers where we expect errrors
    base = file.split('.',1)[0]
    lines_file_name = path + base  + '.errs'
    iloc_file_name  = path + base + '.i'

    if not os.path.isfile(lines_file_name):
        print('\n==> test block \'' + file +'\' is missing a .errs file')
        print('halting all tests')
        exit(0)
        
    e_file = open(lines_file_name,'r')

    # only one line in the file
    line = e_file.readline()
    if line == "":
        print('==> File \'' + base + '\' is formatted badly.')
        print('    See note in that directory.')
        exit(0)
    line = line.rstrip('\n') # get rid of the newline

    e_file.close()


    command_line = 'timeout 60 ./412fe -p ' + iloc_file_name + ' >& ./' + base + '.output'

    # check if timeout occurs; if it does not terminate, it gets no credit
    start_tic = time.perf_counter()    
    os.system(command_line)
    stop_tic = time.perf_counter()
    if (stop_tic - start_tic) > 59.5:
        return -1, -1, -1, -1, 0

    extras, found, missing, total, conforms = check_output('./' + base + '.output',line)
    
    return extras, found, missing, total, conforms

# Check to see if it handle a bad input file name gracefully
def lab_missing_file_check(res):
    
    # set stdin to /dev/null in case lab reads from terminal if open
    # fails. Use timeout as a hedge against other bad results from the open()
    fname = "./does_not_exist"
    command_line = 'timeout 20s ./412fe -p ' + fname + '.mine >& ./'+ fname+ '.output </dev/null'
    #print('--> executing \'' +command_line + '\'')
    os.system(command_line)

    result = check_missing_file_name(fname+".output",res)
    return result

# Check to see if it prints out a complete help message
def lab_help_message_check(res):
    fname = "./helpmessage"
    command_line = './412fe -h >& ./'+fname+'.output'
    os.system(command_line)

    result = check_for_help_message(fname+".output",res)
    return result



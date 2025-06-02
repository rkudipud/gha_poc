#!/usr/intel/pkgs/python3/3.11.1/bin/python3

from __future__ import print_function
from timeit import default_timer as timer
import argparse
from pathlib import Path
import time
import resource
import subprocess
import filecmp
import glob
import os
import shutil
import uuid
import sys
import hashlib
import shutil
import signal
import re
import tracemalloc
import os
import itertools
import threading
import time
import sys
import pickle


# Global Variables
errorVar = False
done = False


# Compiled regex for quick match
SCRIPT_PATH_REGEX = re.compile(r"Script:\s*(.*)/runs/(.*)", flags=re.I)
VERSION_REGEX = re.compile(r'\s+Version\s+(\S+)\s+', flags=re.I)
FILEPATH_REGEX = re.compile(r"(\$\S+|/\S+)", flags=re.I)

# Graceful Exiter
class GracefulExiter:
    def __init__(self):
        self.state = False
        signal.signal(signal.SIGINT, self.change_state)

    def change_state(self, signum, frame):
        print(f"{bcolors.WARNING}ctrl+c Received, press again to exit{bcolors.ENDC}", flush=True )
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.state = True

    def exit(self):
        return self.state

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Here is the animation
def animate():
    width = os.get_terminal_size().columns
    for c in itertools.cycle(["|", "/", "-", "\\", "|", "/", "-", "\\"]):
        if done:
            break
        print(f"Processing Log....... {c}", flush=True, end="\r")
        time.sleep(0.1)

############################################ Helper functions ########################################
# if file path checker
def file_path(string):
    """ File path checker """
    abs_path = os.path.abspath(string)
    if os.path.isfile(abs_path):
        return string
    else:
        raise FileNotFoundError(abs_path)

# Dir_path checker
def dir_path(string):
    """ Directory path checker """
    abs_path = os.path.abspath(string)
    if os.path.isdir(abs_path):
        return string
    else:
        raise NotADirectoryError(string)

# Identical file checker
def are_files_identical(file1, file2):
    """ Identical file checker """
    return filecmp.cmp(file1, file2, shallow=True)

# calculate md5 of a file
def calculate_md5(file_path):
    """ Calculate MD5 of a file """
    hash_md5 = hashlib.md5()
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    else:
        return False


# checksum checker
def checksum(file1, file2):
    hash1 = hashlib.md5(open(file1, 'rb').read()).hexdigest()
    hash2 = hashlib.md5(open(file2, 'rb').read()).hexdigest()
    return hash1 == hash2


######################################## support files definitions #####################################
# Creates id card for the source folder
def id_creator(dest_path,block_name, tech, task, reference_side, implemented_side):
    id_file_path = os.path.join(dest_path,block_name, "id.csh")
    if (os.path.exists(id_file_path)):
        with open(id_file_path, 'r') as file:
            content = file.readlines()
        for line in content:
            if 'fub_collaterals' in line:
                # print(f'Fub Collaterals already exists with : {content.index(line)}', flush=True)
                matches = re.search(r"\(.*\)", line, re.IGNORECASE | re.VERBOSE)
                if (reference_side not in matches.group()):
                    # print (f"not, {content[content.index(line)]}", flush=True)
                    content[content.index(line)] = content[content.index(line)].replace(")", f"{reference_side} )")
                if (implemented_side not in matches.group()):
                    # print (f"not, {content[content.index(line)]}", flush=True)
                    content[content.index(line)] = content[content.index(line)].replace(")", f"{implemented_side} )")
            if 'fub_tasks' in line:
                # print(f'Fub Tasks already exists with : {content.index(line)}', flush=True)
                matches = re.search(r"\(.*\)", line, re.IGNORECASE | re.VERBOSE)
                if (task not in matches.group()):
                    # print (f"not, {content[content.index(line)]}", flush=True)
                    content[content.index(line)] = content[content.index(line)].replace(")", f"{task} )")
        # print(content)
        with open(id_file_path, 'w') as file:
            file.writelines(content)
    else:

        data = """#!/bin/csh -f

set fub_name = {block_name}
set fub_collaterals = \"( {reference_side} {implemented_side} )\"
set fub_tasks = \"( {task} )\"
set fub_techs = \"( {tech} )\"
#nb_mode:64G_4C

        """.format(block_name=block_name, reference_side=reference_side, implemented_side=implemented_side, task=task, tech=tech)
        with open(id_file_path, 'w') as file:
            file.writelines(data)
    print(f"{bcolors.OKCYAN}---> ID file Created{bcolors.ENDC}", flush=True)


# Creates vars.tcl file
def vars_creator(extr_dir):
    vars_file_path = os.path.join(extr_dir, "scripts", "vars.tcl")
    data = """

#library setup
set ivar(link_libs) ""  

set lib_scenario [ lindex $ivar(setup,hip_oc_types_list) 0 ]
set libs_copied [glob -nocomplain -path $ward/src_backup/library/db/ * ] 

set all_libs "" 
foreach individual_path $libs_copied { 
    regexp {([^\/]+$)} $individual_path libname 	
    lappend all_libs $libname 
}


set ivar(link_libs) $all_libs 
foreach linkLib $ivar(link_libs) {  
    set ivar(lib,$linkLib,use_ccs) 0 
    set ivar(lib,$linkLib,db_nldm_filelist,$lib_scenario) [glob -nocomplain -path $ward/src_backup/library/db/ *$linkLib* ] 
} 


    """
    if (os.path.exists(vars_file_path)):
        shutil.copyfile(vars_file_path, os.path.join(extr_dir, "scripts", "vars.tcl_orig"))
    with open(vars_file_path, "a+") as vars:
        vars.write("\n")
        vars.write(data)
        print(f"{bcolors.OKCYAN}---> Modified Vars{bcolors.ENDC}", flush=True)
    return


def rtl_list_path_modifier(file_path):
    if (os.path.exists(os.path.join(file_path))):
        shutil.copyfile(os.path.join(file_path),os.path.join(file_path.rsplit("/", 1)[0], f"{file_path.rsplit('/', 1)[-1]}_orig"))
    os.system(f"sed -i '/lappend/ s/\"//g' {os.path.join(file_path)}")
    os.system(f"sed -i 's#/nfs/#\$env(ward)/src_backup/rtl/nfs/#g' {os.path.join(file_path)}")
    os.system(f"sed -i 's#/p/#\$env(ward)/src_backup/rtl/p/#g' {os.path.join(file_path)}")


    if ( "_f.tcl" in os.path.basename(file_path)):
        with open(file_path, "a") as f_tcl:
            f_tcl.write("set ::env(ward) $env(ward)")

    print(f"{bcolors.OKCYAN}--> Modified {file_path.rsplit('/', 1)[-1]} to new paths{bcolors.ENDC}", flush=True)
    return

def dotf_processor(dotf_entries, rtl_entries, extr_dir):
    # reads the rtl_data set ( orig_path, copied_path, md5)
    # reads the dotf files set( copied_path, orig_path, md5)
    
    for dotf_file in dotf_entries.keys():
        #print(dotf_files)
        with open(dotf_file, 'r') as dot_f_file:
            for Line in dot_f_file:
                line = Line.strip()
                if FILEPATH_REGEX.match(line):
                    matched_path = FILEPATH_REGEX.match(line).group(1).strip()
                    if ( re.match(r"^(/p|/nfs)",matched_path, re.I) ):
                        #print(matched_path)
                        if(matched_path in rtl_entries.keys()):
                            #print("Path present in rtl_data", rtl_entries[matched_path])
                            copied_path = (rtl_entries[matched_path][0].split(extr_dir)[-1])
                            mod_path = (f"$ward{copied_path}")
                            #print(mod_path)
                            os.system(f"sed -i 's#{matched_path}#{mod_path}#' {os.path.join(dotf_file)}")
        print(f"{bcolors.OKCYAN}---> Processed dotf files{bcolors.ENDC}", flush=True)


############################################## function Main ############################################
def main_fm():

    #######################################################################################################################
    # parsing input
    global done
    global errorVar
    global verbose

    # reads the rtl_data set ( orig_path, copied_path, md5)
    rtl_entries = dict()
    # reads the dotf files set( copied, orig_path, md5)
    dotf_entries = dict()


    # stats
    # global varibales
    ward = ""
    block_name = ""
    tech = ""
    flow = ""
    task = ""
    log_name = ""

    # predefined variables
    # initial states
    libs = False
    extr_dir = ""


    ref = False
    impl = False
    pre_eco = False
    post_eco = False
    rtl_mode = False
    gate_mode = False
    design = False
    upf = False
    td_files = False
    child = False

    # stats
    count = 0
    rtl_files = 0
    design_files = 0
    lib_files = 0
    upf_files = 0


    with open(log_path, 'r') as source_log:
        for line in source_log:
            count += 1
            try:
                if VERSION_REGEX.match(line):
                    cfm_version = VERSION_REGEX.match(line).group(1)
                    print(f"{bcolors.OKBLUE}Formality version:{bcolors.ENDC} {cfm_version}", flush=True)
                    
                if SCRIPT_PATH_REGEX.match(line):
                    ward=SCRIPT_PATH_REGEX.match(line).group(1)
                    data_path = SCRIPT_PATH_REGEX.match(line).group(2)
                    data_path = data_path.split('/')
                    block_name=data_path[0]
                    tech=data_path[1]
                    flow=data_path[2]
                    task=data_path[3]
                    log_name=log_path.rsplit('/',1)[-1]

                    try:
                        print(f"{bcolors.OKBLUE}Ward Path:{bcolors.ENDC} {ward}", flush=True)
                        print(f"{bcolors.OKBLUE}Block_Name:{bcolors.ENDC} {block_name}", flush=True)
                        print(f"{bcolors.OKBLUE}Block_Tech:{bcolors.ENDC} {tech}", flush=True)
                        print(f"{bcolors.OKBLUE}Block_Flow:{bcolors.ENDC} {flow}", flush=True)
                        print(f"{bcolors.OKBLUE}Block_Task:{bcolors.ENDC} {task}", flush=True)
                        print(f"{bcolors.OKBLUE}Block_Log:{bcolors.ENDC} {log_name}\n", flush=True)

                        print(f"{bcolors.BOLD}Creating Extracted Dirs{bcolors.ENDC}", flush=True)
                        extr_dir = os.path.join(dest_path,block_name)

                        if (os.path.exists(dest_path)):
                            os.makedirs(os.path.join(extr_dir), exist_ok=True, mode=0o777)
                            os.makedirs(os.path.join(extr_dir, "scripts"), exist_ok=True, mode=0o777)
                            os.makedirs(os.path.join(extr_dir, "scripts", task), exist_ok=True, mode=0o777)
                            if os.path.exists(os.path.join(extr_dir, task+".orig.log")):
                                if checksum(os.path.join(extr_dir, task+".orig.log"), log_path):
                                    print(f"{bcolors.WARNING}-->same log file present in Testcase{bcolors.ENDC}\n", flush=True)
                            else:
                                shutil.copyfile(log_path, os.path.join(extr_dir, task+".orig.log"))
                    except OSError as error:
                        print(f"{bcolors.WARNING}Error in creating directory :{bcolors.ENDC}\n" + str(error), flush=True)
                        errorVar = True
                        sys.exit(1)


                ####### Self Copiers
                # SVF files and copy it
                svf_file = re.match(r"\s*SVF\s*set\s*to\s*'(.*)'\s*",line,re.I)
                if(svf_file):
                    if ( not os.path.exists(os.path.join(extr_dir,implemented_side)) ) :
                        os.makedirs(os.path.join(extr_dir,implemented_side),exist_ok = True,mode=0o777)
                    
                    shutil.copyfile(svf_file.group(1).split(" ")[0], os.path.join(extr_dir,implemented_side,os.path.basename(svf_file.group(1).split(" ")[0])),follow_symlinks=True)
                    print(f"{bcolors.OKGREEN}copied{bcolors.ENDC} {svf_file.group(1).split('/')[-1]}", flush=True)
    


                ### Mode Setters
                #read standard cell libs
                if (re.match(r"^read_libs\s+", line,re.I)):
                    print(f"{bcolors.OKBLUE}Working on db files{bcolors.ENDC}", flush=True)
                    libs = True

                #captures "loading db file"
                db_file = re.match(r"\s*loading\s*db\s*file\s*'(.*)'",line,re.I)
                if(db_file and not 'gtech.db' in db_file.group(1)):
                    db_path = os.path.join(extr_dir,"src_backup","library","db")

                    if (not os.path.exists(db_path)) :
                        os.makedirs(db_path,exist_ok = True,mode=0o777)

                    shutil.copyfile(db_file.group(1).strip(), os.path.join(db_path,os.path.basename(db_file.group(1).strip())),follow_symlinks=True)
                    if debug:
                        print (f"copied db file: {db_file.group(1).rsplit('/',1)[-1]}")

                    lib_files +=1

                
                #Captures reference design
                side = re.match(r"\s*(INTEL_INFO|INFO)?\s*:?\s*Reading\s*(Reference|impleme.*)\s*(Design|upf)",line,re.I)
                if (side and re.search('refer',line, re.IGNORECASE)):
                    ref = True; impl = False
                if (side and re.search('implem',line, re.IGNORECASE)):
                    ref = False; impl = True
                if (side and re.search('design',line, re.IGNORECASE)):
                    design = True; upf = False
                if (side and re.search('upf',line, re.IGNORECASE)):
                    upf = True; design = False; child = False

                
                
                if(re.search(r"\s*(INTEL_INFO|INFO)?\s*:?\s*read_rtl\s*",line,re.I)):
                    rtl_mode = True; gate_mode = False; child = False

                if(re.search(r"\s*(INTEL_INFO|INFO)?\s*:?\s*read_gate\s*",line,re.I)):
                    rtl_mode = False; gate_mode = True; child = False

                if(re.search(r"\s*(INTEL_INFO|INFO)?\s*:?\s*reading child netlists\s*",line,re.I)):
                    child = True

                    


				#experimental - no actual function no logic
                if( (re.search(r"\s*file list\s*:\s*",line,re.I)) and re.search (r"rtl_list_2stage_sim.tcl",line,re.I)):
                    print(f"Experimental: {bcolors.UNDERLINE}rtl_list_2stage for sim exists{bcolors.ENDC}", flush=True)

                if( (re.search(r"\s*file list\s*:\s*",line,re.I)) and re.search (r"rtl_list_2stage.tcl",line,re.I)):
                    print(f"Experimental: {bcolors.UNDERLINE}rtl_list_2stage file (rtl) exists{bcolors.ENDC}", flush=True)

                if( (re.search(r"\s*creating Loader UPF\s*",line,re.I)) ):
                    print(f"{bcolors.WARNING} IT has Hier UPF be careful and scrutunise all the UPF files{bcolors.ENDC}", flush=True)


                ## this is upf self sourced files+
                sourced_file = re.search(r"\s*Sourcing\s*file\s*'(.*)'\s*",line,re.I)
                if(sourced_file and (design or upf)):
                    sourced_file = sourced_file.group(1).strip()
                    if ( (reference_side if ref else implemented_side) in sourced_file ):
                        path_after_side = sourced_file.split((reference_side if ref else implemented_side))[-1]
                        mid_path = os.path.join(extr_dir,(reference_side if ref else implemented_side))
                        new_path = os.path.join(mid_path,path_after_side.rsplit('/',1)[0].lstrip('/'))
                    else:
                        new_path = os.path.join(extr_dir,"src_backup","rtl",sourced_file.rsplit('/',1)[0])

                    os.makedirs(new_path,exist_ok = True,mode=0o777)
                    shutil.copyfile(sourced_file, os.path.join(new_path,os.path.basename(sourced_file)),follow_symlinks=True)


                
                # copy design verilog files for designs - the loaded design files
                design_file = re.search(r"\s*loading\s*(verilog|include|upf|design ware)\s*.*file\s*'(.*)'\s*",line,re.I)
                if(design_file and (design or upf)):
                    design_file = design_file.group(2).strip()
                    ## Add logic for child module
                    if ( child and not rtl_mode and gate_mode and not upf ):
                        child_file_ward = design_file.replace(ward, "").strip()
                        child_regx_er = re.match(r"(.+\/)*(.+)\/(\S*)\.(\S*)$",child_file_ward,flags=re.I)
                        child_name = child_regx_er.group(1).split("/")[2]
                        side_dir = os.path.join(dest_path,block_name, (golden_side if ref else implemented_side ), "child_modules",child_name)
                    else:
                        side_dir = os.path.join(extr_dir,(implemented_side if impl else reference_side))

                    os.makedirs(side_dir,exist_ok = True,mode=0o777)

                    #copy upf files
                    if( upf ):
                        if ( "loader" in design_file ) :
                            child = True
                            print("upf loader found")
                            continue
                        else:
                            if ( child ):
                                print ("in child upf")
                                child_file_ward = design_file.replace(ward, "").strip()
                                child_regx_er = re.match(r"(.+\/)*(.+)\/(\S*)\.(\S*)$",child_file_ward,flags=re.I)
                                child_name = child_regx_er.group(1).split("/")[2]
                                new_path = os.path.join(dest_path,block_name, (golden_side if ref else implemented_side ), "child_modules",child_name)
                                print(f"child upf: {new_path}")
                            else:
                                if ( (reference_side if ref else implemented_side) in design_file ):
                                    path_after_side = design_file.split((reference_side if ref else implemented_side))[-1]  
                                    mid_path = os.path.join(extr_dir,(reference_side if ref else implemented_side))
                                    new_path = os.path.join(mid_path,path_after_side.rsplit('/',1)[0].lstrip('/'))
                                else:
                                    mid_path = os.path.join(extr_dir,"src_backup","rtl")
                                    new_path = mid_path+(design_file.rsplit('/',1)[0])
                                    
                        os.makedirs(new_path,exist_ok = True,mode=0o777)
                        shutil.copyfile(design_file, os.path.join(new_path,os.path.basename(design_file)),follow_symlinks=True)
                        print(f"trying to {os.path.join(new_path,os.path.basename(design_file))}")
                        print(f"{bcolors.OKGREEN}copied{bcolors.ENDC} {design_file.split('/')[-1]}", flush=True)
                        upf_files +=1

                    #for gate mode ref and impl design file copy
                    if(gate_mode and not rtl_mode and not upf):
                        if ( child ) :
                            print(f" child dest path: {side_dir}")
                            os.makedirs(side_dir,exist_ok = True,mode=0o777)
                            shutil.copytree(design_file.rsplit("/",1)[0], side_dir, symlinks=True, dirs_exist_ok = True)
                        else :
                            sub_break = design_file.split(reference_side if ref else implemented_side)
                            #print(sub_break)
                            copy_dir = os.path.join(side_dir,sub_break[-1].rsplit('/',1)[0].split("/",1)[-1])
                            os.makedirs(copy_dir,exist_ok = True,mode=0o777)
                            shutil.copyfile(design_file, os.path.join(copy_dir,os.path.basename(design_file)),follow_symlinks=True)
                            print(f"{bcolors.OKGREEN}copied{bcolors.ENDC} {design_file.split('/')[-1]}", flush=True)
                            design_files +=1

                    #rtl mode to copy files listed in rtllist file
                    if(rtl_mode and not gate_mode and not upf):
                        #creating src_backup/rtl
                        new_path = ""
                        actual_md5 = calculate_md5(design_file)
                        if ("cfg.sv" in os.path.basename(design_file) ):
                            #print (f"FOund cgg.sv file, {design_file}")
                            final_path = os.path.join(extr_dir,( reference_side if ref else implemented_side ),os.path.basename(design_file))
                            shutil.copyfile(design_file, final_path,follow_symlinks=True)
                            rtl_entries[design_file] = [final_path, actual_md5]

                        if ( (reference_side if ref else implemented_side) in design_file ):
                            path_after_side = design_file.split((reference_side if ref else implemented_side))[-1]  
                            mid_path = os.path.join(extr_dir,(reference_side if ref else implemented_side))
                            new_path = os.path.join(mid_path,path_after_side.rsplit('/',1)[0].lstrip('/'))
                        else:
                            mid_path = os.path.join(extr_dir,"src_backup","rtl")
                            new_path = mid_path+(design_file.rsplit('/',1)[0])

                        os.makedirs(new_path,exist_ok = True,mode=0o777)
                        final_path = os.path.join(new_path,os.path.basename(design_file))
                        shutil.copyfile(design_file, final_path,follow_symlinks=True)
                        rtl_entries[design_file] = [final_path, actual_md5]
                        rtl_files +=1

                
                ##for .f files which might be read in
                f_file = re.search(r"read_sverilog\s*.* -f(.*) -",line,re.I)
                #rtl mode to copy files listed in rtllist file
                if(rtl_mode and not gate_mode and not upf and f_file is not None):
                    new_path = ""
                    #print("inside dot_f block")
                    #dotf_arr is [-fpath, -f path] process it.
                    dotf_arr = re.findall(r"(\s*-f\s+\S+\.f)",line,re.I)
                    if ( debug ) :
                        print(f"dotf_arr {dotf_arr}")
                    #creating src_backup/rtl
                    tc_rtl_path = os.path.join(extr_dir,"src_backup","rtl")
                    if (not os.path.exists(tc_rtl_path)) :
                        os.makedirs(tc_rtl_path,exist_ok = True,mode=0o777)
                    
                    for dotf in dotf_arr:
                        dotf_file = dotf.split(" ")[-1]
                        parsed_file_md5 = calculate_md5(dotf_file)
                        
                        if ( (reference_side if ref else implemented_side) in dotf_file ):
                            path_after_side = dotf_file.split((reference_side if ref else implemented_side))[-1]
                            mid_path = os.path.join(extr_dir,(reference_side if ref else implemented_side))
                            new_path = os.path.join(mid_path,path_after_side.rsplit('/',1)[0].lstrip('/'))
                        else:
                            mid_path = os.path.join(extr_dir,"src_backup","rtl")
                            new_path = mid_path+(dotf_file.rsplit('/',1)[0])

                        os.makedirs(new_path,exist_ok = True,mode=0o777)
                        new_dest_path = os.path.join(new_path,os.path.basename(dotf_file))
                        shutil.copyfile(dotf_file, new_dest_path,follow_symlinks=True)
                        dotf_entries[new_dest_path] = [dotf_file, parsed_file_md5]
                        rtl_files +=1


                    
                done_reading = re.search(r"\s*(INFO|INTEL_INFO)\s*:\s*Setup\s*",line,re.I)
                if(done_reading):
                    ref = False;impl = False;rtl_mode =False;gate_mode = False;design=False;upf = False;td_files = False; child = False

                #done copying impl and ref files
                td_constraints = re.search(r"Applying\s*TD\s*constraints.*",line,re.I)
                if(td_constraints):
                    td_files = True

                dop_mapping = re.search(r"(INTEL_INFO|INFO)\s*:\s*add_fm_clk_dop_mapping\s*procedure.*",line,re.I)
                if(dop_mapping):
                    td_files = True

                reset = re.search(r"\s*(INFO|INTEL_INFO)\s*:\s*STEP\s*DONE\s*:\s*(match|verify)",line,re.I)
                if(reset):
                    td_files = False

                #copies all the "Script start" stuff
                script_start = re.match (r"(INTEL_INFO|INFO)\s*:\s*SCRIPT_START\s*:\s*(.*)\s*(\({1}|\[{1})",line,re.I)
                if(script_start):
                    script_file = script_start.group(2).split(" ")[0]
                    #print (f'{script_file}')
                    
                    #matches for *hookfiles* tag in namefile
                    name_match = re.search(r"(fev|user)_fm_.*",script_file.rsplit("/",1)[-1],re.I)
                    if(name_match):
                        print(f"{bcolors.OKGREEN}copied{bcolors.ENDC} {script_file.split('/')[-1]}", flush=True)
                        shutil.copyfile(script_file, os.path.join(extr_dir,"scripts",task,os.path.basename(script_file)),follow_symlinks=True)
                    
                    #rtl 2stagelist copier - the list file
                    if(rtl_mode and not gate_mode and design):
                        side_dir = os.path.join(extr_dir,(implemented_side if impl else reference_side))

                        if (not os.path.exists(side_dir)) :
                            os.makedirs(side_dir,exist_ok = True,mode=0o777)

                        shutil.copyfile(script_file,os.path.join(side_dir,os.path.basename(script_file)),follow_symlinks=True)
                        rtl_list_path_modifier(os.path.join(side_dir, os.path.basename(script_file)))#this creates and modify the copied file
                        print(f"{bcolors.OKGREEN}copied{bcolors.ENDC} {script_file.split('/')[-1]}", flush=True)
                        design_files +=1
                    
                    if(td_files):
                        td_dir = os.path.join(extr_dir,"td_collateral","icc2")
                        if (not os.path.exists(td_dir)) :
                            os.makedirs(td_dir,exist_ok = True,mode=0o777)
                        shutil.copyfile(script_file, os.path.join(td_dir,os.path.basename(script_file)),follow_symlinks=True)
                        print(f"{bcolors.OKGREEN}copied{bcolors.ENDC} {script_file.split('/')[-1]}", flush=True)
                        design_files +=1

                    vars_detect = re.search(r"/scripts/vars.tcl",script_file,re.I)
                    if(vars_detect):
                        os.makedirs(extr_dir,exist_ok = True,mode=0o777)
                        shutil.copyfile(script_file, os.path.join(extr_dir,"scripts",os.path.basename(script_file)),follow_symlinks=True)
                    
                    hips_detect = re.search(r"hip_ivars.tcl",script_file,re.I)
                    if(hips_detect):
                        shutil.copytree(script_file.rsplit('/',1)[0], os.path.join(extr_dir,"hip_data"),symlinks=False,dirs_exist_ok=True)
                        #os.system(f"cp -rf {script_file.rsplit('/',1)[0]} {os.path.join(extr_dir)} ")
                        print(f"{bcolors.OKGREEN}copied{bcolors.ENDC} {script_file.split('/')[-1]}", flush=True)


            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(f"{bcolors.FAIL}Exception Encountered:{bcolors.ENDC} {e}", flush=True)
                print(f"{bcolors.FAIL}{exc_type}, {fname}, {exc_tb.tb_lineno}{bcolors.ENDC}", flush=True)
                print (f"{bcolors.FAIL}line no:{bcolors.ENDC} {count}\n{bcolors.FAIL}line:{bcolors.ENDC} {line}\n")
                if debug:
                    with open("error.log", "a+") as error_log:
                        error_log.write(f"{exc_type, fname, exc_tb.tb_lineno}\n")
                        error_log.write(f"line no: {count}\nline: {line}\n")
                    print(e)
                errorVar = True
                pass         

        vars_creator(extr_dir)
        id_creator(dest_path,block_name, tech, task, reference_side, implemented_side)
        # write out rtl set
        dotf_processor(dotf_entries, rtl_entries,extr_dir)       
        if (debug):
            print("Writing pkl files for dotf and rtlfiles")
            with open( os.path.join(extr_dir,"rtl_data.pkl"), 'wb') as f:
                pickle.dump(rtl_entries, f)
            with open( os.path.join(extr_dir,"dotf_data.pkl"), 'wb') as f:
                pickle.dump(dotf_entries, f)

    done = True


if __name__ == "__main__":

    # Check the major and minor version of Python
    if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 8):
        # Display a message and exit with an error code
        print("This script requires Python 3.8 or higher.")
        sys.exit(1)

# rest of the script
    # initialises the graceful exitting feature
    flag = GracefulExiter()
    # this clears the console beofore start
    os.system('cls' if os.name == 'nt' else 'clear')
    time_start = time.perf_counter()
    t = threading.Thread(target=animate)
    t.start()

    # initiliases the parser-argument reader tool
    parser = argparse.ArgumentParser(prog='pandora_extractor', description='A wrapper to automate Pandora testcase extraction')
    parser.add_argument('-l', '--log', required=True, type=file_path, help='Path lo log file')
    parser.add_argument('-d', '--dest', required=True,type=dir_path, help='Destination path')
    parser.add_argument('-f', required=False,action='store_true', help='.f based')
    parser.add_argument('-g', '--golden', required=True,help='golden folder name')
    parser.add_argument('-r', '--revised', required=True,help='revised folder name')
    parser.add_argument('--verbose',action='store_true', required=False,default=False,help='revised folder name')

    args = parser.parse_args()
    # print(args)
    log_path = str(Path(os.path.abspath(args.log)).resolve())
    dest_path = str(Path(os.path.abspath(args.dest)).resolve())
    dotf_mode = args.f
    reference_side = args.golden
    implemented_side = args.revised
    debug = args.verbose

    print (f"default values {log_path} {dest_path} {reference_side} {implemented_side} {dotf_mode} {debug}")

    # Init verbose
    print(f"{bcolors.OKCYAN}Given log Path:{bcolors.ENDC} {log_path}", flush=True)
    print(f"{bcolors.OKCYAN}Given Destination Path:{bcolors.ENDC} {dest_path}\n", flush=True)

    # Start actual procerssing
    main_fm()
    

    

    # final stats printing
    print(f"{bcolors.BOLD}{bcolors.OKGREEN}Extraction Completed.{bcolors.ENDC}", flush=True)
    print(f"{bcolors.BOLD}{bcolors.OKCYAN}Starting Post Porcessing{bcolors.ENDC}", flush=True)

    if (not errorVar):
        print(f"{bcolors.OKGREEN}Extraction Completed with no Errors.{bcolors.ENDC}\n", flush=True)
    else:
        print(f"{bcolors.FAIL}Extraction Detected errors, fix them and Re-launch.{bcolors.ENDC}\n", flush=True)

    # this causes the graceful exit
    time_elapsed = (time.perf_counter() - time_start)
    memMb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0
    print(f"{bcolors.OKBLUE}Total time elapsed: {time_elapsed:5.1f} secs\nTotal memory used: {memMb:5.1f} MByte{bcolors.ENDC}", flush=True)

    if flag.exit():
        print(f"{bcolors.FAIL}ctrl+c eceived again.Exitting{bcolors.ENDC}", flush=True)
        exit(1)

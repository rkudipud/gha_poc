#!/usr/intel/bin/python3.10.8


# -*- coding: utf-8 -*-
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
script_path_regex = re.compile(r"Script:\s*(.*)/runs/(.*)", flags=re.I)
script_start_regex = re.compile(r"INTEL_INFO\s*:\s*SCRIPT_START\s*:\s*(\S*)\s*", flags=re.I)
tool_regex = re.compile(r"Script:\s*(.*)/runs/(.*)", flags=re.I)
version_regex = re.compile(r'\s+Version\s+(\S+)\s+', flags=re.I)
build_dir_cfm = re.compile(r"INTEL_INFO\s+:\s+Initializing\s+::ivar\(build_dir\)\s+=\s+'(\S+)'\s+\[.*\]", flags=re.I)
task_cfm = re.compile(r"INTEL_INFO\s+:\s+Initializing\s+::ivar\(task\)\s+=\s+'(\S+)'\s+\[.*\]", flags=re.I)
parsing_file_regex_cfm = re.compile(r"\/\/\s*Parsing file\s*(\S+)\s*...(\(md5sum:(\S*)\))?", flags=re.I)
filepath = re.compile(r"(\$\S+|/\S+)", flags=re.I)

class GracefulExiter:
    def __init__(self):
        self.state = False
        signal.signal(signal.SIGINT, self.change_state)

    def change_state(self, signum, frame):
        print(f"{bcolors.WARNING}ctrl+c Received, press again to exit{bcolors.ENDC}", flush=True)
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
    abs_path = os.path.abspath(string)
    if os.path.isfile(abs_path):
        return string
    else:
        raise FileNotFoundError(abs_path)

# Dir_path checker


def dir_path(string):
    abs_path = os.path.abspath(string)
    if os.path.isdir(abs_path):
        return string
    else:
        raise NotADirectoryError(string)

# Identical file checker


def are_files_identical(file1, file2):
    return filecmp.cmp(file1, file2, shallow=True)

# calculate md5 of a file


def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    if (os.path.exists(file_path)):
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
def id_creator(dest_path, block_name, tech, task, reference_folder, implementation_folder):
    id_file_path = os.path.join(dest_path, block_name, "id.csh")
    if (os.path.exists(id_file_path)):
        with open(id_file_path, 'r') as file:
            content = file.readlines()
        for line in content:
            if 'fub_collaterals' in line:
                # print(f'Fub Collaterals already exists with : {content.index(line)}', flush=True)
                matches = re.search(r"\(.*\)", line, re.IGNORECASE | re.VERBOSE)
                if (reference_folder not in matches.group()):
                    # print (f"not, {content[content.index(line)]}", flush=True)
                    content[content.index(line)] = content[content.index(line)].replace(")", f"{reference_folder} )")
                if (implementation_folder not in matches.group()):
                    # print (f"not, {content[content.index(line)]}", flush=True)
                    content[content.index(line)] = content[content.index(line)].replace(")", f"{implementation_folder} )")
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
set fub_collaterals = \"( {reference_folder} {implementation_folder} )\"
set fub_tasks = \"( {task} )\"
set fub_techs = \"( {tech} )\"
#nb_mode:64G_4C

        """.format(block_name=block_name, reference_folder=reference_folder, implementation_folder=implementation_folder, task=task, tech=tech)
        with open(id_file_path, 'w') as file:
            file.writelines(data)
    print(f"{bcolors.OKCYAN}---> ID file Created{bcolors.ENDC}", flush=True)


# Creates vars.tcl file
def vars_creator(dest_path, block_name):
    vars_file_path = os.path.join(dest_path, block_name, "scripts", "vars.tcl")
    data = """
#HIP Settings
if { [file exists $env(ward)/runs/$env(block)/$env(tech)/hip_data/hip_ivars.tcl] } { 

    source $env(ward)/runs/$env(block)/$env(tech)/hip_data/hip_ivars.tcl
    set hip_scenario [lindex $ivar(setup,hip_oc_types_list) 0]

} else {
    set ivar(setup,hip_lib_types_list) ""
    set hips_copied [glob -nocomplain -path $ward/src_backup/library/hip/ *.lib* ]

    set all_hips ""
    foreach individual_path $hips_copied {
        regexp {([^\/]+$)} $individual_path hip_name 	
    lappend all_hips $hip_name
    }

    set ivar(setup,hip_lib_types_list) $all_hips
    set hip_scenario "TT_100"
}

foreach hipLib $ivar(setup,hip_lib_types_list) { 
        set ivar(lib,$hipLib,use_ccs) 0
    set ivar(lib,$hipLib,lib_nldm_filelist,$hip_scenario) [glob -nocomplain -path $ward/src_backup/library/hip/ *$hipLib* ] 
}


#library setup
set libs_copied [glob -nocomplain -path $ward/src_backup/library/liberty/ *.lib* ]
set lib_scenario [ lindex $ivar(setup,oc_types_list) 0 ]

set all_libs ""
foreach individual_path $libs_copied {
        regexp {([^\/]+$)} $individual_path libname 	
    lappend all_libs $libname
}

set ivar(link_libs) $all_libs
foreach linkLib $ivar(link_libs) {
    set ivar(lib,$linkLib,use_ccs) 1
    set ivar(lib,$linkLib,lib_ccs_filelist,$lib_scenario) [glob -nocomplain -path $ward/src_backup/library/liberty/ *$linkLib* ]

}

#verilog libs
set ivar(target_libs) ""
set all_verilogs ""

set verilogs_copied [glob -nocomplain -path $ward/src_backup/library/verilog/ *.v* ]

foreach individual_verilog $verilogs_copied {
        regexp {([^\/]+$)} $individual_verilog verilogname 	
    lappend all_verilogs $verilogname
}

set ivar(target_libs) $all_verilogs 
foreach verilog $ivar(target_libs) {
    set ivar(lib,$verilog,verilog_default_filelist) [glob -nocomplain -path $ward/src_backup/library/verilog/ *$verilog* ] 
}
    """
    if (os.path.exists(vars_file_path)):
        shutil.copyfile(vars_file_path, os.path.join(dest_path, block_name, "scripts", "vars.tcl_orig"))
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

def dotf_processor(dotf_entries, rtl_entries,dest_path,block):
    # reads the rtl_data set ( orig_path, copied_path, md5)
    # reads the dotf files set( copied_path, orig_path, md5)
    
    for dotf_file in dotf_entries.keys():
        #print(dotf_files)
        with open(dotf_file, 'r') as dot_f_file:
            for Line in dot_f_file:
                line = Line.strip()
                if filepath.match(line):
                    matched_path = filepath.match(line).group(1).strip()
                    if ( re.match(r"^(/p|/nfs)",matched_path, re.I) ):
                        #print(matched_path)
                        if(matched_path in rtl_entries.keys()):
                            #print("Path present in rtl_data", rtl_entries[matched_path])
                            copied_path = (rtl_entries[matched_path][0].split(os.path.join(dest_path,block))[-1])
                            mod_path = (f"$ward{copied_path}")
                            #print(mod_path)
                            os.system(f"sed -i 's#{matched_path}#{mod_path}#' {os.path.join(dotf_file)}")
        print(f"{bcolors.OKCYAN}---> Processed dotf files{bcolors.ENDC}", flush=True)


############################################## function Main ############################################
def main_cfm():

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
    block_name = ""
    tech = ""
    ward = ""
    flow = ""
    task = ""
    log_name = ""
    build_dir = ""

    # predefined variables
    # initial states
    libs = False
    verilog_libs = False
    hips = False



    gol = False
    rev = False
    pre_eco = False
    post_eco = False
    rtl_mode = False
    gate_mode = False
    dotf_mode = False
    design = False
    upf = False
    td_files = False
    child = False

    # stats
    count = 0
    rtl_files = 0
    design_files = 0
    verilog_lib_files = 0
    lib_files = 0
    upf_files = 0

    with open(log_path, 'r') as source_log:
        for line in source_log:
            count += 1
            try:
                if version_regex.match(line):
                    cfm_version = version_regex.match(line).group(1)
                    print(
                        f"{bcolors.OKBLUE}Conformal version:{bcolors.ENDC} {cfm_version}", flush=True)
                if build_dir_cfm.match(line):
                    build_dir = build_dir_cfm.match(line).group(1)
                    print(
                        f"{bcolors.OKBLUE}Build Dir:{bcolors.ENDC} {build_dir}", flush=True)
                if task_cfm.match(line):
                    task = task_cfm.match(line).group(1)
                    print(f"{bcolors.OKBLUE}Task:{bcolors.ENDC} {task}", flush=True)

                    try:
                        # now create testcase location
                        build_dir = build_dir.rsplit("runs",1)
                        ward = build_dir[0]
                        block_name = build_dir[1].split("/")[1]
                        tech = build_dir[1].split("/")[2]
                        flow = "fev_conformal"
                        task = task
                        log_name = log_path.rsplit('/', 1)[-1]

                        print(f"{bcolors.OKBLUE}Ward Path:{bcolors.ENDC} {ward}", flush=True)
                        print(f"{bcolors.OKBLUE}Block_Name:{bcolors.ENDC} {block_name}", flush=True)
                        print(f"{bcolors.OKBLUE}Block_Tech:{bcolors.ENDC} {tech}", flush=True)
                        print(f"{bcolors.OKBLUE}Block_Flow:{bcolors.ENDC} {flow}", flush=True)
                        print(f"{bcolors.OKBLUE}Block_Task:{bcolors.ENDC} {task}", flush=True)
                        print(f"{bcolors.OKBLUE}Block_Log:{bcolors.ENDC} {log_name}\n", flush=True)

                        print(f"{bcolors.BOLD}Creating Extracted Dirs{bcolors.ENDC}", flush=True)
                        if (os.path.exists(dest_path)):
                            os.makedirs(os.path.join(dest_path, block_name), exist_ok=True, mode=0o777)
                            os.makedirs(os.path.join(dest_path, block_name, "scripts"), exist_ok=True, mode=0o777)
                            os.makedirs(os.path.join(dest_path, block_name, "scripts", task), exist_ok=True, mode=0o777)
                            if os.path.exists(os.path.join(dest_path, block_name, task+".orig.log")):
                                if checksum(os.path.join(dest_path, block_name, task+".orig.log"), log_path):
                                    print(f"{bcolors.WARNING}-->same log file present in Testcase{bcolors.ENDC}\n", flush=True)
                            else:
                                shutil.copyfile(log_path, os.path.join(dest_path, block_name, task+".orig.log"))
                    except OSError as error:
                        print(f"{bcolors.WARNING}Error in creating directory :{bcolors.ENDC}\n" + str(error), flush=True)
                        errorVar = True
                        sys.exit(1)


                #read standard cell libs
                if (re.match(r"// Command: read_stdcell_libs", line, flags=re.I)):
                    print(f"{bcolors.OKBLUE}Working on Liberty files{bcolors.ENDC}", flush=True)
                    libs = True
                    hips = False
                    verilog_libs = False

                # verilog library files
                if (re.match(r"(INTEL_INFO|INFO)\s*:\s*Use STD_CELL_VERILOG libraries:", line, flags=re.I)):
                    print(f"{bcolors.OKBLUE}Working on Liberty Verilog files{bcolors.ENDC}", flush=True)
                    libs = False
                    hips = False
                    verilog_libs = True

                # verilog library files close
                if (re.match(r"// Note: Read VERILOG library successfully", line, flags=re.I)):
                    print(f"{bcolors.OKBLUE}Read verilog lib done{bcolors.ENDC}", flush=True)
                    libs = False
                    hips = False
                    verilog_libs = False
                    
                # read hips mode
                if (re.match(r"// Command: read_hips ", line, flags=re.I)):
                    print(f"{bcolors.OKBLUE}Working on HIP files{bcolors.ENDC}", flush=True)
                    libs = False
                    hips = True
                    verilog_libs = False

                # closes library section
                if (re.match(r"// Note: Read Liberty library successfully", line, flags=re.I)):
                    print(f"{bcolors.OKBLUE}Read liberty lib done{bcolors.ENDC}", flush=True)
                    libs = False
                    hips = False
                    verilog_libs = False

                # sets to read_golden_design
                if (re.search(r"(INTEL_INFO|INFO)\s*:\s*Reading Golden Design", line, re.I)):
                    print(f"{bcolors.OKBLUE}Working on Golden Design{bcolors.ENDC}", flush=True)
                    gol = True
                    rev = False
                    design = True

                # sets to read_revised_design
                if (re.search(r"(INTEL_INFO|INFO)\s*:\s*Reading Revised Design", line, re.I)):
                    print(f"{bcolors.OKBLUE}Working on Revised Design{bcolors.ENDC}", flush=True)
                    gol = False
                    rev = True
                    design = True

                # sets to read_rtl_dotf mode
                if (re.search(r"(INTEL_INFO|INFO)\s*:\s*read_rtl_dotf procedure is invoked", line, re.I)):
                    print(f"{bcolors.OKBLUE}Working on rtl dot F Design{bcolors.ENDC}", flush=True)
                    dotf_mode = True
                    rtl_mode = True
                    gate_mode = False

                # set to read_rtl2stage mode
                if (re.search(r"(INTEL_INFO|INFO)\s*:\s*read_rtl_2stage procedure is invoked", line, re.I)):
                    print(f"{bcolors.OKBLUE}Working on rtl_2stage Design{bcolors.ENDC}", flush=True)
                    dotf_mode = False
                    rtl_mode = True
                    gate_mode = False
                
                # sets to read_gate_mode
                if (re.search(r"(INTEL_INFO|INFO)\s*:\s*read_gate procedure is invoked", line, re.I)):
                    print(f"{bcolors.OKBLUE}Working on read_gate Design{bcolors.ENDC}", flush=True)
                    dotf_mode = False
                    rtl_mode = False
                    gate_mode = True

                # sets UPF revised
                if (re.search(r"// Command: set exit code -clear", line, re.I)):
                    print(f"{bcolors.OKBLUE}Working on UPF - Revised{bcolors.ENDC}", flush=True)
                    gol = False
                    rev = True
                    design = False
                    upf = True

                # sets to read PRE_ECO_netlist
                if (re.search(r"(INTEL_INFO|INFO)\s*:\s*Reading PRE ECO Netlist", line, re.I)):
                    print(f"{bcolors.OKBLUE}Working on Golden Design{bcolors.ENDC}", flush=True)
                    gol = True
                    rev = False
                    design = True

                # sets to read POST_ECO_netlist
                if (re.search(r"(INTEL_INFO|INFO)\s*:\s*Reading POST ECO Design", line, re.I)):
                    print(f"{bcolors.OKBLUE}Working on Revised Design{bcolors.ENDC}", flush=True)
                    gol = False
                    rev = True
                    design = True


                # sets UPF golden
                if (re.search(r"(INTEL_INFO|INFO)\s*:\s*Reading UPF", line, re.I)):
                    print(f"{bcolors.OKBLUE}Working on UPF - Golden{bcolors.ENDC}", flush=True)
                    rtl_mode =False
                    gate_mode = False
                    dotf_mode = False
                    design = False
                    gol = True
                    rev = False
                    upf = True
                    child = False


                # sets to - Child detector netlist
                if (re.search(r"(INTEL_INFO|INFO)\s*:\s*Reading child netlists", line, re.I)):
                    print(f"{bcolors.OKBLUE}Working on Child netlist {bcolors.ENDC}", flush=True)
                    child = True


                # sets to disable TD_file _copier
                if ( re.search(r"fev.tcl doesnt exist in the path specified", line, re.I) ) :
                    gol = False
                    rev = False
                    eco = False
                    upf = False
                    design = False
                    gate_mode = False
                    rtl_mode = False
                    child = False
                    dotf_mode = False
                    print(f"{bcolors.OKBLUE}TD collaterals dosent exists {bcolors.ENDC}", flush=True)
                    td_files = False
                    

                # sets to Enable TD_file _copier
                if ( re.search(r"(INTEL_INFO|INFO)\s*:\s*script_start\s*:\s*\S*\/td_collateral\/\S*", line,re.I) ) :
                    print(f"{bcolors.OKBLUE}TD collaterals exists {bcolors.ENDC}", flush=True)
                    td_files = True

                # discovers and copies to process cadence contruction
                if (re.search(r"Command: read implementation information\s*(\S*)\s*", line, re.I)):
                    print(f"{bcolors.OKBLUE}Found cadence construction information {bcolors.ENDC}", flush=True)
                    # New path input with multiple occurrences of "genus"
                    new_path = re.search(r"Command: read implementation information\s*(\S*)\s*", line, re.I).group(1)
                    # Split the new path into its components
                    new_path_components = new_path.split('/')
                    # Find the index of the last component that contains the word "genus"
                    last_genus_index = next((len(new_path_components) - i - 1 for i, component in enumerate(reversed(new_path_components)) if "genus" in component), None)

                    # Extract the path up to and including the last "genus" component
                    extracted_path_components = new_path_components[:last_genus_index + 1] if last_genus_index is not None else []

                    # Join the components back into a path
                    extracted_new_path =  os.path.join("/",*extracted_path_components)
                    file_dest_path = os.path.join(dest_path,block_name,extracted_new_path.split('/')[-1])
                    os.makedirs(file_dest_path, exist_ok=True, mode=0o777)
                    shutil.copytree(extracted_new_path, file_dest_path, symlinks=True, dirs_exist_ok = True)
                    print(f"{bcolors.OKBLUE}Copied cadence construction information {bcolors.ENDC}", flush=True)
                    
                # discovers and copies to process ALIAS construnction
                if (re.search(r"Command: add name alias\s*(\S*)\s*", line, re.I)):
                    # New path input with multiple occurrences of "genus"
                    map_path = re.search(r"Command: add name alias\s*(\S*)\s*", line).group(1)
                    map_tc_path = os.path.join(dest_path, block_name, "src_backup")
                    if (not os.path.exists(map_tc_path)):
                        os.makedirs(map_tc_path, exist_ok=True, mode=0o777)
                    shutil.copyfile(map_path.strip(), os.path.join(map_tc_path, os.path.basename(map_path.strip())), follow_symlinks=True)
                    print(f"{bcolors.OKBLUE}Copied Alias file  - backup{bcolors.ENDC}", flush=True)
                    

                # discovers and copies to process Guidance VSDC construnction
                if (re.search(r"Command: system cfm_env python3\s*\S*\s*(\S*)\s*", line, re.I)):
                    # New path input with multiple occurrences of "genus"
                    vsdc_path = re.search(r"Command: system cfm_env python3\s*\S*\s*(\S*)\s*", line, re.I).group(1)
                    vsdc_tc_path = os.path.join(dest_path, block_name, (revised_side if rev else golden_side) )
                    if (not os.path.exists(vsdc_tc_path)):
                        os.makedirs(vsdc_tc_path, exist_ok=True, mode=0o777)
                    shutil.copyfile(vsdc_path.strip(), os.path.join(vsdc_tc_path, os.path.basename(vsdc_path.strip())), follow_symlinks=True)
                    print(f"{bcolors.OKBLUE}Copied VSDC file {bcolors.ENDC}", flush=True)


                # discovers and copies to process lcp scandef file
                if (re.search(r"Reading\s*(\/.*scan\.def)", line, re.I)):
                    print(f"{bcolors.OKBLUE}Found LCP scan chain {bcolors.ENDC}", flush=True)
                    # New path input with multiple occurrences of "genus"
                    new_path = re.search(r"Reading\s*(\/.*scan\.def)", line, re.I).group(1)
                    file_dest_path = os.path.join(dest_path,block_name,new_path.rsplit('/')[-2])
                    os.makedirs(file_dest_path, exist_ok=True, mode=0o777)
                    shutil.copyfile(new_path.strip(), os.path.join(file_dest_path, os.path.basename(new_path.strip())), follow_symlinks=True)
                    print(f"{bcolors.OKBLUE}Copied LCP scanchain def information {bcolors.ENDC}", flush=True)


                # discovers and copies the dot .f verilog comand files
                if (re.search(r"Note:\s*Process verilog command file\s*(\S+)\s*", line, re.I)):
                    print(f"{bcolors.OKBLUE}Found .f File {bcolors.ENDC}", flush=True)
                    file_path_f = re.search(r"\s*Process verilog command file\s*(\S+)\s*", line, re.I).group(1)

                    if ( (golden_side if gol else revised_side) in file_path_f):
                        path_after_side = file_path_f.split((golden_side if gol else revised_side))[-1]
                        mid_path = os.path.join(dest_path,block_name,(golden_side if gol else revised_side))
                        new_path = os.path.join(mid_path,path_after_side.rsplit('/',1)[0].lstrip('/'))
                    else:
                        new_path = os.path.join(dest_path,block_name,"src_backup","rtl",file_path_f.rsplit('/',1)[0].lstrip('/'))

                    os.makedirs(new_path, exist_ok=True, mode=0o777)
                    new_dest_path = os.path.join(new_path, os.path.basename(file_path_f.strip()))
                    shutil.copyfile(file_path_f.strip(), new_dest_path, follow_symlinks=True)
                    dotf_entries[new_dest_path] = [file_path_f, parsed_file_md5]
                    print(f"{bcolors.OKBLUE}Copied .f file {os.path.basename(file_path_f.strip())} {bcolors.ENDC}", flush=True)
                



                # Major processes
                if (parsing_file_regex_cfm.match(line)):
                    parsed_file = parsing_file_regex_cfm.match(line).group(1)
                    parsed_file_md5 = parsing_file_regex_cfm.match(line).group(3)
                    
                    # A failsafe to pickup patch files from eco based runs
                    if ( "patch.v" in parsed_file ):
                        pass

                    actual_md5 = calculate_md5(parsed_file)
                    
                    
                    if debug:
                        print( f"{parsed_file} and md5 is:{parsed_file_md5} processed md5 is {actual_md5}")
                    if (parsed_file_md5 == actual_md5):
                        if debug:
                            print(f"{bcolors.OKGREEN}Matched{bcolors.ENDC}", flush=True)
                    else:
                        if debug:
                            print(f"{bcolors.FAIL}Not matched {bcolors.ENDC}: {parsed_file}", flush=True)

                    # copies libs
                    if (libs and not verilog_libs and not hips):
                        liberty_path = os.path.join(dest_path, block_name, "src_backup", "library", "liberty")
                        if (not os.path.exists(liberty_path)):
                            os.makedirs(liberty_path, exist_ok=True, mode=0o777)
                        shutil.copyfile(parsed_file.strip(), os.path.join(liberty_path, os.path.basename(parsed_file.strip())), follow_symlinks=True)
                        if debug:
                            print (f"copied lib file: {os.path.basename(parsed_file.strip())}")
                        lib_files += 1
                        
                    #copies standard cell verilog hips    
                    if (not libs and verilog_libs and not hips):
                        verilog_lib_path = os.path.join(dest_path, block_name, "src_backup", "library", "verilog")
                        if (not os.path.exists(verilog_lib_path)):
                            os.makedirs(verilog_lib_path,exist_ok=True, mode=0o777)
                        shutil.copyfile(parsed_file.strip(), os.path.join(verilog_lib_path, os.path.basename(parsed_file.strip())), follow_symlinks=True)
                        if debug:
                            print (f"copied verilog file: {os.path.basename(parsed_file.strip())}")
                        verilog_lib_files += 1
                
                    #copies hips
                    if (hips and not libs and not verilog_libs):
                        hip_path = os.path.join(dest_path, block_name, "src_backup", "library", "hip")
                        if (not os.path.exists(hip_path)):
                            os.makedirs(hip_path, exist_ok=True, mode=0o777)
                        shutil.copyfile(parsed_file.strip(), os.path.join(hip_path, os.path.basename(parsed_file.strip())), follow_symlinks=True)
                        if debug:
                            print (f"copied libs file: {os.path.basename(parsed_file.strip())}")
                        verilog_lib_files += 1

                    #coies rtl fiels from rtl_list_2stage_proc
                    if (design and rtl_mode and not gate_mode and not upf):
                        #creating src_backup/rtl
                        if (not os.path.exists(os.path.join(dest_path,block_name,"src_backup","rtl"))) :
                            os.makedirs(os.path.join(dest_path,block_name,"src_backup","rtl"),exist_ok = True,mode=0o777)

                        if ( (golden_side if gol else revised_side) in parsed_file):
                            path_to_file = parsed_file.split((golden_side if gol else revised_side))[-1]
                            mid_path = os.path.join(dest_path,block_name)
                            new_path = os.path.join(mid_path,(golden_side if gol else revised_side),path_to_file.rsplit('/',1)[0].lstrip('/'))
                        else:
                            new_path = os.path.join(dest_path,block_name,"src_backup","rtl",parsed_file.rsplit('/',1)[0].lstrip('/'))

                        os.makedirs(new_path,exist_ok = True,mode=0o777)
                        final_path = os.path.join(new_path,os.path.basename(parsed_file))
                        shutil.copyfile(parsed_file, final_path,follow_symlinks=True)
                        rtl_entries[parsed_file] = [final_path, actual_md5]

                        if debug:
                            print (f"copied Design file: {os.path.basename(parsed_file.strip())}")
                        rtl_files +=1



                    #coies gate netlist for top and child modules
                    if (design and not rtl_mode and gate_mode and not upf):
                        #creating src_backup/rtl
                        child_regx_er = ""
                        design_dest_path = ""
                        if ( child ):
                            child_file_ward = parsed_file.replace(ward, "").strip()
                            child_regx_er = re.match(r"(.+\/)*(.+)\/(\S*)\.(\S*)$",child_file_ward,flags=re.I)
                            design_dest_path = os.path.join(dest_path,block_name, (golden_side if not rev else revised_side ), "child_modules",child_regx_er.group(2))

                        else:
                            design_dest_path = os.path.join(dest_path,block_name,( golden_side if not rev else revised_side ))

                        if (not os.path.exists(design_dest_path)) :
                            os.makedirs(design_dest_path,exist_ok = True,mode=0o777)
                        # copy the design file
                        if ( child ):
                            shutil.copytree(parsed_file.rsplit("/",1)[0], design_dest_path, symlinks=True, dirs_exist_ok = True)
                            if debug:
                                if debug:
                                    print (f"copied Child Design Data: {child_regx_er.group(3)}")
                        else :
                            shutil.copyfile(parsed_file, os.path.join(design_dest_path,os.path.basename(parsed_file)),follow_symlinks=True)
                            if debug:
                                if debug:
                                    print (f"copied Design file: {os.path.basename(parsed_file.strip())}")
                        design_files  +=1

                    #coies UPF Files
                    if (not design and not rtl_mode and not gate_mode and upf):
                        if ( "loader" in parsed_file ) :
                            child = True
                            continue
                        else :
                            if ( child ):
                                child_file_ward = parsed_file.replace(ward, "").strip()
                                child_regx_er = re.match(r"(.+\/)*(.+)\/(\S*)\.(\S*)$",child_file_ward,flags=re.I)
                                upf_dest_path  = os.path.join( dest_path,block_name, (golden_side if gol else revised_side ), "child_modules",child_regx_er.group(2) )
                            else :
                                upf_dest_path = os.path.join( dest_path,block_name, (golden_side if gol else revised_side ) )

                            if (not os.path.exists(upf_dest_path)) :
                                os.makedirs(upf_dest_path,exist_ok = True,mode=0o777)
                            
                            shutil.copyfile(parsed_file, os.path.join(upf_dest_path,os.path.basename(parsed_file)),follow_symlinks=True)
                            if debug:
                                print (f"copied UPF file: {os.path.basename(parsed_file.strip())}")


                # copies all the "Script start" stuff
                if script_start_regex.match(line):
                    script_file = script_start_regex.match(line).group(1)
                    # print (f'{script_file}')

                    # matches for *hookfiles* tag in namefile
                    name_match = re.search(r"(fev|user)_.*", script_file.rsplit("/", 1)[-1], re.I)
                    if (name_match):
                        print(f"{bcolors.OKGREEN}copied{bcolors.ENDC} {script_file.split('/')[-1]}", flush=True)
                        shutil.copyfile(script_file, os.path.join(dest_path, block_name, "scripts", task, os.path.basename(script_file)), follow_symlinks=True)
                    
                    # rtl design files copier - the list file
                    if (rtl_mode and not gate_mode and design):
                        print(f"{bcolors.OKGREEN}copied{bcolors.ENDC} {script_file.split('/')[-1]}", flush=True)
                        if (not gol and rev):
                            side_dir = os.path.join(dest_path, block_name, revised_side)
                        elif (gol and not rev):
                            side_dir = os.path.join(dest_path, block_name, golden_side)

                        if (not os.path.exists(side_dir)):
                            os.makedirs(side_dir, exist_ok=True, mode=0o777)

                        shutil.copyfile(script_file, os.path.join(side_dir, os.path.basename(script_file)), follow_symlinks=True)
                        #this creates and modify the copied file
                        rtl_list_path_modifier(os.path.join(side_dir, os.path.basename(script_file)))
                        #print(f"Please enable rtl modifier here", flush=True)
                        design_files += 1
                    

                    if (td_files):
                        td_dir = os.path.join(dest_path, block_name, "td_collateral", "icc2")
                        if (not os.path.exists(td_dir)):
                            os.makedirs(td_dir, exist_ok=True, mode=0o777)
                        shutil.copyfile(script_file, os.path.join(td_dir, os.path.basename(script_file)), follow_symlinks=True)
                        print(f"{bcolors.OKGREEN}copied{bcolors.ENDC} {script_file.split('/')[-1]}", flush=True)
                        td_files = False
                        design_files += 1

                    vars_detect = re.search(r"/scripts/vars.tcl", script_file, re.I)
                    if (vars_detect):
                        shutil.copyfile(script_file, os.path.join(dest_path, block_name, "scripts", os.path.basename(script_file)), follow_symlinks=True)
                        print(f"{bcolors.OKGREEN}copied{bcolors.ENDC} {script_file.split('/')[-1]}", flush=True)

                    hips_detect = re.search(r"hip_ivars.tcl", script_file, re.I)
                    if (hips_detect):
                        shutil.copytree(script_file.rsplit('/',1)[0], os.path.join(dest_path,block_name,"hip_data"),symlinks=False,dirs_exist_ok=True)
                        #os.system(f"cp -rf {script_file.rsplit('/',1)[0]} {os.path.join(dest_path,block_name)} ")
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

        vars_creator(dest_path,block_name)
        id_creator(dest_path, block_name, tech, task, golden_side, revised_side)
        # write out rtl set
        dotf_processor(dotf_entries, rtl_entries,dest_path,block_name)
        if (debug):
            print("Writing pkl files for dotf and rtlfiles")
            with open( os.path.join(dest_path,block_name,"rtl_data.pkl"), 'wb') as f:
                pickle.dump(rtl_entries, f)
            with open( os.path.join(dest_path,block_name,"dotf_data.pkl"), 'wb') as f:
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
    golden_side = args.golden
    revised_side = args.revised
    debug = args.verbose

    #print (f"default values {log_path} {dest_path} {golden_side} {revised_side} {dotf_mode} {debug}")

    # Init verbose
    print(f"{bcolors.OKCYAN}Given log Path:{bcolors.ENDC} {log_path}", flush=True)
    print(f"{bcolors.OKCYAN}Given Destination Path:{bcolors.ENDC} {dest_path}\n", flush=True)

    # Start actual procerssing
    main_cfm()
    

    

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

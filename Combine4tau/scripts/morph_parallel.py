#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import glob
import argparse
from multiprocessing import Pool

def execute(cmd):
    try:
        os.system(cmd)
    except:
        print "[WARNING] Command failed:",cmd

parser = argparse.ArgumentParser( description = "Compare Integrals of Processes between ML and Cutbased shapes")
parser.add_argument('--output-folder', required = True, help = "Main folder, where the datacards should be created")
parser.add_argument('--analysis', required = True, help = "Analysis to be prepared with morphing")
parser.add_argument('--category-list', required = True, help = "Category list, which will be used for parallelization of morphing")
parser.add_argument('--variable', required = True, help = "Variable to be used for the list of categories")
parser.add_argument('--eras', required = True, help = "Eras list, which will be used for parallelization of morphing")
parser.add_argument('--parallel', type=int, default=5, help = "Cores provided for parallel morphing")
parser.add_argument('--additional-arguments', type=str, default="--auto_rebin=1" , help = "Additional arguments to be passed to the Morphing executable")
parser.add_argument('--dry-run',action='store_true', help = "Don't execute, only list Morphing commands")
args = parser.parse_args()

categories = []
with open(args.category_list, "r") as f:
    categories = [l.strip() for l in f.readlines()]

eras = args.eras.split(',')

commands = []

command_template = "Morphing4tau --era={ERA} --category={CATEGORY} --output_folder={OUTPUT} --analysis={ANALYSIS} --variable={VARIABLE} {ADDITIONALARGS}"
for era in eras:
    for category in categories:
        command = command_template.format(ERA=era, CATEGORY=category, ANALYSIS=args.analysis,
                                          ADDITIONALARGS=args.additional_arguments, OUTPUT=args.output_folder,
                                          VARIABLE=args.variable)
        commands.append(command)

if args.dry_run:
    for command in commands:
        print command

else:
    p = Pool(args.parallel)
    p.map(execute, commands)

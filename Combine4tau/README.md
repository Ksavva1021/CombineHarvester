# 4tau Guide

## Step 1: Harvesting Datacards (TH1 -> txt datacards)

**python scripts/harvestDatacards.py**

Before you run this script, you have to set up the configuration file located at **config/harvestDatacards.yml**. Options available in the config are:

    -output_folder: Folder to store the txt datacards
    -analysis: Analysis name (same thing as htt in the past)
    -era_tag: Era/Year to harvest datacards for
    -channels: Channels to harvest datacards for
    -variable: Discriminator to harvest datacards for
    -categories: Categories per channel to harvest datacards for
    -background_processes: List of background processes per channel
    -signal_processes: Signal processes (This only includes the mass of the pseudoscalar since the mass of phi is added as a shift)
    -mass_shifts: Grid of phi masses
    -auto-rebin: Enable CH auto re_bin
    -auto_mc: Use CH AutoMCStats
    -verbose
 
For multi-categories, you have to hadd the root datacards with the TH1s. You can use **scripts/util/haddDatacards.py** but, you have to add in your directory with the root datacards and your shapes output directory. I will set this up to pull from **config/harvestDatacards.yml** so, we don't have to edit the script everytime but, for now you can do it like this.

## Step 2: Building Workspaces, Computing Limits and Collecting Limits

**python scripts/harvestDatacards_step2.py**

Before you run this script, you have to set up the configuration file located at **config/harvestDatacards.yml**. Options available in the config are:

    -output_folder: Folder in which the txt datacards are stored
    -year: Era/Year to harvest datacards for
    -categories: Categories per channel
    -combine_categories: categorical combinations you want to create cmb folders for e.g. for mmtt create a cmb_mmtt_os_ss folder with the relevant os and ss root files and txt datacards
    -build_workspaces: option to build workspaces when you run code (this builds them for all categories defined above)
    -build_combined_workspaces: option to build workspaces for the combined categories
    -calculate_AsymptoticLimits: Calculate asymptotics for all categories defined above (individual ones)
    -calculate_combined_AsymptoticLimits: Calculate asymptotics for combined categories
    -calculate_HybridNew: Calculate limits with toys (Don't use this at the moment I need to set it up nicely for all limit bands)
    -unblind: Option to unblind
    -collect_limits: Collect Limits for individual categories
    -collect_combined_limits: Collect limits for combined categories
    -grid_A: Grid of pseudoscalar masses
    -grid_phi: Grid of phi masses


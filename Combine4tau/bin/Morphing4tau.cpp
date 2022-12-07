#include "CombineHarvester/CombinePdfs/interface/MorphFunctions.h"
#include "CombineHarvester/CombinePdfs/interface/CMSHistFuncFactory.h"
#include "CombineHarvester/CombineTools/interface/Algorithm.h"
#include "CombineHarvester/CombineTools/interface/AutoRebin.h"
#include "CombineHarvester/CombineTools/interface/BinByBin.h"
#include "CombineHarvester/CombineTools/interface/CardWriter.h"
#include "CombineHarvester/CombineTools/interface/CombineHarvester.h"
#include "CombineHarvester/CombineTools/interface/Observation.h"
#include "CombineHarvester/CombineTools/interface/Process.h"
#include "CombineHarvester/CombineTools/interface/Systematics.h"
#include "CombineHarvester/CombineTools/interface/Utilities.h"
#include "CombineHarvester/Combine4tau/interface/dout_tools.h"
#include "RooRealVar.h"
#include "RooWorkspace.h"
#include "TF1.h"
#include "TH2.h"
#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/split.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/program_options.hpp"
#include "boost/regex.hpp"
#include <cstdlib>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <utility>
#include <vector>
#include <math.h>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>

using namespace std;
using boost::starts_with;
namespace po = boost::program_options;

int main(int argc, char **argv) {
	
  typedef vector<string> VString;
  typedef vector<pair<int, string>> Categories;
  using ch::syst::bin_id;
  using ch::JoinStr;

  // Define program options
  string output_folder = "output";
  string base_path = string(getenv("CMSSW_BASE")) + "/src/CombineHarvester/Combine4tau/shapes/";  
  string chan = "all";
  string category = "all";
  string analysis = "2HDM";
  string variable = "mvis_min_sum_dR_1";
 
  bool auto_rebin = false;
  bool use_automc = true;
  //bool real_data = false;
  bool verbose = false;

  int era = 2018; // 2016, 2017 or 2018
  std::vector<int> era_choices = {2016, 2017, 2018};	
  
  po::variables_map vm;
  po::options_description config("configuration");
  config.add_options()
      ("base-path,base_path", po::value<string>(&base_path)->default_value(base_path), "inputs, expected to contain a subdirectory <era>/<channel>")
      ("channel", po::value<string>(&chan)->default_value(chan), "single channel to process")
      ("category", po::value<string>(&category)->default_value(category))
      ("variable", po::value<string>(&variable)->default_value(variable))
      ("auto_rebin", po::value<bool>(&auto_rebin)->default_value(auto_rebin))
      //("real_data", po::value<bool>(&real_data)->default_value(real_data))
      ("use_automc", po::value<bool>(&use_automc)->default_value(use_automc))
      ("verbose", po::value<bool>(&verbose)->default_value(verbose))
      ("output_folder", po::value<string>(&output_folder)->default_value(output_folder))
      ("analysis", po::value<string>(&analysis)->default_value(analysis))
      ("era", po::value<int>(&era)->default_value(era))
      ("help", "produce help message");
  po::store(po::command_line_parser(argc, argv).options(config).run(), vm);
  po::notify(vm);
  if (vm.count("help"))
  {
    cout << config << "\n";
    return 0;
  }	 
  
  // Define the location of the "auxiliaries" directory where we can
  // source the input files containing the datacard shapes
  std::string era_tag;
  if (era == 2016) era_tag = "2016";
  else if (era == 2017) era_tag = "2017";
  else if (era == 2018) era_tag = "2018";
  else std::runtime_error("Given era is not implemented.");

  output_folder = output_folder + "_" + analysis;
  std::map<string, string> input_dir;
  if (base_path.back() != '/' ) base_path += "/";
  if (!boost::filesystem::exists(output_folder)) boost::filesystem::create_directories(output_folder);
  // input_dir["eett"] = base_path + "/" +era_tag + "_hig-19-010" + "/eett/";
  input_dir["eett"] = base_path + "/" +era_tag + "/eett/";
  input_dir["emtt"] = base_path + "/" +era_tag + "/emtt/";
  input_dir["ettt"] = base_path + "/" +era_tag + "/ettt/";
  input_dir["mmtt"] = base_path + "/" +era_tag + "/mmtt/";	
  input_dir["mttt"] = base_path + "/" +era_tag + "/mttt/";		
  input_dir["tttt"] = base_path + "/" +era_tag + "/tttt/";	
  
  // Define channels
  VString chns;
  if (chan.find("eett") != std::string::npos)
    chns.push_back("eett");
  if (chan.find("emtt") != std::string::npos)
    chns.push_back("emtt");
  if (chan.find("ettt") != std::string::npos)
    chns.push_back("ettt");
  if (chan.find("mmtt") != std::string::npos)
    chns.push_back("mmtt");	
  if (chan.find("mttt") != std::string::npos)
    chns.push_back("mttt");
  if (chan.find("tttt") != std::string::npos)
    chns.push_back("tttt");	
  if (chan == "all")
    chns = {"eett", "emtt", "ettt","mmtt","mttt","tttt"};
  
  
  // Define restriction to the channel defined by '--category' option
  if(category != "all"){
    std::vector<std::string> category_split;
    boost::split(category_split, category, boost::is_any_of("_"));
    chns = {category_split.at(0)};
  }  
  doutnonl("Channels:\n\t");
  dprintVector(chns);
	
  // Define background and signal processes
  map<string, VString> bkg_procs;
  VString bkgs;
  
  bkgs = {"ZJF","ZLF","ZR","TTR","TTJF","TTLF","VVJF","VVLF","VVR","VVV","WGam","WJF","WR","WLF"};
  std::cout << "[INFO] Considering the following processes as main backgrounds:\n";  
	
  if (chan.find("eett") != std::string::npos || chan.find("emtt") != std::string::npos || chan.find("ettt") != std::string::npos || chan.find("mmtt") != std::string::npos || chan.find("mttt") != std::string::npos || chan.find("tttt") != std::string::npos) {
    std::cout << "For eett,emtt,ettt,mmtt,mttt,tttt channels : \n";
    for (unsigned int i=0; i < bkgs.size(); i++) std::cout << bkgs[i] << std::endl;
  }
  bkg_procs["eett"] = bkgs;
  bkg_procs["emtt"] = bkgs;
  bkg_procs["ettt"] = bkgs;
  bkg_procs["mmtt"] = bkgs;
  bkg_procs["mttt"] = bkgs;
  bkg_procs["tttt"] = bkgs;
  
  // Specify signal processes and masses
  vector<string> sig_procs;
  sig_procs = {
	"A60phi","A100phi","A150phi"
  };

  vector<string> phi_masses;
  phi_masses = {"100","200","300"};
  
  //Define 2HDM phi mass parameter Mphi
  RooRealVar Mphi("MH", "MH", 125., 60., 800.);
  Mphi.setConstant(true);

  // Define categories
  map<string, Categories> cats;
  cats["eett"] = {{ 1 , "eett_inclusive"} };
  cats["emtt"] = {{ 1 , "emtt_inclusive"} };
  cats["ettt"] = {{ 1 , "ettt_inclusive"} };
  cats["mmtt"] = {{ 1 , "mmtt_inclusive"} };
  cats["mttt"] = {{ 1 , "mttt_inclusive"} };
  cats["tttt"] = {{ 1 , "tttt_inclusive"} };

  // Create combine harverster object
  ch::CombineHarvester cb;
  cb.SetFlag("workspaces-use-clone", true);
  
  // Add observations and processes
  for (auto chn : chns) {
    cb.AddObservations({"*"}, {"htt"}, {era_tag}, {chn}, cats[chn]);
    cb.AddProcesses({"*"}, {"htt"}, {era_tag}, {chn}, bkg_procs[chn], cats[chn],
                    false);
    cb.AddProcesses(phi_masses, {"htt"}, {era_tag}, {chn}, sig_procs, cats[chn],
                    true);
  }
  
  for (string chn : chns) {
      string input_file_base = input_dir[chn] + "datacard_" + variable + "_inclusive_" + chn + "_" + era_tag + ".root";
      cb.cp().channel({chn}).process(bkg_procs[chn]).ExtractShapes(
                input_file_base, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC");
      cb.cp().channel({chn}).process(sig_procs).ExtractShapes(
                input_file_base, "$BIN/$PROCESS$MASS", "$BIN/$PROCESS$MASS_$SYSTEMATIC");
    }
  
  // Delete processes with 0 yield
  //cb.FilterProcs([&](ch::Process *p) {
  //  if (std::find(sig_procs.begin(), sig_procs.end(), p->process()) != sig_procs.end())
  //  {
  //    return false;
  //  }
  //  bool null_yield = !(p->rate() > 0.0);
  //  if (null_yield) {
  //    std::cout << "[WARNING] Removing process with null yield: \n ";
  //    std::cout << ch::Process::PrintHeader << *p << "\n";
      //cb.FilterSysts([&](ch::Systematic *s) {
      //  bool remove_syst = (MatchingProcess(*p, *s));
      //  return remove_syst;
      //}
	  //);
  // }
  //  return null_yield;
  //});  
  

  // At this point we can fix the negative bins
  //std::cout << "[INFO] Fixing negative (-ve)  bins.\n";
  //cb.ForEachProc([](ch::Process *p) {
  //  if (ch::HasNegativeBins(p->shape())) {
  //    auto newhist = p->ClonedShape();
  //    ch::ZeroNegativeBins(newhist.get());
  //    p->set_shape(std::move(newhist), false);
  //  }
  //});

  // Perform auto-rebinning
//  if (auto_rebin) {
//    std::cout << "[INFO] Performing auto-rebinning.\n";
//    auto rebin = ch::AutoRebin().SetBinThreshold(10.0).SetBinUncertFraction(0.9).SetRebinMode(1).SetPerformRebin(true).SetVerbosity(1);
//    rebin.Rebin(cb, cb);
//  }



//  // This function modifies every entry to have a standardised bin name of
//  // the form: {analysis}_{channel}_{bin_id}_{era}
//  ch::SetStandardBinNames(cb, "$ANALYSIS_$CHANNEL_$BINID_$ERA");
//  ch::CombineHarvester cb_obs = cb.deep().backgrounds();

//  // Adding bin-by-bin uncertainties
//  if (use_automc) {
//    std::cout << "[INFO] Adding bin-by-bin uncertainties.\n";
//    cb.SetAutoMCStats(cb, 0.);
//  }
  
  // Setup morphed mssm signals for bsm analyses
  RooWorkspace ws("htt", "htt");

  std::map<std::string, RooAbsReal *> mass_var = {
  	{"A60phi", &Mphi},{"A100phi", &Mphi},{"A150phi",&Mphi}
  };

  std::map<std::string, std::string> process_norm_map = {
        {"A60phi", "prenorm"},{"A100phi", "prenorm"},{"A150phi","prenorm"}
  };  
  
  // Perform morphing
  std::cout << "[INFO] Performing template morphing for 2HDM.\n";
  auto morphFactory = ch::CMSHistFuncFactory();
  morphFactory.SetHorizontalMorphingVariable(mass_var);
  morphFactory.Run(cb, ws, process_norm_map);
  /*for (auto bin : cp.cp().bin_set())
  {
    for (auto proc : sig_procs) {
       std::string prenorm_name = bin + "_" + proc + "_morph_prenorm";
       std::string norm_name = bin + "_" + proc + "_morph_norm";
       std::string proc_frac = boost::replace_all_copy(proc,"ggX","ggh");
       ws.factory(TString::Format("expr::%s('@0*@1',%s, %s_frac)", norm_name.c_str(), prenorm_name.c_str(), proc_frac.c_str()));
    }
  }
  */
  cb.AddWorkspace(ws);
  cb.ExtractPdfs(cb, "htt", "$BIN_$PROCESS_morph");
  cb.ExtractData("htt", "$BIN_data_obs");
  std::cout << "[INFO] Finished template morphing for mssm ggh and bbh.\n";

  std::cout << "[INFO] Writing datacards to " << output_folder << std::endl;
    
  // Decide, how to write out the datacards depending on --category option
  // Write out datacards. Naming convention important for rest of workflow. We
  // make one directory per chn-cat, one per chn and cmb. In this code we only
  // store the individual datacards for each directory to be combined later.
  ch::CardWriter writer(output_folder + "/" + era_tag + "/$BIN/$BIN.txt",
                        output_folder + "/" + era_tag + "/$BIN/common/$BIN_input_" + era_tag + ".root");
  std::cout << "after writer" << std::endl;
  // We're not using mass as an identifier - which we need to tell the
  // CardWriter
  // otherwise it will see "*" as the mass value for every object and skip it
  writer.SetWildcardMasses({});

  // Set verbosity
  if (verbose)
    writer.SetVerbosity(1);

  // Write datacards combined and per channel
  writer.WriteCards("cmb", cb);

  for (auto chn : chns) {
    writer.WriteCards(chn, cb.cp().channel({chn}));
  }

  if (verbose)
    cb.PrintAll();

  std::cout << "[INFO] Done producing datacards.\n";
}

#include "HistMaker.h"

// Root headers
#include "TROOT.h"
#include "TH1D.h"
#include "TFile.h"
#include "TChain.h"
#include "TLorentzVector.h"
#include "TMath.h"
#include "Math/Vector4D.h"

// c++ headers
#include <iostream>
#include <sys/stat.h>
#include <stdexcept>

// Main function to run in executable
int main(int argc, char* argv[])
{
    // Want command line arguments to be:
    //  (1) sample (data, ggfHiggs, VBFHiggs)
    // argc is our args + 1
    if (argc==2){
        const char* sample = argv[1];
        std::stringstream ssSample;
        ssSample << sample;
        std::string strSample = ssSample.str();

        // TODO not ideal to have these hard-coded paths... how could you make this more flexible? 
        std::string ntuplePath = "data/GamGam";
        std::string outputPath = "histograms/GamGam_rootCpp/";
        struct stat check;
        if (stat(outputPath.c_str(), &check) != 0){
            throw std::runtime_error(outputPath+" doesn't exist, please create it.");
        }

        std::string outHists_name = outputPath + strSample + ".root";
        TFile *outHists = TFile::Open(outHists_name.c_str(), "RECREATE");

        bool isData = (strSample.find("data") != std::string::npos) || (strSample.find("Data") != std::string::npos);

        std::string treename = "mini";
        TChain* chain = new TChain(treename.c_str(), "");
        std::string filename;
        if (isData){
            std::vector dataindices = {"A", "B", "C", "D"};
            for (auto i : dataindices)
            {
                std::string filename = ntuplePath + "/Data/data_" + i + ".GamGam.root";
                chain->Add(filename.c_str());
            }
        }
        else
        {
            // given an example of using a map:
            std::map<std::string, std::string> MCnames = {
                {"ggfHiggs", "/MC/mc_343981.ggH125_gamgam.GamGam.root"},
                {"VBFHiggs", "/MC/mc_345041.VBFH125_gamgam.GamGam.root"}
            };
            std::string filename = ntuplePath + MCnames[sample];
                try{
                    chain->Add(filename.c_str());
                }
                catch (...){
                    throw std::runtime_error("not a valid input choice: select ggfHiggs or VBFHiggs");
                }
        }

        // Initalise out HistMaker class
        HistMaker myHistMaker;
        // Run the event looper on our sample.
        myHistMaker.EventLooper(chain, outHists, isData);

    }
    else
    {
        throw std::runtime_error("need 1 argument for what sample to run over");
    }

}
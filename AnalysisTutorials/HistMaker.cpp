#define HistMaker_cpp
#include "HistMaker.h"

// Root headers
#include "TROOT.h"
#include "TH1D.h"
#include "TFile.h"
#include "TChain.h"
#include "TCanvas.h"
#include "TBranchElement.h"
#include "TLorentzVector.h"
#include "TMath.h"
#include "Math/Vector4D.h"

// c++ headers
#include <iostream>
#include <sys/stat.h>
#include <stdexcept>

HistMaker::HistMaker(TTree *tree)
{
    // constructor for an instance of our HistMaker class.
    // if parameter tree is not specified (or zero), connect the file
    // used to generate this class and read the Tree.
    if (tree == 0) {
        #ifdef SINGLE_TREE
            TFile *f = (TFile*)gROOT->GetListOfFiles()->FindObject("Memory directory");
    
            tree = (TTree*)gDirectory->Get("mini");

        #else //SINGLE_TREE
            TChain *chain = new TChain("mini","");
            chain->Add("mini");
            tree = chain;
        #endif
    }

    Init(tree);

}

HistMaker::~HistMaker()
{
    // Destructor
    if (!fChain) return;
    delete fChain->GetCurrentFile();
}


Long64_t HistMaker::GetNEvents()
{
    ///
    // TODO
    //
    Long64_t nentries = fChain->GetEntries();
    if (nentries==0){
        std::cerr << "oh no, the files are empty or read in wrong :( ";
        return EXIT_FAILURE;
    }
    return nentries;
}

void HistMaker::SetupHist1D(TH1D*& hist, TFile* file, std::string name, int nbins, float xlow, float xhigh, std::string xlab)
{
    ///
    // TODO
    //
    std::string titles = name+";"+xlab+";Events / bin";
    hist = new TH1D(name.c_str(), titles.c_str(), nbins, xlow, xhigh);
    // Make sure it stores sum of weights squared and sets bin errors as sqrt(sum-of-weights), correct for weighted histogram.
    hist->Sumw2();
    hist->SetDirectory(file);
    std::cout << "Registering histogram... " << name << std::endl;

}


void HistMaker::Init(TTree *tree)
{
    std::cout<<tree<<std::endl;
    if (!tree){
        std::cerr << "there's no TTree to initialise!";
        return;
    }
    fChain = tree;
    
    // by default don't read any branches, to speed up.
    fChain->SetBranchStatus("*",0);

    // switch on the branches to read
    fChain->SetBranchStatus("photon_pt", 1);
    fChain->SetBranchAddress("photon_pt", &photon_pt);//, &b_photon_pt);
    fChain->SetBranchStatus("photon_E", 1);
    fChain->SetBranchAddress("photon_E", &photon_E);//, &b_photon_E);
    fChain->SetBranchStatus("photon_phi", 1);
    fChain->SetBranchAddress("photon_phi", &photon_phi);//, &b_photon_phi);
    fChain->SetBranchStatus("photon_eta", 1);
    fChain->SetBranchAddress("photon_eta", &photon_eta);//, &b_photon_eta);

    fChain->SetBranchStatus("mcWeight", 1);
    fChain->SetBranchAddress("mcWeight", &mcWeight);//, &b_mcWeight);
    fChain->SetBranchStatus("XSection", 1);
    fChain->SetBranchAddress("XSection", &xsec_ipb);//, &b_xsec_ipb);
    fChain->SetBranchStatus("SumWeights", 1);
    fChain->SetBranchAddress("SumWeights", &sumWeights);//, &b_sumWeights);
    fChain->SetBranchStatus("scaleFactor_PILEUP", 1);
    fChain->SetBranchAddress("scaleFactor_PILEUP", &pileupSF);//, &b_pileupSF);
    
    // TODO include the scaleFactor_PHOTON in the event weight
    
    return;

}

void HistMaker::EventLooper(TChain* chain, TFile *outHists, bool isData)
{
    ///
    // TODO
    //

    SetupHist1D(hist_pTGam_1, outHists, "photon_pT_1", 100, 0., 500., "pT [GeV]");
    SetupHist1D(hist_pTGam_2, outHists, "photon_pT_2", 100, 0., 500., "pT [GeV]");
    SetupHist1D(hist_EGam_1, outHists, "photon_E_1", 100, 0., 500., "E [GeV]");
    SetupHist1D(hist_EGam_2, outHists, "photon_E_2", 100, 0., 500., "E [GeV]");
    SetupHist1D(hist_etaGam_1, outHists, "photon_eta_1", 10, -2.5, 2.5, "#eta");
    SetupHist1D(hist_etaGam_2, outHists, "photon_eta_2", 10, -2.5, 2.5, "#eta");
    SetupHist1D(hist_phiGam_1, outHists, "photon_phi_1", 10, -4., 4., "#phi");
    SetupHist1D(hist_phiGam_2, outHists, "photon_phi_2", 10, -4., 4., "#phi");
    SetupHist1D(hist_mGamGam, outHists, "diphoton_mass", 100, 0., 1000., "m#gamma#gamma [GeV]");

    HistMaker::Init(chain);

    
    Long64_t nentries = GetNEvents();
    std::cout << "There are " << nentries << " events in the TTree" << std::endl;


    for (Long64_t entry=0; entry<nentries; entry++)
    {
        // some printout to track progress
        if (entry%5000 == 0)
        {
            int pcnt_done = static_cast<int>(std::round(100*entry/nentries));
            std::cout << "Processed " << entry << " events, " << pcnt_done << "% done." << std::endl;
        }

        // read the entry from the ntuple
        fChain->GetEntry(entry);

        // read in the event weight
        float histoweight = 1.0;
        if (!isData) 
        {
            // MC event weighting to luminosity of data
            histoweight = mcWeight * xsec_ipb *1000. * luminosity_ifb / sumWeights;
            // MC weight corrections for experimental effects
            histoweight = histoweight * pileupSF;
            // TODO multiply by the photon scale factor weight
        }

        // Need events that have at least 2 photons in to start with.
        // Note we are formating this as "if fail requirement exit and move to the next event in the loop". "if pass opposite-to-requirement" is also fine but I find this more readable in this scenario in terms of what requirements we do want.
        if (!(photon_pt->size() >= 2)) continue;
        
        // Obtain the kinematic variables (note TTree is in MeV and I want GeV)
        float photon_1_pt = photon_pt->at(0)*0.001;
        float photon_2_pt = photon_pt->at(1)*0.001;
        float photon_1_E = photon_E->at(0)*0.001;
        float photon_2_E = photon_E->at(1)*0.001;
        float photon_1_eta = photon_eta->at(0);
        float photon_2_eta = photon_eta->at(1);
        float photon_1_phi = photon_phi->at(0);
        float photon_2_phi = photon_phi->at(1);

        // Need to check the photons are in the fiducial region
        if (!((std::fabs(photon_1_eta) < 2.37 && (std::fabs(photon_1_eta) < 1.37 || std::fabs(photon_1_eta) > 1.56)) && 
            (std::fabs(photon_2_eta) < 2.37 && (std::fabs(photon_2_eta) < 1.37 || std::fabs(photon_2_eta) > 1.56)))) continue;

        // We need to apply the photon trigger requirements, approximated by requiring our photons to have photon 1(2) pT > 35(25) GeV
        if (!(photon_1_pt > 35. && photon_2_pt > 25.)) continue;


        // TODO we're also only interested in the case where our two photons have passed a Tight particle ID, to reduce misreconstruction backgrounds.
        // Can you use the boolean "photon_isTightID" vector branch to require this?..

        // Only interested in events that have exactly 2 photons in that pass those requirements.
        if (!(photon_pt->size() == 2)) continue;

        ROOT::Math::PtEtaPhiEVector photon_1_p4(photon_1_pt, photon_1_eta, photon_1_phi, photon_1_E);
        ROOT::Math::PtEtaPhiEVector photon_2_p4(photon_2_pt, photon_2_eta, photon_2_phi, photon_2_E);

        float diphoton_mass = (photon_1_p4 + photon_2_p4).M();

        // Another requirement for the events is a pT/diphoton mass bound
        if (!(photon_1_pt/diphoton_mass > 0.35 && photon_2_pt/diphoton_mass > 0.25)) continue;

        // Fill the histograms in the output file with the event values.
        hist_pTGam_1->Fill(photon_1_pt, histoweight);
        hist_pTGam_2->Fill(photon_2_pt, histoweight);
        hist_EGam_1->Fill(photon_1_E, histoweight);
        hist_EGam_2->Fill(photon_2_E, histoweight);
        hist_etaGam_1->Fill(photon_1_eta, histoweight);
        hist_etaGam_2->Fill(photon_2_eta, histoweight);
        hist_phiGam_1->Fill(photon_1_phi, histoweight);
        hist_phiGam_2->Fill(photon_2_phi, histoweight);
        hist_mGamGam->Fill(diphoton_mass, histoweight);

    }

    // write histograms to root file for further analysis.
    outHists->Write();
    outHists->Close();

}

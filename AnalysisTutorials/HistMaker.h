#ifndef HistMaker_h
#define HistMaker_h

// Root headers
#include "TROOT.h"
#include "TH1D.h"
#include "TFile.h"
#include "TChain.h"
#include "TCanvas.h"
#include "TBranchElement.h"
#include "TLorentzVector.h"

class HistMaker
{

public:
    TTree *fChain; //! pointer to analysed TTree/TChain
    Int_t fCurrent; //! current Tree number in a chain
    TFile *f; //! pointer to file 
    int nentries;

    float luminosity_ifb = 10.;

    // Declaration of leaf types (root types)
    Float_t mcWeight = 0.;
    Float_t xsec_ipb = 0.;
    Float_t sumWeights = 0.;
    Float_t pileupSF = 0.;

    std::vector<Float_t> *photon_pt = 0;
    std::vector<Float_t> *photon_E = 0;
    std::vector<Float_t> *photon_eta = 0;
    std::vector<Float_t> *photon_phi = 0;

    // Declare functions
    Long64_t GetNEvents();
    void SetupHist1D(TH1D*& hist, TFile* file, std::string name, int nbins, float xlow, float xhigh, std::string xlab);
    void Init(TTree *tree);
    void EventLooper(TChain* chain, TFile *outHists, bool isData);


    // Define output Histograms
    TH1D *hist_pTGam_1;
    TH1D *hist_pTGam_2;
    TH1D *hist_EGam_1;
    TH1D *hist_EGam_2;
    TH1D *hist_etaGam_1;
    TH1D *hist_etaGam_2;
    TH1D *hist_phiGam_1;
    TH1D *hist_phiGam_2;
    TH1D *hist_mGamGam;

    // constructor
    HistMaker(TTree *tree = 0);

    // destructor
    virtual ~HistMaker();

private:

};

#endif /* HistMaker_h */


// Int_t HistMaker::GetEntry(Long64_t entry)
// {
// // Read contents of entry.
//    if (!fChain) return 0;
//    return fChain->GetEntry(entry);
// }

// Long64_t HistMaker::LoadTree(Long64_t entry)
// {
// // Set the environment to read one entry
//    if (!fChain) return -5;
//    Long64_t centry = fChain->LoadTree(entry);
//    if (centry < 0) return centry;
//    if (!fChain->InheritsFrom(TChain::Class()))  return centry;
//    TChain *chain = (TChain*)fChain;
//    if (chain->GetTreeNumber() != fCurrent) {
//       fCurrent = chain->GetTreeNumber();
//       Notify();
//    }
//    return centry;
// }

/*
Now we look at making stacked histograms of the signals, and then a plot of the spectrum with signal, data and a fitted background function.

This example demonstrates use of a C++ Root Macro. if we run:
root -q -l AnalysisTutorials/part1_plotter.root.C

then we will run the part1_plotter function inside an interactive root window; and then leave root (by the -q flag)
(if we had arguements to our functinon we could run it via:
    root -q -l AnalysisTutorials/part1_plotter.root.C'(arg1, "strarg")'
)


This example uses ATLAS open data from 2015+2016. We are looking at a simple version of the Higgs->GammaGamma discovery anlaysis.
(https://arxiv.org/pdf/1408.7084)

Things to try:
- where there are #TODOs in the code
- Look for chunks of code that are repeated between these 2 functions - how could we make the overal script shorter using functions/classes?
- how might you change the way we are setting up our hard-coded settings to add flexibility? Our main function is currently very poorly written, it would be better if we didn't have to recompile the code if we decided to change the binning or move the in/out files etc....
- we already gave an x-axis label in the histogram production but what if we want to override that now .eg. to change mGamGam to m_{GamGam} or M(GamGam)?
- do you understand what's happening to the overflow and underflow bins? 
*/

// Root headers
#include "TROOT.h"
#include "TStyle.h"
#include "TRint.h"
#include "TFile.h"
#include "TCanvas.h"
#include "TLegend.h"
#include "TLatex.h"
#include "TLine.h"
#include "THStack.h"
#include "TPad.h"
#include "TF1.h"
#include "TGraphAsymmErrors.h"
#include "TColor.h"
#include "Fit/DataRange.h"

#include "../utils/AtlasStyle.C"

// c++ headers
#include <iostream>
#include <sys/stat.h>
#include <stdexcept>
#include <string>

void plotStack(std::map<std::string, TH1F*> histsin, std::vector<float> xrange, std::string plotdir, std::string variable, int rebin=1)
{
    /*
    plot a stack of filled histograms

    Args:
        histsin (std::map<std::str,TH1*>): str labels of input hists and the hists themselves.
        xrange (std::vector<float>): min and max x-range.
        plotdir (std::string): directory to save plot to.
        variable (std::string): name of variable to plot.
        rebin (int): to rebin newbinwidth = rebin * oldbinwidth

    */
    if (xrange.size() < 2) throw std::out_of_range("need 2 values for x axis range");
    if (int(rebin)!=rebin) throw std::runtime_error("need rebin to be an integer");

    // define some config
    std::map<std::string, std::string> legenddict = {{"ggfHiggs", "ggf H#gamma#gamma"}, 
                                                    {"VBFHiggs", "VBF H#gamma#gamma"}};
    // See the glorious TColor wheel and text to see what these numbers mean: https://root.cern.ch/doc/master/classTColor.html
    std::map<std::string, int> colourdict = {{"ggfHiggs", 815},
                                                {"VBFHiggs", 610}};

    // initialise our canvas
    TCanvas* canvas = new TCanvas(variable.c_str(), variable.c_str(), 200, 10, 700, 750);
    canvas->cd(1); // point current root tdirectory and Draw()s to it
    canvas->SetTopMargin(0.03);
    canvas->SetRightMargin(0.05);
    canvas->SetLeftMargin(0.12);
    canvas->SetFillColor(kWhite);
    canvas->SetFillStyle(0);
    canvas->SetLineWidth(1);
    canvas->SetLogy(1);

    // intiialise our legend
    TLegend* legend = new TLegend(0.7, 0.8, 0.95, 0.94);
    legend->SetTextFont(42);
    legend->SetTextSize(0.036);
    legend->SetFillStyle(0);
    legend->SetBorderSize(0);
  
    // initalise our Stack
    THStack* stack = new THStack("signal_stack", ";;Events / bin");

    // read in and config our histograms
    std::map<std::string, TH1F*> hist = {};
    // iterate through input hists, lets use an iterator, which points to the start of the map and then moves through it:
    std::map<std::string, TH1F*>::iterator it = histsin.begin();
    while (it != histsin.end()){
        std::string label = it->first;
        TH1F* histin = it->second;
        hist.insert(std::pair<std::string, TH1F*>(label, (TH1F*)histin->Clone(label.c_str())));
        hist[label]->Sumw2();
        if (rebin!=1) hist[label]->Rebin(rebin);
        hist[label]->GetXaxis()->SetRangeUser(xrange[0], xrange[1]);
        hist[label]->SetFillColor(colourdict[label]);
        stack->Add(hist[label]);
        legend->AddEntry(hist[label], legenddict[label].c_str(), "f"); // f= filled
        // move iterator along
        it++;
    }

    // Get the stack total
    TH1F* stack_total = (TH1F*)stack->GetStack()->Last()->Clone("total");
    stack_total->GetXaxis()->SetRangeUser(xrange[0], xrange[1]);
    stack_total->SetFillStyle(0); // 0 = hollow
    // Extract error on SM total
    TGraphAsymmErrors* total_error = new TGraphAsymmErrors(stack_total);
    total_error->GetXaxis()->SetRangeUser(xrange[0], xrange[1]);
    total_error->SetFillStyle(3005);
    total_error->SetMarkerSize(0);
    total_error->SetFillColor(kBlack);
    total_error->SetLineColor(kBlack);
    legend->AddEntry(total_error,"Total","flp"); // fill, line, marker

    // find the y range and set nice axis limits around it
    stack_total->GetYaxis()->SetRangeUser(std::max(stack_total->GetMinimum(),0.001)*0.2,stack_total->GetMaximum()*10);

    // actually draw the histograms in the canvas (https://root.cern/doc/v628/classTHistPainter.html)
    stack_total->Draw("hist"); // plot this first to set the y range
    stack->Draw("histf same"); // filled hist
    total_error->Draw("E2");
    // draw the legend
    legend->Draw("same");

    // add some text
    TLatex* l = new TLatex();
    l->SetNDC();
    l->SetTextFont(42);
    l->SetTextColor(kBlack);
    l->SetTextSize(0.036);
    std::string lumi_string = "10 fb^{#minus1} #sqrt{s}=13 TeV";
    l->DrawLatex(0.2, 0.9, lumi_string.c_str());
 
    canvas->RedrawAxis();
    std::vector<std::string> exts = {".pdf", ".png"};
    for (auto ext : exts){
        std::string outname = plotdir + "Stack_" + variable + "_rootcpp" + ext;
        canvas->SaveAs(outname.c_str());
    }

    //delete the pointers we made
    delete canvas;
    delete legend;
    delete stack;
    delete total_error;

}


void plotSigBgData(TH1F* sigHistin, TH1F* dataHistin, std::vector<float> xrange, std::string plotdir, std::string variable, bool blinded, std::vector<float> rangeToBlind)
{
    /*
    plot a signal and data, and fit/plot a parametrised background estimate

    Args:
        sigHists (TH1*): signal histogram
        dataHist (TH1*): data histogram
        xrange (std::vector<float>): min and max x-range.
        plotdir (str): directory to save plot to
        variable (str): name of variable to plot
        blinded (bool): should we blind the data around the signal?
        rangeToBind (std::vector<float>): min and max x values to blind.
    */
    if (xrange.size() < 2) throw std::out_of_range("need 2 values for x axis range");
    
    // initialise our canvas
    TCanvas* canvas = new TCanvas(variable.c_str(), variable.c_str(), 200, 10, 700, 750);
    canvas->cd(1); // point current root tdirectory and Draw()s to it
    canvas->SetTopMargin(0.03);
    canvas->SetRightMargin(0.05);
    canvas->SetLeftMargin(0.12);
    canvas->SetFillColor(kWhite);
    canvas->SetFillStyle(0);
    canvas->SetLineWidth(1);

    // we want 2 pads, for the distribution and ratios.
    TPad* pad1 = new TPad("upper_pad","upper_pad",0.0,0.3,1.0,1.0,21);
    TPad* pad2 = new TPad("lower_pad","lower_pad",0.0,0.0,1.0,0.295,22);
    for (TPad* pad : {pad1, pad2})
    {
        pad->Draw();
        pad->SetRightMargin(0.03);
        pad->SetFillColor(kWhite);
        pad->SetLeftMargin(0.14);
    }
    pad1->SetTopMargin(0.02);
    pad1->SetBottomMargin(0.00);
    pad2->SetTopMargin(0.00);
    pad2->SetBottomMargin(0.3);
    pad1->cd();

    // intiialise our legend
    TLegend* legend = new TLegend(0.6, 0.8, 0.9, 0.94);
    legend->SetTextFont(42);
    legend->SetTextSize(0.036);
    legend->SetFillStyle(0);
    legend->SetBorderSize(0);

    // sort out the data histograms
    TH1F* dataHist = (TH1F*)dataHistin->Clone("data");
    dataHist->GetXaxis()->SetRangeUser(xrange[0], xrange[1]);
    dataHist->Sumw2();
    dataHist->SetMarkerColor(kBlack);
    dataHist->GetYaxis()->SetTitleOffset(1.5);
    dataHist->SetMarkerStyle(20); // https://root.cern.ch/doc/master/classTAttMarker.html 
    if (blinded and variable=="diphoton_mass")
    {
        int minbin = dataHist->FindBin(rangeToBlind[0]);
        int maxbin = dataHist->FindBin(rangeToBlind[1]);
        for (int bin=minbin; bin<=maxbin; bin++) dataHist->SetBinContent(bin, 0.);
    }
    legend->AddEntry(dataHist, "data", "ep"); // lep = line, error, points

    // sort out the signal histogram
    TH1F* sigHist = (TH1F*)sigHistin->Clone("signal");
    sigHist->Sumw2();
    sigHist->GetXaxis()->SetRangeUser(xrange[0], xrange[1]);
    sigHist->SetLineColor(kRed);
    sigHist->SetLineStyle(1);
    sigHist->SetLineWidth(3);
    sigHist->SetMarkerSize(0);
    legend->AddEntry(sigHist, "ggf + VBF SM Higgs", "l"); // line

    // find the y range and set nice axis limits around it
    float ymin = std::max(dataHist->GetMinimum(),0.001)*0.2;
    float ymax = dataHist->GetMaximum()*1.15;
    dataHist->GetYaxis()->SetRangeUser(ymin, ymax);
    
    // actually draw the histograms in the canvas
    dataHist->Draw("PE0X0"); // plot this first to set the y range
    sigHist->Draw("HIST same");

    // functional fit for background function.
    // https://root.cern/doc/master/classTH1.html#a63eb028df86bc86c8e20c989eb23fb2a: predefined fucntions: gaus, landau, expo, pol1,...,9
    // TODO try a 4th order polynominal instead of the exponential, or your own user-defined function.
    // define a bg hist, starting from the data
    TH1F* bgHist = (TH1F*)dataHist->Clone("bg");
    // define the fit object and settings
    TF1* bgFit = new TF1("bgFit", "expo", xrange[0], xrange[1]);
    
    // A bit messy in python but defining excluded range if we want to blind the function
    ROOT::Fit::DataRange frange;
    frange.AddRange(0, xrange[0], rangeToBlind[0]);
    frange.AddRange(0, rangeToBlind[1], xrange[1]);
    // Yes this is a function within a function but it's not really a problem
    auto blindedFit = [&](double *x, double *p)
    {
        if (!frange.IsInside(x[0])){
            TF1::RejectPoint();
            return 0.;
        }
        return bgFit->EvalPar(x,p);
    };

    TF1* blindFit = new TF1("blindFit", blindedFit, xrange[0], xrange[1], bgFit->GetNpar());
    blindFit->SetLineColor(kBlue);
    blindFit->SetLineWidth(3);
    blindFit->SetMarkerSize(0);

    // indicate the region blinded
    TLine* line = new TLine();
    line->SetLineColor(kGray);
    line->SetLineWidth(3);
    line->DrawLine(rangeToBlind[0], ymin, rangeToBlind[0], ymax/1.15);
    line->DrawLine(rangeToBlind[1], ymin, rangeToBlind[1], ymax/1.15);
    TLatex* text = new TLatex();
    text->SetNDC();
    text->SetTextFont(42);
    text->SetTextColor(kGray);
    text->SetTextSize(0.03);
    float left = (rangeToBlind[0] - xrange[0])/(xrange[1] - xrange[0]);
    text->DrawLatex(left + 0.14, 0.7, "Blind in bg fit");

    // setup some plotting options for the bg fit
    bgFit->SetLineColor(kBlue);
    bgFit->SetLineWidth(3);
    bgHist->SetMarkerSize(0);
    bgFit->SetMarkerSize(0);

    // perform the fit and print out the results (note 0 option stops it being drawn automatically in the wrong colour)
    // save the parameters and errors in case we need them later...
    bgHist->Fit("blindFit","0");
    int nparams = blindFit->GetNpar();
    const Double_t* params = blindFit->GetParameters();
    const Double_t* errors = blindFit->GetParErrors();
    for (int p=0; p<nparams; p++)
    {
        std::cout << "parameter " << p << std::endl;
        std::cout << "value: " << params[p] << ", error: " << errors[p] << std::endl;
    }
    
    bgHist->Draw("FUNC same");

    // new function to plot extapolate to the blinded region.
    TF1* plotfit = new TF1("plotfit", "expo", xrange[0], xrange[1]);
    plotfit->SetParameters(blindFit->GetParameters());
    plotfit->SetLineColor(kBlue);
    plotfit->Draw("same");

    legend->AddEntry(plotfit, "SM Background fit","l");

    // draw the legend
    legend->Draw("same");

    // add some text
    TLatex* text2 = new TLatex();
    text2->SetNDC();
    text2->SetTextFont(42);
    text2->SetTextColor(kBlack);
    text2->SetTextSize(0.036);
    std::string lumi_string = "10 fb^{#minus1} #sqrt{s}=13 TeV";
    text2->DrawLatex(0.2, 0.9, lumi_string.c_str());
    text2->SetTextColor(kBlue);
    // TODO make this not wrong/crash if we want to change the fit function:
    std::string fitstr = "fit: y = exp(" + std::to_string(params[0]) + " + " + std::to_string(params[1]) + "*x)";
    text2->DrawLatex(0.2, 0.85, fitstr.c_str());
 
    pad1->RedrawAxis();

    // now lets move to the ratio pad to draw the data/bg and signal/bg.
    pad2->cd();

    TH1F* data_ratio = (TH1F*)dataHist->Clone("data ratio");
    data_ratio->Divide(plotfit);
    data_ratio->GetYaxis()->SetRangeUser(0.01, 1.99);
    data_ratio->GetYaxis()->SetTitle("distribution / SM bg");

    data_ratio->GetXaxis()->SetTitleSize(0.1);
    data_ratio->GetXaxis()->SetTitleOffset(1.3);
    data_ratio->GetXaxis()->SetLabelSize(0.1);

    data_ratio->GetYaxis()->SetTitleSize(0.1);
    data_ratio->GetYaxis()->SetTitleOffset(0.45);
    data_ratio->GetYaxis()->SetLabelSize(0.1);
    data_ratio->GetYaxis()->SetNdivisions(7);

    data_ratio->Draw("PE0X0");
  
    TLine* line2 = new TLine();
    line2->SetLineColor(kBlue);
    line2->SetLineWidth(3);
    line2->DrawLine(xrange[0], 1., xrange[1], 1.);

    TH1F* sig_ratio = (TH1F*)sigHist->Clone("sig ratio");
    sig_ratio->Divide(plotfit);
    sig_ratio->Draw("HIST same");

    pad2->RedrawAxis();

    std::vector<std::string> exts = {".pdf", ".png"};
    for (auto ext : exts){
        std::string outname = plotdir + "SigDataBgFit_" + variable + "_rootcpp" + ext;
        canvas->SaveAs(outname.c_str());
    }

    pad1->Close();
    pad2->Close();
    delete canvas;
    delete pad1;
    delete pad2;
    delete legend;
    delete bgFit;
    delete blindFit;
    delete plotfit;
    delete line;
    delete line2;
    delete text;
    delete text2;

}

int main(int argc, char* argv[])
{

    // Can use a macro to set a lot of style settings you want, experiments might have these to ensure nice uniformity. e.g. here we use the ATLAS one, but you could have your own to get a reliable setup you're happy with.
    //gROOT->LoadMacro("utils/AtlasStyle.C");
    SetAtlasStyle();
    gROOT->SetBatch(1);
    gStyle->SetOptStat(0);
    gStyle->SetPalette(112);
    gStyle->SetTitleYOffset(1.1);

    // Define out input and output paths, make sure the output path exists.
    std::string histPath = "histograms/GamGam_root/";
    std::string plotPath = "plots/GamGam_root/";
    struct stat check;
    if (stat(plotPath.c_str(), &check) != 0){
        throw std::runtime_error(plotPath+" doesn't exist, please create it.");
    }

    //===============================================================================================================
    // First do the Stack plot example.
    // config our samples and variables
    std::vector<std::string> samplesToStack = {"VBFHiggs", "ggfHiggs"};
    std::vector<std::string> varsToPlot = {"diphoton_mass"};
    
    // Note we already nicely defined our x-axis label and binning in the previous script, but you could override/refine that here.
    std::map<std::string, std::vector<float>> xrangeDict = {{"diphoton_mass", {0., 500}}};
    std::map<std::string, int> rebinDict = {{"diphoton_mass", 5}};

    // TODO can you alter the function to allow us to use variable size bins?
    // rebin docs here: https://root.cern.ch/doc/master/classTH1.html#a9eef6f499230b88582648892e5e4e2ce
    
    // retrieve the histogram files
    std::map<std::string, TFile*> files;
    for (auto sample : samplesToStack)
    {
        std::string filename = histPath + sample + ".root";
        files[sample] = new TFile(filename.c_str(), "READ");
        std::cout << files[sample] << std::endl;
    }
    for (auto var : varsToPlot)
    {
        // produce dict of our histograms per sample 
        std::map<std::string, TH1F*> histsin;
        for (auto sample : samplesToStack)
        {
            histsin[sample] = (TH1F*)files[sample]->Get(var.c_str());
            std::cout << histsin[sample] << std::endl;
        }
        // produce the stack plots
        plotStack(histsin, xrangeDict[var], plotPath, var, rebinDict[var]);
    }

    //===============================================================================================================
    // now run the signal/data/bgFitter plot function:

    std::string variable = "diphoton_mass";
    // do we want to blind the visual of the plot?
    bool blind = true;
    // want to blind the signal part of the fit in any case so we don't fit the background to bits of data that might have signal in.
    std::vector<float> rangeToBlind = {105., 145.}; //GeV
    // this will determine the axis range and the range used in the fit.
    std::vector<float> fitRange = {90., 300.}; //GeV
    // TODO can you alter the function to allow us to rebin the histograms?
    
    // read in the signal and data histograms
    std::string sigHistPath = histPath + "allHiggs.root";
    TFile* sigFile = new TFile(sigHistPath.c_str(), "READ");
    std::string dataHistPath = histPath + "data.root";
    TFile* dataFile = new TFile(dataHistPath.c_str(), "READ");
    TH1F* sigHist = (TH1F*)sigFile->Get(variable.c_str());
    TH1F* dataHist = (TH1F*)dataFile->Get(variable.c_str());
    
    plotSigBgData(sigHist, dataHist, fitRange, plotPath, variable, blind, rangeToBlind);

    delete sigFile;
    delete dataFile;

}
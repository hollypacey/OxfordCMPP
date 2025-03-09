# Worked example analysis for the Higgs to diphoton discovery/exclusion fits, considering a variety of hypothesised Higgs masses.
# TODO: Head to the main function at the bottom, and comment everything out. 
#       Re-add each step one-by-one. Inspect each function as you go, try to understand what's happening. And look through the terminal outputs which have A LOT of info about what fit is happening, how well it is going, and what the results are.
#       Look at the new plots that are made at each stage to also understand the results of each fit.

# Run the script via:
#        python Fitting/part2_discoHiggs.py  -i histograms/GamGam_root/ -o plots/ -f poly4

# Based on: https://statisticalmethods.web.cern.ch/StatisticalMethods/ 
import argparse
import math
import numpy as np

import ROOT as r
from ROOT import TFile, RooRealVar, RooAbsData, RooFit, RooDataSet, RooArgSet, RooCBShape, RooDataHist, TCanvas, TLegend, RooArgList, RooExponential, RooExtendPdf, RooWorkspace, RooStats, TGraph

def plotResultsScan(results, var, plot_dir):
    """
    Function to plot the p0 values or significance for our null hypothesis vs massHiggs. Or the excluded upper limit mu_sig. will use right at the end. Sorry the plots are ugly!
    Args:
        results (dict): masses and the results for each
        var (str): p0, z0, mu_sig_hat, ExcUpperLim to plot.
    """
    fittype = "excl" if var=="ExcUpperLim" else "disco"
    c = TCanvas("discoresults", "discoresults", 600, 500)
    c.cd()
    masses = list(results.keys())
    npoints = len(masses)
    vals = [results[m][var] for m in masses]
    graph = TGraph(npoints, np.array(masses), np.array(vals))
    graph.SetTitle("Results of "+fittype+" fits;Hypothesised m(H) [GeV];"+var)
    graph.Draw("ALP")
    # draw a line at relevant value.
    line = r.TLine()
    line.SetLineColor(r.kBlue)
    y = 0.05 if var=="p0" else (5.0 if var=="Z0" else 1.0)
    line.DrawLine(masses[0], y, masses[npoints-1], y)
    c.SaveAs(plot_dir+fittype+"results_"+var+".png")


def signal_fit(sig_file, fit_range, range_to_blind, plot_dir, mH):
    """
    Function to fit our signal MC to a crystal ball function, and plot the result. 
    Aim is to check that this fit models our MC well so is a good choice, and to obtain the best-fit values.

    Args:
        sig_file (TFile): total signal MC histogram file.
        fit_range (list(floats)): min and max masses to consider for full search range.
        range_to_blind (list(floats): min and max masses to considier for signal fit.
        plot_dir (str): path to save plots to
        mH (float): Higgs mass hypothesis, should actually match the MC here.

    Returns:
        (float) nominal signal yield.
        (dict) best fit parameters
    """

    if (mH != 125.): raise Exception("need mH=125. if you want to fit to the MC!")

    diphoton_mass = RooRealVar("diphoton_mass", "$M(\gamma\gamma)$", fit_range[0], fit_range[1])

    # For the signal Higgs, use a crystal ball function to model the breit-wigner resonance shape.
    # We'll use the signal MC to set the overall size and fit the function to it.

    sig_hist = sig_file.Get("diphoton_mass")
    sig_rdhist = RooDataHist("sig_diphoton_mass",\
                             "sig_diphoton_mass",\
                             diphoton_mass,\
                             RooFit.Import(sig_hist))

    # crystal ball, setup with parameters - have to work out for yourself how to initialise
    mean = RooRealVar("mean","Mean of Gaussian CrystalBall", mH)
    sigma = RooRealVar("sigma","Width of gaussian component of CrystalBall", 2., 0., 20.)
    alpha = RooRealVar("alpha","powerlaw/Gaussian transition point CrystalBall", 1., -10., 10.)
    n = RooRealVar("n","exponent of power law", 100, 1, 200)

    sig_crystal = RooCBShape("sig_crystal","Crystalball",diphoton_mass, mean, sigma, alpha, n)

    # define range where fit is valid ie mH +- 5 GeV:
    diphoton_mass.setRange("signal", range_to_blind[0], range_to_blind[1])

    # Now fit our function to the signal MC
    sig_crystal.fitTo(sig_rdhist, RooFit.Range("signal"), RooFit.PrintLevel(0), RooFit.SumW2Error(True))

    # Return our fitted parameters:
    mass_h = mean.getVal()
    sigma_h = sigma.getVal()
    alpha_h = alpha.getVal()
    n_h = n.getVal()
    print("Fitted values: ")
    print('mass: {0:.3f}, sigma: {1:.3f}, alpha: {2:.3f}, n {3:.3f}'.format(mass_h, sigma_h, alpha_h, n_h))

    # Lets plot the fit result.
    # Draw all frames on a canvas
    c = TCanvas("signal_crystal_ball_fit", "signal crystal ball fit", 600, 500)
    c.cd()

    plot = diphoton_mass.frame(RooFit.Title("Signal Mass fit"))
    plot.SetTitle("")
    plot.GetYaxis().SetTitleOffset(1.)
    plot.GetYaxis().SetTitleSize(0.05)
    plot.GetXaxis().SetTitleSize(0.05)
    plot.GetXaxis().SetTitleOffset(.6)
    plot.SetXTitle(r"$M(\gamma\gamma)$ [GeV]")
    sig_rdhist.plotOn(plot, RooFit.Name("sig MC"), RooFit.DataError(RooAbsData.SumW2))
    sig_crystal.plotOn(plot, RooFit.Name("sig fit"), RooFit.Range(""))

    l = TLegend( 0.5, 0.6, 0.9, 0.9)
    mc_obj = plot.findObject("sig MC")
    fit_obj = plot.findObject("sig fit")

    # TODO it would be nice if the fitted function params were printed on the plot...
    l.AddEntry(mc_obj, "Higgs MC", "pl")
    l.AddEntry(fit_obj, "{0:0.1f} GeV Higgs mass Fit".format(mH), "l")
    l.SetTextSizePixels(400)
    plot.Draw()
    l.Draw()
    c.Draw()
    c.SaveAs(plot_dir + "signal_fit.png")

    # return the best-fit values and signal yield for later use.
    return sig_hist.Integral(), {"sigma":sigma_h, "alpha": alpha_h, "n": n_h}

def background_fit(data_file, fit_range, range_to_blind, plot_dir, func):
    """
    Function to fit our SM background (data outside the signal peak region) function, and plot the result. 
    Aim is to check that this fit models our MC well so is a good choice, and to obtain the best-fit parameters. 
    Can try exponential or polynomial versions

    Args:
        data_file (TFile): data histogram file.
        fit_range (list(floats)): min and max masses to consider for full search range.
        range_to_blind (list(floats): min and max masses to considier for signal fit.
        plot_dir (str): path to save plots to
        func (str): type of function to fit to: exp, poly2 or poly4

    Returns:
        (float) nominal background yield.
        (dict) best fit parameters
    """
    diphoton_mass = RooRealVar("diphoton_mass", "$M(\gamma\gamma)$", fit_range[0], fit_range[1])

    # define range where fit is valid:
    diphoton_mass.setRange("sideband-low", fit_range[0], range_to_blind[0])
    diphoton_mass.setRange("sideband-high", range_to_blind[1], fit_range[1])
    diphoton_mass.setRange("full", fit_range[0], fit_range[1])

    # Fit data region outside of Higgs mass window to an exponential fit.

    data_hist = data_file.Get("diphoton_mass").Clone("bg+")
    data_rdhist = RooDataHist("data_diphoton_mass",\
                             "data_diphoton_mass",\
                             diphoton_mass,\
                             RooFit.Import(data_hist))

    # define the bg fit function
    bestfit_val_dict = {}
    if func=="expo":
        lam = RooRealVar("lam", "decay rate of exponential", -0.5, -3., 0.)
        bg_func = RooExponential("bg_exp", "exponential decaying combinatorial background", diphoton_mass, lam)
        # Now fit our function to the data
        bg_func.fitTo(data_rdhist, RooFit.Range("sideband-low,sideband-high"), RooFit.PrintLevel(0), RooFit.SumW2Error(False))
        # print the best fit parameters:
        lam_h = lam.getVal()
        bestfit_val_dict["lambda"] = lam_h
        print("Fitted values: ")
        print('y = exp({0:.3f} x)'.format(lam_h))

    elif func=="poly4":
        coef_0 = RooRealVar("coef_0", "0th coefficient 4th order polynomial", 25000, 10000., 50000.)
        coef_1 = RooRealVar("coef_1", "1st coefficient 4th order polynomial", -300, -500, 0.)
        coef_2 = RooRealVar("coef_2", "2nd coefficient 4th order polynomial", 0, -1., 1.)
        coef_3 = RooRealVar("coef_3", "3rd coefficient 4th order polynomial", 0, -0.1, 0.1)
        coef_4 = RooRealVar("coef_4", "4th coefficient 4th order polynomial", 0, -0.01, 0.01)
        bg_func = r.RooPolynomial("bg_poly", "4Polynomial", diphoton_mass, RooArgList(coef_0, coef_1, coef_2, coef_3, coef_4))
        # Now fit our function to the data
        bg_func.fitTo(data_rdhist, RooFit.Range("sideband-low,sideband-high"), RooFit.PrintLevel(0), RooFit.SumW2Error(False))
        # print the best-fit parameters
        coef_0_h = coef_0.getVal()
        coef_1_h = coef_1.getVal()
        coef_2_h = coef_2.getVal()
        coef_3_h = coef_3.getVal()
        coef_4_h = coef_4.getVal()
        bestfit_val_dict["coef_0"] = coef_0_h
        bestfit_val_dict["coef_1"] = coef_1_h
        bestfit_val_dict["coef_2"] = coef_2_h
        bestfit_val_dict["coef_3"] = coef_3_h
        bestfit_val_dict["coef_4"] = coef_4_h
        print("Fitted values: ")
        print('y =  {0:.3f} + {1:.3f}m + {2:.3f}m^2 + {3:.3f}m^3 + {4:.3f}m^4'.format(coef_0_h, coef_1_h, coef_2_h, coef_3_h, coef_4_h))

    elif func=="poly2":
        coef_0 = RooRealVar("coef_0", "0th coefficient 4th order polynomial", 12000, 8000., 20000.)
        coef_1 = RooRealVar("coef_1", "1st coefficient 4th order polynomial", -120, -500, 0.)
        coef_2 = RooRealVar("coef_2", "2nd coefficient 4th order polynomial", 0.4, -1., 1.)
        bg_func = r.RooPolynomial("bg_poly", "4Polynomial", diphoton_mass, RooArgList(coef_0, coef_1, coef_2))
        # Now fit our function to the data
        bg_func.fitTo(data_rdhist, RooFit.Range("sideband-low,sideband-high"), RooFit.PrintLevel(0), RooFit.SumW2Error(False))
        # print the best-fit parameters
        coef_0_h = coef_0.getVal()
        coef_1_h = coef_1.getVal()
        coef_2_h = coef_2.getVal()
        bestfit_val_dict["coef_0"] = coef_0_h
        bestfit_val_dict["coef_1"] = coef_1_h
        bestfit_val_dict["coef_2"] = coef_2_h
        print("Fitted values: ")
        print('y =  {0:.3f} + {1:.3f}m + {2:.3f}m^2'.format(coef_0_h, coef_1_h, coef_2_h))

    else:
        raise Exception(func + " not supported, implemented it yourself or change to expo, poly4 or poly2")

    # Draw all frames on a canvas
    c = TCanvas("background_" + func + "_fit", "background " + func + " fit", 600, 500)
    c.cd()

    plot = diphoton_mass.frame(RooFit.Title("Background fit"))
    plot.SetTitle("")
    plot.GetYaxis().SetTitleOffset(1.)
    plot.GetYaxis().SetTitleSize(0.05)
    plot.GetXaxis().SetTitleSize(0.05)
    plot.GetXaxis().SetTitleOffset(.6)
    plot.SetXTitle(r"$M(\gamma\gamma)$ [GeV]")
    data_rdhist.plotOn(plot, RooFit.Name("data"), RooFit.DataError(RooAbsData.SumW2))
    bg_func.plotOn(plot, RooFit.Name("bg fit"), RooFit.Range("sideband-low,sideband-high"))

    l = TLegend( 0.5, 0.6, 0.9, 0.9)
    data_obj = plot.findObject("data")
    bgfit_obj = plot.findObject("bg fit")

    l.AddEntry(data_obj, "data", "pl")
    l.AddEntry(bgfit_obj, "background " + func + " fit", "l")
    l.SetTextSizePixels(400)
    plot.Draw()
    l.Draw()
    c.Draw()
    c.SaveAs(plot_dir + "bg_fit.png")



    # return the overall bg yield and best-fit values for later use.
    return data_hist.Integral(data_hist.FindBin(fit_range[0]), data_hist.FindBin(fit_range[1])), bestfit_val_dict


def build_model(data_file, fit_range, range_to_blind, plot_dir, mH, nSig_predicted, sig_cb_params, nBg_predicted, bg_fit_params, func):
    """
    Function to take our defined signal and background models (ended over the blinded range), and data. Builds our likelihood expression for predicted and observed yields, and the PDFs that goven the signal/bg predictions, defines a workspace to hold this info. fits the likelihood to data to find the best fit values.

    Args:
        data_file (TFile): data histogram file.
        fit_range (list(floats)): min and max masses to consider for full search range.
        range_to_blind (list(floats): min and max masses to considier for signal fit.
        plot_dir (str): path to save plots to
        mH (float): Higgs mass hypothesis, should actually match the MC here.
        nSig_predicted (float): nominal predicted signal yield from MC (scaled a bit if we use a different mH)
        sig_cb_params (dict): the best-fit crystal ball parameters for our signal fit
        nBg_predicted (float): nominal predicted background yield, just taken from data in this example.RooExponential
        bg_fit_params (dict): the best-fit parameters for our bg fit.background_fit
        func (str): type of function to fit to: exp, poly2 or poly4

    Return:
        (RooWorkspace) our full likelihood model workspace :)
        (RooDataHist) our data
        (float) our best fit mu_sig value (mu_sig_hat)
    """

    diphoton_mass = RooRealVar("diphoton_mass", "$M(\gamma\gamma)$", fit_range[0], fit_range[1])
    # define range where signal fit is valid:
    diphoton_mass.setRange("signal", range_to_blind[0], range_to_blind[1])
    # define range where background fit is valid:
    diphoton_mass.setRange("sideband-low", fit_range[0], range_to_blind[0])
    diphoton_mass.setRange("sideband-high", range_to_blind[1], fit_range[1])
    # full range to consider in our analysis:
    diphoton_mass.setRange("full", fit_range[0], fit_range[1])

    # For the signal Higgs, use a crystal ball function to model the breit-wigner resonance shape.
    # We use the best-fit parameters of the function from the earlier MC fit.
    # We will later use our nSig_predicted from MC to set our nominal predicted signal yield to scale the function.
    mean = RooRealVar("mean","Mean of Gaussian CrystalBall", mH)
    sigma = RooRealVar("sigma","Width of gaussian component of CrystalBall", sig_cb_params["sigma"])
    alpha = RooRealVar("alpha","powerlaw/Gaussian transition point CrystalBall", sig_cb_params["alpha"])
    n = RooRealVar("n","exponent of power law", sig_cb_params["n"])

    sig_crystal = RooCBShape("sig_crystal","Crystalball",diphoton_mass, mean, sigma, alpha, n)

    # Read in the actual data to test (and use in our bg estimate).
    obsdata_hist = data_file.Get("diphoton_mass").Clone("data")
    #obsdata_hist = obsdata_hist.Rebin(2)
    data_rdhist = RooDataHist("data_diphoton_mass",\
                             "data_diphoton_mass",\
                             diphoton_mass,\
                             RooFit.Import(obsdata_hist))

    # Now move on to building background model.
    if func=="expo":
        lam = RooRealVar("lam", "decay rate of exponential", bg_fit_params["lambda"])
        bg_func = RooExponential("bg_exp", "exponential decaying combinatorial background", diphoton_mass, lam)
    elif func=="poly4":
        coef_0 = RooRealVar("coef_0", "0th coefficient 4th order polynomial", bg_fit_params["coef_0"])
        coef_1 = RooRealVar("coef_1", "1st coefficient 4th order polynomial", bg_fit_params["coef_1"])
        coef_2 = RooRealVar("coef_2", "2nd coefficient 4th order polynomial", bg_fit_params["coef_2"])
        coef_3 = RooRealVar("coef_3", "3rd coefficient 4th order polynomial", bg_fit_params["coef_3"])
        coef_4 = RooRealVar("coef_4", "4th coefficient 4th order polynomial", bg_fit_params["coef_4"])
        bg_func = r.RooPolynomial("bg_poly", "4Polynomial", diphoton_mass, RooArgList(coef_0, coef_1, coef_2, coef_3, coef_4))
    elif func=="poly2":
        coef_0 = RooRealVar("coef_0", "0th coefficient 4th order polynomial", bg_fit_params["coef_0"])
        coef_1 = RooRealVar("coef_1", "1st coefficient 4th order polynomial", bg_fit_params["coef_1"])
        coef_2 = RooRealVar("coef_2", "2nd coefficient 4th order polynomial", bg_fit_params["coef_2"])
        bg_func = r.RooPolynomial("bg_poly", "4Polynomial", diphoton_mass, RooArgList(coef_0, coef_1, coef_2))
    else:
        raise Exception(func + " not supported, implemented it yourself or change to expo or poly4")

    # Set background prediction to a freely floating value: note we just define an expected range for the bg to help the fit converge, based on it being either slightly less than data (if the data contains signal) or the same. In a real analysis you'd either fix this via the prediction/MC, or have some scaling of the MC as a free NP in the fit.
    nBg = RooRealVar("nBg", "n fitted bg", nBg_predicted, nBg_predicted*0.99, nBg_predicted)

    # form extended pdf of n-events over full range (fit in the defined low/high range but then extrapolate beyond it to 'full' automatically.)
    eBg = RooExtendPdf("eBg", "eBg", bg_func, nBg, "full")
    eBg.fitTo(data_rdhist, RooFit.Range("sideband-low,sideband-high"))

    # a parameter for the "theoretical" predicted event counts is defined
    nBg_SM = RooRealVar("nBg_SM","Fitted number of background events", int(nBg.getVal())) # best fit value from above fit.
    # Set signal prediction based on our MC yield, calculated in the signal_fit function.
    nSig = RooRealVar("nSig", "n pred sig", nSig_predicted)
    print("Predicted yields: bg=",nBg.getVal(), ", sig=", nSig.getVal())
    nSig_SM = RooRealVar("nSig_SM","predicted number of signal events", int(nSig.getVal()))

    ##===========================================================================================================
    # define the Root workspace to contain the model
    w = RooWorkspace("diphoton_mass_Higgs_disco")

    # define our signal and background PDF shapes, and the nominal counts.
    getattr(w, "import")(sig_crystal)
    getattr(w, "import")(bg_func)
    getattr(w, "import")(nBg_SM)
    getattr(w, "import")(nSig_SM)

    # Now set the 'expected' yield part of our Poisson to go into our Likelihood
    # expression for expected signal yield = signal strength mu_sig * our predicted signal yield from the crystal ball fit. Multiply by our signal crystal PDF.
    # expression for expected background yield = our predicted bg yield from the exponential fit. Multiply by our bg function PDF.
    # the SUM gives our total expected yield = expected signal yield + expected background yield
    w.factory("SUM::model(expr::nsig('mu_sig*nSig_SM', mu_sig[1, 0, 5], nSig_SM)*sig_crystal, expr::nbg('nBg_SM', nBg_SM)*bg_poly)")

    # what is the observed data to compare to our expectation, in the Poisson in our likelihood?
    # feed in data mGamGam histogram.
    getattr(w, "import")(data_rdhist, RooFit.Rename("observed_data"))

    # What does this roostats workspace look like?
    print("This is our RooWorkspace: ")
    w.Print("t")

    # save the workspace to a file
    w.writeToFile("diphoton_mass_Higgs_disco_ws_" + str(int(mH)) + ".root")

    ##===========================================================================================================
    # total PDF = our likelihood expression.
    # Now lets fit our likleihood to data to get the 'best fit' values.
    pdf = w.pdf("model")
    pdf.fitTo(data_rdhist)

    # Draw fit result on a canvas
    c = TCanvas("data_fit", "data fit", 600, 500)
    c.cd()
    mframe = diphoton_mass.frame(RooFit.Title("diphoton_mass_Higgs_disco"))
    data_rdhist.plotOn(mframe)
    pdf.plotOn(mframe)
    mframe.Draw()
    c.SaveAs(plot_dir+"data_fit_" + str(int(mH)) + ".png")

    mu_sig_best = w.var("mu_sig").getVal()
    print("Best fit signal strength? ", mu_sig_best)
    # Note we could then use this to get a best-fit estimate of the Higgs cross section, for example.
    
    # return the workspace we made for hypothesis testing...
    return w, data_rdhist, mu_sig_best


def discovery_test(w, data_rdhist):
    """
    Function to do the discovery hypothesis test to evaluate our discovery sensitivity.
    
    Args:
        w (RooWorkspace): containing our complete model.
        data_rdhist (RooDataHist): our data

    Returns:
        (dict) our p0, Z0 values.
    """
    pdf = w.pdf("model")
    #pdf.fitTo(data_rdhist)

    # Use this 'model config' to establish our signal+background and background-only hypotheses
    mod_conf = RooStats.ModelConfig("ModelConfig", w)
    mod_conf.SetPdf(pdf)
    mod_conf.SetParametersOfInterest(RooArgSet(w.var("mu_sig")))
    mod_conf.SetObservables(RooArgSet(w.var("diphoton_mass")))
    # define set of nuisance parameters.. well if we had systmatics that would be here. in this example there's nothing to add, unless we implemented uncertainties on our sig/bg functional form fit choices.

    # import the ModelConfig in the workspace
    getattr(w, "import")(mod_conf)

    # Get the signal+background model hypothesis, this is where we have the nominal signal yield i.e. mu_sig==1
    sb_model = mod_conf.Clone()
    sb_model.SetName("Sig+Bg Model")
    poi = sb_model.GetParametersOfInterest().first()
    poi.setVal(1)
    sb_model.SetSnapshot(RooArgSet(poi)) # fix mu_sig at one for this model.

    # Get the background-only model hypothesis, this is where we have the no signal yield i.e. mu_sig==0
    b_model = sb_model.Clone() # copy from the sb model to start with
    b_model.SetName("Bg Model")
    poi.setVal(0)
    b_model.SetSnapshot(RooArgSet(poi)) # fix mu_sig at zero for this model.

    ##===========================================================================================================
    # Now lets do a one-sided discovery test to see if we can exclude the bg-only model! Note we'll use the Asymptotic formula here instead of throwing Toys (https://arxiv.org/abs/1007.1727)
    # Define a hypothesis test which sets the NULL hypothesis to be our b-only model (which we try to reject), and the ALT hypothesis as s+b. 
    as_calc_disc = RooStats.AsymptoticCalculator(data_rdhist, sb_model, b_model)
    as_calc_disc.SetOneSidedDiscovery(True)
    as_result_disc = as_calc_disc.GetHypoTest()
    print("Here's the result of our hypothesis testing:")
    as_result_disc.Print()

    # Can also retrieve our results as so:
    p0 = as_result_disc.NullPValue()
    Z0 = as_result_disc.Significance()
    if (p0<0.05): print("ooh you can exclude the background-only hypothesis at 95% CL")
    if (Z0>5): print("congratulations, you've discovered a particle with mass {:.1f} GeV !".format(mH))

    # return our hypothesis test results
    return {"p0": p0, "Z0": Z0}



def exclusion_test(w, data_rdhist, plot_dir):
    """
    If relevant, lets do an exclusion fit to see if we can exclude our nominal model. 
    And if we can set an upper limit on the allowed signal strength multiplier (which could be translated unto an upper limit on the cross_section)
     (i.e. if the upper limit is mu_sig=3 then our nominal signal model IS NOT excluded, we have only excluded other models that give the same kinematics but a cross section > 3x our prediction. )
     (i.e. if the upper limit is mu_sig=0.2 then our nominal signal model IS excluded, we have excluded other models that give the same kinematics but a cross section >0.2x our prediction. )

    Args:
        w (RooWorkspace): containing our complete model.
        data_rdhist (RooDataHist): our data

    Returns:
        (float): mu_sig upper limit value
    """

    # Now we can do the hypothesis test to evaluate our discovery/exclusion sensitivity.
    # Use this 'model config' to establish our signal+background and background-only hypotheses
    mod_conf = RooStats.ModelConfig("ModelConfig", w)
    pdf = w.pdf("model")
    mod_conf.SetPdf(pdf)
    mod_conf.SetParametersOfInterest(RooArgSet(w.var("mu_sig")))
    mod_conf.SetObservables(RooArgSet(w.var("diphoton_mass")))
    # define set of nuisance parameters.. well if we had systmatics that would be here. in this example there's nothing to add, unless we implemented uncertainties on our sig/bg functional form fit choices.

    # import the ModelConfig in the workspace
    getattr(w, "import")(mod_conf)

    # Get the signal+background model hypothesis, this is where we have the nominal signal yield i.e. mu_sig==1
    sb_model = mod_conf.Clone()
    sb_model.SetName("Sig+Bg Model")
    poi = sb_model.GetParametersOfInterest().first()
    poi.setVal(1)
    sb_model.SetSnapshot(RooArgSet(poi)) # fix mu_sig at one for this model.

    # Get the background-only model hypothesis, this is where we have the no signal yield i.e. mu_sig==0
    b_model = sb_model.Clone() # copy from the sb model to start with
    b_model.SetName("Bg Model")
    poi.setVal(0)
    b_model.SetSnapshot(RooArgSet(poi)) # fix mu_sig at zero for this model.

    # Okay so if p0>0.05, we haven't excluded the bg-only (no Higgs) hypothesis or discovered the signal..... Can we exclude the sig+bg hypothesis instead then?
    # Define an 'Inverter' hypothesis test which now sets the NULL hypothesis to be our s+b model (which we try to reject), and the ALT hypothesis as b-only, 
    # We can scan over different mu_sig values to see at what signal strength we can exclude the signal.
    as_calc_exc = RooStats.AsymptoticCalculator(data_rdhist, b_model, sb_model)
    as_calc_exc.SetOneSided(True)
    as_result_exc = as_calc_exc.GetHypoTest()
    print("Here's the result of our inverted hypothesis testing:")
    as_result_exc.Print()
    inv_calc = RooStats.HypoTestInverter(as_calc_exc)
    inv_calc.SetConfidenceLevel(0.95)
    inv_calc.UseCLs(True)
    inv_calc.SetVerbose(True)
    npoints = 41
    poimin = poi.getMin()
    poimax = poi.getMax()
    inv_calc.SetFixedScan(npoints, poimin, poimax)
    inv_result = inv_calc.GetInterval()
    inv_plot = RooStats.HypoTestInverterPlot("HTI_Result_Plot", "Feldman-Cousins Interval", inv_result)

    c2 = TCanvas("HypoTestInverter Scan", "HypoTestInverter Scan", 800, 600)
    c2.cd()
    inv_plot.Draw("CLb 2CL")
    c2.SaveAs("{0}HypoTestInverterScan_{1:.0f}.png".format(plot_dir,mH))

    obs_limit = inv_result.UpperLimit()
    obs_err = inv_result.UpperLimitEstimatedError()
    print("The computed upper limit is: {0:.3f} +/- {1:.3f}".format(obs_limit, obs_err))

    return obs_limit



#_____________________________________________________________________________
if __name__ == "__main__":

    # setup command line arguments for our input and output files.
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--hist_path", help="input histogram path", default="")
    parser.add_argument("-o", "--plot_path", help="output path dir", default="")
    parser.add_argument("-f", "--bg_func", help="functional form for bg fit", default="")

    args = parser.parse_args()

    hist_path = args.hist_path
    plot_path = args.plot_path
    bg_func = args.bg_func

    # read in the signal and data histograms
    sig_file = TFile(hist_path + "allHiggs.root", "READ")
    data_file = TFile(hist_path + "data.root", "READ")
    
    mH = 125.
    #this will determine the axis range and the range used in the fit.
    fit_range = [110., 160.] #GeV
    # want to blind the signal part of the fit in any case so we don't fit the background to bits of data that might have signal in.
    range_to_blind = [mH-5., mH+5] #GeV

    ## First we want to check our choices for functional form fits to parametrise the signal and background distribution:
    nSig_predicted, sig_cb_bestfit_params = signal_fit(sig_file, fit_range, range_to_blind, plot_path, mH)
    #print(nSig_predicted)
    nSig_predicted = 373.246



    # Then we want to 
    #  (1) define the expected signal and background PDFs
    #  (2) define our likelihood form.
    #  (3) define our 'parameter of interest' in the fit as the signal_strength multiplying our nominal predicted signal
    #  (4) fit our likelihood to observed data to get the 'best-fit' values
    #  (5) define our signal+background and background-only hypotheses
    #  (6) perform a 'discovery fit' to see if we can reject our background-only hypothesis.
    # Nominally we do this for our mH=125. value that we have MC for, to see if we can discover the actual Higgs boson,
    # But we can ALSO imagine we don't yet know what mH is, and scan over different values (ie shifting our crystal ball signal model along the mGamGam) to see how the results of our hypothesis test change...
    results = {}
    masses = [115., 120., 125., 130., 135., 140., 145., 150., 155.]
    for mH in masses:
        # Range to use for the signal fit and blind in the bg fit.
        #range_to_blind = [mH-5., mH+5.] #GeV
        nBg_predicted, bg_bestfit_params = background_fit(data_file, fit_range, range_to_blind, plot_path, bg_func)
        #nBg_predicted = 42382.12

        # very approximate to account for lighter higgses having a larger production xsecion
        xsec_scale = math.exp(1 - (mH/125.)**2)
        nSig_predicted_tmp = nSig_predicted*xsec_scale
        print(mH,xsec_scale,nSig_predicted_tmp)

        # Build the statistical workspace and likelihood model for our signal hypothesis and background model. Get the best-fit values.
        workspace, data_rdhist, mu_sig_hat = build_model(data_file, fit_range, range_to_blind, plot_path, mH, nSig_predicted_tmp, sig_cb_bestfit_params, nBg_predicted, bg_bestfit_params, bg_func)
        
        # Perform a discovery test, atttempting to reject our background-only hypothesis so we can discover the Higgs.
        results[mH] = discovery_test(workspace, data_rdhist)

        results[mH]["mu_sig_hat"] = mu_sig_hat
        # if we didn't reject the background-only hypothesis before (ie we got p0>0.05), we can instead perform an exclusion test to see if we can reject the signal+background hypothesis, and set an upper limit on the possible allowed signal hypothesis signal strength.
        results[mH]["ExcUpperLim"] = exclusion_test(workspace, data_rdhist, plot_path)

    # plot the disco fit results nicely
    plotResultsScan(results, "p0", plot_path)
    plotResultsScan(results, "Z0", plot_path)
    plotResultsScan(results, "mu_sig_hat", plot_path)
    plotResultsScan(results, "ExcUpperLim", plot_path)

    print(results)

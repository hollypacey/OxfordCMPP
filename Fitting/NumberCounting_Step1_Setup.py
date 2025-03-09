import ROOT, os

# Questions
# 1) What is the likelihood here (in the absence of systematics)?
# 2) What are the NPs here?
# 3) What do we want to measure?

os.makedirs('./workspaces/NumberCounting',exist_ok = True)

# Defining the dataset

S = 5.7 # Signal
B = 8.9 # Background
O = 18  # Observed data

# Creating the histograms
hS = ROOT.TH1D("S", "S", 1, 0, 1)
hB = ROOT.TH1D("B", "B", 1, 0, 1)
hO = ROOT.TH1D("O", "O", 1, 0, 1)

# Assigning event yields to histograms
hS.SetBinContent(1, S)
hB.SetBinContent(1, B)
hO.SetBinContent(1, O)

c = ROOT.TCanvas("")
s = ROOT.THStack("stack", "Event Yields")
hB.SetLineColor(ROOT.kBlue)
hB.SetFillColor(ROOT.kBlue)
s.Add(hB)
hS.SetLineColor(ROOT.kRed)
hS.SetFillColor(ROOT.kRed)
s.Add(hS)
hO.SetLineColor(ROOT.kBlack)
hO.SetMinimum(0)

hO.Draw("same E0")
s.Draw("hist same")
c.Draw()

c.SaveAs("hist_counts.png")

# Creating HistFactory model
meas = ROOT.RooStats.HistFactory.Measurement("NumberCounting", "NumberCounting")
meas.SetOutputFilePrefix("workspaces/NumberCounting/ws")
meas.SetExportOnly(1)
meas.SetPOI("mu") # Setting Parameter Of Interest (POI)

meas.SetLumi(1.0)
meas.SetLumiRelErr(0.019) # Typical uncertainty on integrated luminosity at LHC Run-2


# Creating the parameters of the model

muS = ROOT.RooStats.HistFactory.NormFactor()
muS.SetName("mu")
muS.SetHigh(100)    # Highest possible value in fit
muS.SetLow(0)       # Lowest possible value in fit
muS.SetVal(1)       # Nominal value

# Creating the Signal Region (SR)
SR = ROOT.RooStats.HistFactory.Channel("SR")
SR.SetData(hO) # Assigning the observed events as data

# Adding the signal and background samples

sS = ROOT.RooStats.HistFactory.Sample("S")
sS.SetHisto(hS)
sS.AddNormFactor(muS)
SR.AddSample(sS)

sB = ROOT.RooStats.HistFactory.Sample("B")
sB.SetHisto(hB)
SR.AddSample(sB)

meas.AddChannel(SR)

meas.PrintTree()

ROOT.RooStats.HistFactory.MakeModelAndMeasurementFast(meas)

oF = ROOT.TFile.Open("./workspaces/NumberCounting/ws_combined_NumberCounting_model.root")
oF.ls()

ws = oF.Get("combined")
ws.Print()

ws.data("obsData").Print()

ws.set("ModelConfig_NuisParams").Print("v")

ws.set("ModelConfig_POI").Print("v")

ws.pdf("simPdf").Print("")

ws.pdf("simPdf").Print("v")

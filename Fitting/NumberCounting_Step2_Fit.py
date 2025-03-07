import ROOT

oF = ROOT.TFile.Open("./workspaces/NumberCounting/ws_combined_NumberCounting_model.root")
oF.ls()

# Reading in the workspace
ws = oF.Get("combined")

# Reading in the elements needed for the fit
mu = ws.var("mu")
pdf = ws.pdf("simPdf")
sbModel = ws.obj("ModelConfig")
data = ws.data("obsData")
asimov = ws.data("asimovData")

# Configuring Minuit
ROOT.Math.MinimizerOptions.SetDefaultMinimizer("Minuit2")
ROOT.Math.MinimizerOptions.SetDefaultStrategy(0)
ROOT.Math.MinimizerOptions.SetDefaultPrintLevel(1)

# Create a single set containing NP and POI to feed negative log-likelihood (NLL)
params = ROOT.RooArgSet( sbModel.GetNuisanceParameters(), sbModel.GetParametersOfInterest() )

# Build negative log-likelihood (NLL)
theData = data
nll = pdf.createNLL( theData, ROOT.RooFit.Constrain(params), ROOT.RooFit.GlobalObservables(sbModel.GetGlobalObservables()), ROOT.RooFit.Offset(1) )

# Helper function to perform the fit
def minimize(fcn, save = False, retry_mode = 3):
  printLevel = ROOT.Math.MinimizerOptions.DefaultPrintLevel()
  msgLevel = ROOT.RooMsgService.instance().globalKillBelow()
  if printLevel < 0:
      ROOT.RooMsgService.instance().globalKillBelow(ROOT.RooFit.FATAL)

  strategy = ROOT.Math.MinimizerOptions.DefaultStrategy()
  save_def_strategy = strategy

  minimizer = ROOT.RooMinimizer(fcn)
  minimizer.optimizeConst(2)
  minimizer.setStrategy(strategy)
  minimizer.setPrintLevel(printLevel)
  minimizer.setMinimizerType(ROOT.Math.MinimizerOptions.DefaultMinimizerType())

  status = minimizer.minimize( ROOT.Math.MinimizerOptions.DefaultMinimizerType(), ROOT.Math.MinimizerOptions.DefaultMinimizerAlgo() )

  # Possibly re-trying if the fit didn't work
  if retry_mode == 0:
    if status != 0 and status != 1 and strategy < 2:
      strategy += 1
      logger.warning( f"Fit failed with status {status}. Retrying with strategy {strategy}" )
      minimizer.setStrategy(strategy)
      status = minimizer.minimize( ROOT.Math.MinimizerOptions.DefaultMinimizerType(), ROOT.Math.MinimizerOptions.DefaultMinimizerAlgo() )

    if status != 0 and status != 1 and strategy < 2:
      strategy += 1
      logger.warning( f"Fit failed with status {status}. Retrying with strategy {strategy}" )
      minimizer.setStrategy(strategy)
      status = minimizer.minimize( ROOT.Math.MinimizerOptions.DefaultMinimizerType(), ROOT.Math.MinimizerOptions.DefaultMinimizerAlgo() )

  else:
    for i in range(retry_mode):
      if status == 0 or status == 1: break
      logger.warning( f"Fit failed with status {status}. Retrying with strategy {strategy}." )
      minimizer.setStrategy(strategy)
      status = minimizer.minimize( ROOT.Math.MinimizerOptions.DefaultMinimizerType(), ROOT.Math.MinimizerOptions.DefaultMinimizerAlgo() )

  if printLevel < 0:
    ROOT.RooMsgService.insurance().setGlobalKillerBelow(msgLevel)
  ROOT.Math.MinimizerOptions.SetDefaultStrategy(save_def_strategy)

  if save:
    fitRes = minimizer.save( f"fitresult_{fcn.GetName()}", f"fitresult_{fcn.GetName()}" )
    return fitRes

res = minimize(nll, True, 0)
res.SaveAs("result.root")

# Exercises
# 1) What are the results you get and how do you interpret them?
# 2) Try runing the fit using the Asimov dataset ; what do you get for mu ?
# 3) Adjust the number of signal and background events (in step 1), re-run the fit and confirm that it behaves as you'd expect
# 4) Adjust the prior constraint on the lumi ; what do you get for mu?
# 5) What happens if you get 100 times more data (and accordingly expected signal and background)?
# 6) (Bonus) add an uncertainty on the background normalisation of 20% ; what happens?

import ROOT
import numpy as np

oF = ROOT.TFile.Open("./workspaces/NumberCounting/ws_combined_NumberCounting_model.root")
oF.ls()

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

def scanLikelihood(ws, parName="mu", scan_range=2, nPts=20, dataName = "obsData"):
    # Reading in the elements needed for the fit
    mu = ws.var("mu")
    pdf = ws.pdf("simPdf")
    sbModel = ws.obj("ModelConfig")
    theData = ws.data(dataName)

    # Create a single set containing NP and POI to feed negative log-likelihood (NLL)
    params = ROOT.RooArgSet( sbModel.GetNuisanceParameters(), sbModel.GetParametersOfInterest() )
    par = ws.var(parName)
    if not par:
      print(f"ERROR: Parameter {parName} doesn't exist")
      return

    # Configuring Minuit
    ROOT.Math.MinimizerOptions.SetDefaultMinimizer("Minuit2")
    ROOT.Math.MinimizerOptions.SetDefaultStrategy(0)
    ROOT.Math.MinimizerOptions.SetDefaultPrintLevel(1)

    # Ensure all parameters are floating freely

    for v in params:
      print(v)
      v.setConstant(0)

    nll = pdf.createNLL( theData, ROOT.RooFit.Constrain(params), ROOT.RooFit.GlobalObservables(sbModel.GetGlobalObservables()), ROOT.RooFit.Offset(1) )

    # Performing unconditional fit (all parameters floating)
    minimize(nll)

    # Saving the value of the NLL at the best fit value
    nll_best = nll.getVal()
    mu_hat = par.getVal()

    print(f"nll_best = {nll_best} ; mu_hat = {mu_hat}")

    # Storing values for plotting
    x_array, y_array = np.zeros(nPts+1), np.zeros(nPts+1)
    print(x_array)
    cnt = 0
    passedMin = False # Variable to check whether minimum was passed
    for i in range(0,nPts):
        val = mu_hat - scan_range + 2 * scan_range * i / (nPts - 1)
        print(i, val)

        if val > mu_hat and not passedMin:
            passedMin = True
            x_array[cnt] = mu_hat
            y_array[cnt] = 0
            cnt += 1

        # Fix the parameter to its point in the scan and fit
        par.setVal(val)
        print(par)
        par.setConstant(1)
        minimize(nll)

        # Saving -2log(L(par/L(par_hat))
        dnllx2 = 2*(nll.getVal()-nll_best)
        x_array[cnt] = val
        y_array[cnt] = dnllx2
        cnt += 1
        print(f"[{i+1} of {nPts}] {parName} = {val}, -2lnLambda = {dnllx2} (best fit = {mu_hat})")

    return x_array, y_array, parName, scan_range, mu_hat

# Helper for drawing
def drawLikelihoodScan(x_array, y_array, parName, scan_range, mu_hat):
    c = ROOT.TCanvas(f"Likelihood Scan {parName} (scan_range = {scan_range})")
    # Plotting the result
    g = ROOT.TGraph(len(x_array), x_array, y_array)
    g.SetTitle("Likelihood Scan")
    g.Draw("ALP*")
    g.GetXaxis().SetTitle(parName)
    g.GetYaxis().SetTitle("-2 ln #Lambda")
    g.Draw("LP*")

    l = ROOT.TLine()
    l.SetLineStyle(2)
    l.SetLineWidth(2)
    l.SetLineColor(ROOT.kRed)
    l.DrawLine(mu_hat-scan_range, 1 ,mu_hat+scan_range, 1)
    l.SetLineColor(ROOT.kBlue)
    l.DrawLine(mu_hat-scan_range, 4 ,mu_hat+scan_range, 4)

    c.Draw()
    c.Print(".png")
    return c.Clone()

# Reading in the workspace
ws = oF.Get("combined")

x_array, y_array, parName, scan_range, mu_hat = scanLikelihood(ws)

c = drawLikelihoodScan(x_array, y_array, parName, scan_range, mu_hat)
c.Draw()

x_array, y_array, parName, scan_range, mu_hat = scanLikelihood(ws, "Lumi", 0.04, 20)

c = drawLikelihoodScan(x_array, y_array, parName, scan_range, mu_hat)
c.Draw()

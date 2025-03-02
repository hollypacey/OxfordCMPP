./part1_process_TTree_root ggfHiggs
./part1_process_TTree_root VBFHiggs
./part1_process_TTree_root data
hadd -f histograms/GamGam_rootCpp/allHiggs.root histograms/GamGam_rootCpp/ggfHiggs.root histograms/GamGam_rootCpp/VBFHiggs.root

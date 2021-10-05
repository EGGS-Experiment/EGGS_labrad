import labrad
from Qsim.abstractdevices.script_scanner.scan_methods import experiment

class fft_spectrum(experiment):
    
    name = 'FFT Spectrum'
    required_parameters = []
    
    def initialize(self, cxn, context, ident):
        print('init')
        
    def run(self, cxn, context):
        print('running')
            
    def finalize(self, cxn, context):
        print('finalize')

class conflicting_experiment(fft_spectrum):
    
    name = 'conflicting_experiment'
    required_parameters = [
                           ('TrapFrequencies','axial_frequency')
                           ]
        
class non_conflicting_experiment(fft_spectrum):
    
    name = 'non_conflicting_experiment'
        
class crashing_example(fft_spectrum):
    
    name = 'crashing_example'

    def initialize(self, cxn, context, ident):
        print('in initialize', self.name(), ident)
        raise Exception ("In a case of a crash, real message would follow")

if __name__ == '__main__':
    #normal way to launch
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = fft_spectrum(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
    #testing single launch
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    from scan_methods import single
    exprt = single(fft_spectrum)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
    #testing repeat launch
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    from scan_methods import repeat_reload
    exprt = repeat_reload(fft_spectrum, 10)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
    #testing scan
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    from scan_methods import scan_experiment_1D
    exprt = scan_experiment_1D(fft_spectrum, ('TrapFrequencies', 'rf_drive_frequency'), 10.0, 20.0, 10, 'MHZ') 
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
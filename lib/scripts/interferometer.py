import labrad
import numpy as np

from *** import experiment

class interferometer(experiment):

    '''
    Takes scope trace and FFTs it, then stores both
    '''

    name = 'MM Compensation'

    exp_parameters = []
    exp_parameters.append(('MMCompensation', 'center_frequency'))
    exp_parameters.append(('MMCompensation', 'cycles'))
    exp_parameters.append(('MMCompensation', 'frequency_offset'))
    exp_parameters.append(('MMCompensation', 'frequency_span'))

    def initialize(self, cxn, context, ident):
        '''
        implemented by the subclass
        '''

    def run(self, cxn, context, replacement_parameters={}):
        '''
        implemented by the subclass
        '''

    def finalize(self, cxn, context):
        '''
        implemented by the subclass
        '''

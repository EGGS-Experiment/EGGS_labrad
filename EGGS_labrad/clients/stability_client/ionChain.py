import numpy as np
# todo: move all wsec calc here

"""
Constants, fundamental and derived
"""
_QE = 1.60217e-19
_AMU = 1.66053904e-27
_HBAR = 1.05457182e-34
_KE2 = 2.30707751e-28
_wkhz = 2 * np.pi * 1e3
_wmhz = 2 * np.pi * 1e6


"""
Helper functions
"""
def axial_secular_frequency():
    """
    Calculate the axial secular frequency of an ion.
    Returns:

    """
    pass


"""
Objects
"""
class ionObject(object):
    """
    Represents an ion within an ion chain.
    """

    def __init__(self, mass):
        """
        Create all chain-related variables here.
        """
        self.mass = mass
        self.position = 0
        self.secular_axial = 0
        self.secular_radial = 0


class ionChain(object):
    """
    An object for calculating normal mode data.
    """

    def __init__(self,
                 v_rf=0, w_rf=0, k_rf=1, r0=0,
                 v_dc=0, k_dc=1, z0=0
                 ):
        """
        Create all chain-related variables here.
        """
        # ion variables
        self.ions = {}
        # trap variables
        self.v_rf = v_rf
        self.w_rf = w_rf
        self.k_rf = k_rf
        self.r0 = r0
        self.v_dc = v_dc
        self.k_dc = k_dc
        self.z0 = z0
        # chain variables
        self.mathieu_order = 1
        self.equilibrium_positions = {}
        self.secular_radial = {}
        self.secular_axial = {}

    def set_ion(self, mass, position):
        """
        Sets the mass of an ion at the given position.
        Arguments:
            mass        (float)     : the mass of the ion (in amu).
            position    (position)  : the position (i.e. index) of the ion.
        """
        if position not in self.ions:
            self.ions[position] = ionObject(mass)
        else:
            self.ions[position].mass = mass

    def recalculate_variables(self):
        """
        Recalculates equilibrium positions and mode data.
        """
        self._calculate_equilibrium_positions()
        self._calculate_secular_axial()
        self._calculate_secular_radial()

    def _calculate_equilibrium_positions(self):
        """
        Recalculates the equilibrium positions of the chain.
        """
        pass

    def _calculate_secular_axial(self):
        """
        Recalculates the axial secular frequencies of the chain.
        """
        pass

    def _calculate_secular_radial(self):
        """
        Recalculates the axial secular frequencies of the chain.
        """
        pass

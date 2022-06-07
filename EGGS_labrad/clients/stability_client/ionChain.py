import numpy as np
from scipy.optimize import root

__all__ = ["ionObject", "ionChain"]


"""
Fundamental and derived constants
"""
_QE = 1.60217e-19
_AMU = 1.66053904e-27
_HBAR = 1.05457182e-34
_LSK = 8.96273592e-4
_KE2 = 2.30707751e-28
_wkhz = 2 * np.pi * 1e3
_wmhz = 2 * np.pi * 1e6


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
        self.secular_axial = 0
        self.secular_radial = 0


class ionChain(object):
    """
    An object for calculating normal mode data.
    """

    def __init__(self,
                 v_rf=0, w_rf=0, k_rf=1, r0=0,
                 v_dc=0, k_dc=1, z0=0,
                 ions=[]
                 ):
        """
        Create all trap-related variables here.
        """
        # ion variables
        # todo: check if ions are ionobjects or masses
        self.ions = ions
        # trap variables
        self.v_rf = v_rf
        self.w_rf = w_rf
        self.k_rf = k_rf
        self.r0 = r0
        self.v_dc = v_dc
        self.k_dc = k_dc
        self.z0 = z0
        # chain/mode variables
        self.l0 = self._length_scale()
        self.mathieu_order = 1
        self.equilibrium_positions = {}
        self.mode_axial = {}
        self.mode_radial = {}


    """
    User Functions
    """
    def insert_ion(self, mass, position=None):
        """
        Insert an ion to the chain.
        Ion is inserted at end of chain by default.
        Arguments:
            mass        (float)     : the mass of the ion (in amu).
            position    (position)  : the position (i.e. index) of the ion. Starts at 0.
        """
        # add ion to end of chain by default
        if position is None:
            position = len(self.ions)
            mass *= _AMU
        # otherwise check that position exists
        elif position not in range(len(self.ions)):
            raise Exception("Error: ion position exceeds chain length.")

        # create ion and insert into chain
        ion = ionObject(mass)
        self.ions.insert(position, ion)

        # calculate secular frequencies
        ion.secular_axial = self._axial_secular_frequency(mass)
        ion.secular_radial = self._radial_secular_frequency(mass)

        # recalculate chain values
        self._calculate_equilibrium_positions()
        self._calculate_modes()

    def set_ion(self, mass, position):
        """
        Changes the mass of an ion within the chain.
        Arguments:
            mass        (float)     : the mass of the ion (in amu).
            position    (position)  : the position (i.e. index) of the ion. Starts at 0.
        """
        # make sure position is in array
        if position not in range(len(self.ions)):
            raise Exception("Error: ion position exceeds chain length.")

        # change ion mass
        mass *= _AMU
        ion = self.ions[position]
        ion.mass = mass

        # recalculate secular frequencies
        ion.secular_axial = self._axial_secular_frequency(mass)
        ion.secular_radial = self._radial_secular_frequency(mass)

        # recalculate chain values
        self._calculate_equilibrium_positions()
        self._calculate_modes()

    def set_trap(self, **kwargs):
        """
        Adjust the value of a trap parameter.
        Args:
            **kwargs:

        Returns:
            ***todo
        """
        # ***todo if changed, need to recalculate all ion values
        pass

    """
    Secular Frequencies
    """
    def _axial_secular_frequency(self, mass):
        """
        Calculate the axial secular frequency of an ion.
        Arguments:
            mass    (float) : the ion mass (in amu).
        Returns:
                    (float) : the axial secular frequency (in Hz).
        """
        return np.sqrt((2 * _QE * self.k_dc * self.v_dc) / (mass * self.z0**2))

    def _radial_secular_frequency(self, mass):
        """
        Calculate the radial secular frequency of an ion.
        Arguments:
            mass    (float) : the ion mass (in amu).
        Returns:
                    (float) : the axial secular frequency (in Hz).
        """
        return np.sqrt(0.5 * ((_QE * self.v_rf * self.k_rf) / (mass * self.w_rf * self.r0**2))**2 -
                       ((_QE * self.k_dc * self.v_dc) / (mass * self.z0**2)))

    def _length_scale(self):
        """
        Calculate the length scale of ion-ion separation.
        Returns:
                    (float) : the length scale (in m).
        """
        return _LSK * np.power(np.power(self.z0, 2) / self.v_dc, 1 / 3)


    """
    Calculating Mode Data
    """
    def _calculate_equilibrium_positions(self):
        """
        Recalculates the equilibrium positions of the chain.
        Returns:
            dict(float, np.array): the normal mode frequencies and their associated eigenvectors.
        """
        num_ions = len(self.ions)

        # create the equilibrium equation for an individual ion
        def ionEquilibriumEquation(positionArr, i):
            distances = np.array(np.array(positionArr) - positionArr[i], dtype=float)
            th21 = np.power(distances[:i], -2)
            th22 = np.power(distances[i+1:], -2)
            return positionArr[i] - np.sum(th21) + np.sum(th22)

        # create equilibrium equations for the entire chain
        def chainEquilibriumEquations(positionArr):
            return [ionEquilibriumEquation(positionArr, i) for i in range(len(positionArr))]

        # guess the ion equilibrium positions
        def guessEquilibriumPositions(n):
            return np.linspace(-1, 1, n) * (1.009 * (n-1) / n**0.559)

        # find scaled equilibrium positions
        soln = root(chainEquilibriumEquations, guessEquilibriumPositions(num_ions), method='krylov')
        self.equilibrium_positions = soln['x']

        return soln['x']

    def _calculate_modes(self):
        """
        Recalculates the radial and axial normal mode frequencies of the chain.
        Returns:
            dict(float, np.array): the normal mode frequencies and their associated eigenvectors.
        """
        # get values from  ion chain
        num_ions = len(self.ions)
        massArr = np.array([ion.mass for ion in self.ions])
        wsecArrAxial = np.array([ion.secular_axial for ion in self.ions])
        wsecArrRadial = np.array([ion.secular_radial for ion in self.ions])

        # create matrix that gives |x_i - x_j|^-3
        ind = np.triu_indices(num_ions, 1)
        distMat = np.zeros((num_ions, num_ions))
        distMat[ind] = np.power(self.equilibrium_positions[ind[1]] - self.equilibrium_positions[ind[0]], -3)
        distMat += np.transpose(distMat)

        # get sum of |x_i - x_j|^-3 for each ion
        distSumMat = np.diag(np.sum(distMat, axis=1))

        # create secular frequency matrix mass-scaled into normal-mode picture
        wzMat = np.sqrt(np.outer(massArr, 1 / massArr))
        wzMat *= np.outer(wsecArrAxial, np.ones(num_ions)) ** 2

        # get anharmonicities
        ah = np.diag(np.power(wsecArrRadial / wsecArrAxial, 2))

        # create hessian matrices
        hessMatAxial = wzMat * (np.identity(num_ions) + 2 * (distSumMat - distMat))
        hessMatRadial = wzMat * (ah - (distSumMat - distMat))

        # get axial eigenvalues
        eigenvalsAxial, eigenvecAxial = np.linalg.eig(hessMatAxial)
        eigenvalsAxial, eigenvecAxial = np.sqrt(eigenvalsAxial), eigenvecAxial.transpose()
        axialModes = dict(zip(eigenvalsAxial, eigenvecAxial))
        self.mode_axial = axialModes

        # get radial eigenvalues
        eigenvalsRadial, eigenvecRadial = np.linalg.eig(hessMatRadial)
        eigenvalsRadial, eigenvecRadial = np.sqrt(eigenvalsRadial), eigenvecRadial.transpose()
        radialModes = dict(zip(eigenvalsRadial, eigenvecRadial))
        self.mode_radial = radialModes
        # todo: sort increasing by mode freq
        return axialModes, radialModes


if __name__ == "__main__":
    # create ion chain object
    # MOTion trap
    chain = ionChain(v_rf=270.2, w_rf=1.697*_wmhz, r0=6.8453e-3, v_dc=94.05, k_dc=0.022, z0=10.16e-3)

    # create ions
    massList = [38, 40, 38, 40, 40]
    for mass_amu in massList:
        chain.insert_ion(mass_amu)

    print("Equilibrium Positions:", np.round(chain.equilibrium_positions, 3))
    print("Axial Modes:")
    print("\tMode Freq. (x2\u03C0 MHz)\tMode Eigenvectors")
    for mode_freq, mode_vec in chain.mode_axial.items():
        print("\t{:.3f}".format(mode_freq / _wmhz), "\t\t", mode_vec)

    print("Radial Modes:")
    print("\tMode Freq. (x2\u03C0 MHz)\tMode Eigenvectors")
    for mode_freq, mode_vec in chain.mode_radial.items():
        print("\t{:.3f}".format(mode_freq / _wmhz), "\t\t", mode_vec)

    print("\n"
          "\n"
          "\n")

    chain.set_ion(30, 0)
    chain.set_ion(30, 2)

    print("Equilibrium Positions:", np.round(chain.equilibrium_positions, 3))
    print("Axial Modes:")
    print("\tMode Freq. (x2\u03C0 MHz)\tMode Eigenvectors")
    for mode_freq, mode_vec in chain.mode_axial.items():
        print("\t{:.3f}".format(mode_freq / _wmhz), "\t\t", mode_vec)

    print("Radial Modes:")
    print("\tMode Freq. (x2\u03C0 MHz)\tMode Eigenvectors")
    for mode_freq, mode_vec in chain.mode_radial.items():
        print("\t{:.3f}".format(mode_freq / _wmhz), "\t\t", mode_vec)

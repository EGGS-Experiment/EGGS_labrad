# the following wavelength to RGB conversion was written by
# http://codingmess.blogspot.com/2009/05/conversion-of-wavelength-in-nanometers.html

def wav2RGB(wavelength):
    wavelength = int(wavelength)

    R, G, B = (0, 0, 0)
    SSS = 0

    # get RGB values
    if wavelength < 380:
        R = 1.0
        G = 0.0
        B = 1
    elif (wavelength >= 380) and (wavelength < 440):
        R = -(wavelength - 440.) / (440. - 350.)
        G = 0.0
        B = 1.0
    elif (wavelength >= 440) and (wavelength < 490):
        R = 0.0
        G = (wavelength - 440.) / (490. - 440.)
        B = 1.0
    elif (wavelength >= 490) and (wavelength < 510):
        R = 0.0
        G = 1.0
        B = -(wavelength - 510.) / (510. - 490.)
    elif (wavelength >= 510) and (wavelength < 580):
        R = (wavelength - 510.) / (580. - 510.)
        G = 1.0
        B = 0.0
    elif (wavelength >= 580) and (wavelength < 645):
        R = 1.0
        G = -(wavelength - 645.) / (645. - 580.)
        B = 0.0
    elif (wavelength >= 645) and (wavelength <= 780):
        R = 1.0
        G = 0.0
        B = 0.0
    elif wavelength > 780:
        R = 1.0
        G = 0.0
        B = 0.0

    # intensity correction
    if wavelength < 380:
        SSS = 0.6
    elif (wavelength >= 380) and (wavelength < 420):
        SSS = 0.3 + 0.7 * (wavelength - 350) / (420 - 350)
    elif (wavelength >= 420) and (wavelength <= 700):
        SSS = 1.0
    elif (wavelength > 700) and (wavelength <= 780):
        SSS = 0.3 + 0.7 * (780 - wavelength) / (780 - 700)
    elif wavelength > 780:
        SSS = 0.3

    SSS *= 255
    return (int(SSS * R), int(SSS * G), int(SSS * B))

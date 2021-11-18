from artiq.dashboard.moninj import _TTLWidget

if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(_TTLWidget)
"""
Contains stuff useful for LabRAD scripts and experiments.
"""

__all__ = ["runExperiment"]


# imports
import sys

# run functions
def runExperiment(experiment, **kwargs):
    """
    Creates a LabRAD experiment file and launches it using scriptscanner.
    """
    # connect to labrad
    import labrad
    cxn = labrad.connect()
    # get script scanner and submit exp
    try:
        ss = cxn.script_scanner
        exp = experiment(cxn=cxn)
        ident = ss.register_external_launch(exp.name)
        exp.execute(ident)
    except Exception as e:
        print(e)
        raise e

"""
Error bits and their definitions for the SRS-RGA200.
Keys in each dictionary are the bits, and the values are the error messages.
"""

_SRS_RGA_SER_ERRORS = {
    # SERIAL ERRORS
    0: 'Serial: Bad command received',
    1: 'Serial: Bad parameter received',
    2: 'Serial: Command too long',
    3: 'Serial: Overwrite in receiving',
    4: 'Serial: Transmit buffer overwrite',
    5: 'Serial: Jumper protection violation',
    6: 'Serial: Parameter conflict',
}

_SRS_RGA_FIL_ERRORS = {
    # FILAMENT ERRORS
    0: 'Filament: Single filament operation',
    5: 'Filament: Vacuum Chamber pressure too high',
    6: 'Filament: Unable to set the requested emission current',
    7: 'Filament: No filament detected'
}

_SRS_RGA_CEM_ERRORS = {
    # ELECTRON MULTIPLIER ERRORS
    7: 'Electron Multiplier: No electron multiplier option installed'
}

_SRS_RGA_QMF_ERRORS = {
    # QUADRUPOLE ERRORS
    4: 'Quadrupole Filter: Power supply in current-limited mode',
    6: 'Quadrupole Filter: Primary current exceeds 2.0A',
    7: 'Quadrupole Filter: RF_CT exceeds (V_EXT- 2V) at M_MAX'
}

_SRS_RGA_DET_ERRORS = {
    # DETECTOR ERRORS
    1: 'Detector: OP-AMP Input Offset Voltage out of range',
    3: 'Detector: COMPENSATE fails to read -5nA input current',
    4: 'Detector: COMPENSATE fails to read +5nA input current',
    5: 'Detector: DETECT fails to read -5nA input current',
    6: 'Detector: DETECT fails to read +5nA input current',
    7: 'Detector: ADC16 Test failure'
}

_SRS_RGA_PSU_ERRORS = {
    # POWER SUPPLY ERRORS
    6: 'Power Supply: Voltage < 22V',
    7: 'Power Supply: Voltage > 26V'
}

_SRS_RGA_STATUS_QUERIES = {
    0: ('EC', _SRS_RGA_SER_ERRORS),     # Serial Communication Error
    1: ('EF', _SRS_RGA_FIL_ERRORS),     # Filament Error
    3: ('EM', _SRS_RGA_CEM_ERRORS),     # Multiplier Error
    4: ('EQ', _SRS_RGA_QMF_ERRORS),     # Quadrupole Filter Error
    5: ('ED', _SRS_RGA_DET_ERRORS),     # Detector Error
    6: ('EP', _SRS_RGA_PSU_ERRORS)      # Power Supply Error
}

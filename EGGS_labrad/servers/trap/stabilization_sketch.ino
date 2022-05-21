#define SCLK_PIN    A0
#define SYNC_PIN    A0
#define SDIN_PIN    A0
#define LDAC_PIN    A0
#define CLR_PIN     A0

#define OUTPUT_PORT PORTA

#define REF_VOLTAGE             5
#define DAC_REG_MAX             0xFFFFF
#define VOLTS_TO_MU(VOLTS)      (VOLTS * 1048575 / REF_VOLTAGE)
#define MU_TO_VOLTS(VOLTS_MU)   (VOLTS_MU * REF_VOLTAGE / 1048575)


void setup() {
    // set pin directions
    // todo: set SCLK, SYNC, SDIN, LDAC, CLR
    // initialize the DAC
    // todo: ensure CLR, LDAC, RESET are raised
    // todo: clear tri, clear gnd
// set up serial
    Serial.begin(115200);
}

void loop() {
    // wait for serial input
    while (!Serial.available()) {}
    // read serial input & check command is correct
    if (Serial.readStringUntil("\n") == "F?\r\n") {
        // get voltage data and convert to percent, then return result over serial
        Serial.println(analogRead(fmaPin) * voltsToPct);
    }
    else {
        Serial.println("Invalid input.");
    }
}

uint32_t createDACMessage(int voltage) {
    uint32_t dac_msg = 0x900000 | VOLTS_TO_MU(voltage);
    return dac_msg
}

uint32_t createControlMessage(uint8_t address, bool OPGND, bool DACTRI, bool SDODIS) {
    uint32_t ctrl_msg = 0xA00000;
    // todo: set default values for arguments
    // todo: or in arguments into ctrl_msg
    return ctrl_msg
}

void programDAC(uint32_t data) {
    // bring SYNC and LDAC low to enable input
    PORTA &= ~(_BV(SYNC_PIN) | _BV(LDAC_PIN));

    // MSB first
    for (uint32_t i=23; i>=0; --i) {
        // bring SCLK high since data clocked in on falling edge
        PORTA |= _BV(SCLK_PIN);

        // set SDIN to data state
        if (data & _BV(i)) {
            PORTA |= _BV(SDIN_PIN);
        } else {
            PORTA &= ~(_BV(SDIN_PIN));
        }

        // set SCLK low to clock data in
        PORTA &= ~(_BV(SCLK_PIN));
    }
    // bring SYNC high to update input shift register
    PORTA |= _BV(SYNC_PIN);
    return
}

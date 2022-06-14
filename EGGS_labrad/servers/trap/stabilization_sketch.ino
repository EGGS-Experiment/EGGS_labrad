#include "stdint.h"

#define SCLK_PIN    PC0
#define SYNC_PIN    PC1
#define SDIN_PIN    PC2
#define LDAC_PIN    PC3
#define CLR_PIN     PC4

#define OUTPUT_PORT         PORTC
#define OUTPUT_PORT_DDR     DDRC

#define REF_VOLTAGE             5
#define DAC_REG_MAX             0xFFFFF
#define VOLTS_TO_MU(VOLTS)      (VOLTS * 1048575 / REF_VOLTAGE)
#define MU_TO_VOLTS(VOLTS_MU)   (VOLTS_MU * REF_VOLTAGE / 1048575)      // 209715 mu per volt

#define msg_init    0x200000
#define msg_1v      0x133333
#define msg_5v      0x1FFFFF


void setup() {
    // set pin directions (DDR registers)
    OUTPUT_PORT_DDR |= 0xFF;

    // initialize the DAC
    programDAC(msg_init);
    programDAC(msg_1v);

    // set up serial
    Serial.begin(115200);
    Serial.println("Ready.");
}

void loop() {
    // wait for serial input
    while (!Serial.available()) {}
    // read serial input & check command is correct
    if (Serial.readStringUntil("\n") == "F?\n") {
        // program DAC with given voltage
        uint32_t dac_msg = createDACMessage(1);
        programDAC(dac_msg);
        Serial.println("Programmed.");
    }
    else {
        Serial.println("Invalid input.");
    }
}

uint32_t createDACMessage(int voltage) {
    uint32_t dac_msg = 0x100000 | VOLTS_TO_MU(voltage);
    return dac_msg;
}

uint32_t createControlMessage(uint8_t address, bool OPGND, bool DACTRI, bool SDODIS) {
    uint32_t ctrl_msg = 0x200000;
    // todo: set default values for arguments
    // todo: or in arguments into ctrl_msg
    return ctrl_msg;
}

void programDAC(uint32_t data) {
    // bring SYNC and LDAC low to enable input
    OUTPUT_PORT &= ~(_BV(SYNC_PIN) | _BV(LDAC_PIN));

    // MSB first
    for (int i=23; i>=0; --i) {
        // bring SCLK high since data clocked in on falling edge
        OUTPUT_PORT |= _BV(SCLK_PIN);

        // set SDIN to data state
        if ((data >> i) & _BV(0)) {
            OUTPUT_PORT |= _BV(SDIN_PIN);
        } else {
            OUTPUT_PORT &= ~(_BV(SDIN_PIN));
        }

        // set SCLK low to clock data in
        OUTPUT_PORT &= ~(_BV(SCLK_PIN));
    }

    // bring SYNC high to update input shift register
    OUTPUT_PORT |= _BV(SYNC_PIN);
    return;
}
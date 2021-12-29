#define fmaPin      A0
#define fmaIndex    0
#define voltsToPct  0.09765625 // 100/1024

void setup() {
  //speed up ADC to 160 kHz (analog read takes 13 clocks)
  ADCSRA = (_BV(ADEN) | _BV(ADPS1) | _BV(ADPS0));  //set prescaler to 1/8, default is 1/128
  ADMUX = (_BV(REFS1) | _BV(ADLAR));               //set vref to vcc and adc register alignment
  //set fmaPin to output
  pinMode(fmaPin, OUTPUT);
  //set up serial
  Serial.begin(115200);
}

void loop() {
  //wait for serial input
  while (!Serial.available()) {}
  //read serial input & check command is correct
  if (Serial.readStringUntil("\n") == "F?\r\n") {
    //get voltage data and convert to percent, then return result over serial
    Serial.println(analogRead(fmaPin) * voltsToPct);
  }
  else {
    Serial.println("Invalid input.");
  }
}

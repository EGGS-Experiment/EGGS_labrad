#define fmaPin      A0
#define fmaIndex    0
#define voltsToPct  0.09765625 // 100/1024

//todo: speedup analogread

void setup() {
  //set up pin
  pinMode(fmaPin, OUTPUT);
  //set up serial
  Serial.begin(115200);
  //wait for serial to connect
  //while (!Serial) {}
  //Serial.setTimeout(500);
}

void loop() {
  //wait for serial input
  while (!Serial.available()) {}
  //read serial input & check command is correct
  if (Serial.readStringUntil("\n") == "Flow?\r\n") {
    //get voltage data and convert to percent, then return result over serial
    Serial.println(analogRead(fmaPin) * voltsToPct);
  }
  else{
    Serial.println("Invalid input.");
  }
}

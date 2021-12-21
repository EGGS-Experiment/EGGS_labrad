int fmaPin = A0;
int fmaIndex = 0;

void setup() {
  //set up serial
  Serial.begin(38400);
  //wait for serial to connect
  while (!Serial) {}
  Serial.setTimeout(2000);
}

void loop() {
  //wait for serial input
  while (!Serial.available()) {}
  //read serial input
  String serial_cmd = Serial.readString();
  //check command is correct
  if (serial_cmd == "Flow?\r\n") {
    //get voltage data and convert to %
    float pct = float(analogRead(fmaPin)) * 100 / 1024;
    //return result over serial
    Serial.println(pct);
    Serial.flush();
  }
  else{
    Serial.println("Invalid input.");
  }
}

//
//void get_serial(){
//  //check serial buffer for input and read if it exists
//  bytes_to_read = Serial.available();
//  String serial_input = Serial.readString()
//  for (int i = fmaIndex; i
//}
//
//void parse_serial(){
  

//todo: poll in background and add bytes to buffer

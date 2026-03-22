#include <Servo.h>

Servo myServo;
int currentPos = 90; // start from middle

void setup() {
  myServo.attach(9);
  myServo.write(currentPos);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    char command = Serial.read();

    if (command == 'C') {
      // Clockwise slow
        myServo.write(90);
        
      // for (int pos = currentPos; pos <= 180; pos++) {
      //   myServo.write(pos);
      //   delay(20);  // increase delay = slower
      // }
      // currentPos = 180;
    }

    if (command == 'A') {
      // Anti-clockwise slow
       
        myServo.write(0);
      // for (int pos = currentPos; pos >= 0; pos--) {
      //   delay(20);  // increase delay = slower
      // }
      // currentPos = 0;
    }
  }
}

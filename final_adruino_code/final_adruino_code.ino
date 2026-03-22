#include <Servo.h>

Servo gasServo;

const int servoPin = 9;
const int lpgLedPin = 2;
const int inductionLedPin = 3;

void setup() {
  Serial.begin(9600); // Communication with Python
  gasServo.attach(servoPin);
  gasServo.write(90); // Start closed

  pinMode(lpgLedPin, OUTPUT);
  pinMode(inductionLedPin, OUTPUT);

  digitalWrite(lpgLedPin, LOW);
  digitalWrite(inductionLedPin, LOW);

  delay(2000); // wait a bit before checking connection
  Serial.println("ARDUINO_READY"); // Initial handshake
}
void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "OPEN_COVER") {
      Serial.println("OPEN_COVER"); // Initial handshake
      gasServo.write(0);
    }
    else if (command == "CLOSE_COVER") {
      Serial.println("CLOSE_COVER"); // Initial handshake
      gasServo.write(90);
      digitalWrite(2, LOW);
      digitalWrite(3, LOW);
    }
    else if (command == "LPG_ON") {
      digitalWrite(2, HIGH);
      digitalWrite(3, LOW);
    }
    else if (command == "INDUCTION_ON") {
      digitalWrite(3, HIGH);
      digitalWrite(2, LOW);
    }
    else if (command == "NONE") {
      digitalWrite(2, LOW);
      digitalWrite(3, LOW);
    }
  }
}

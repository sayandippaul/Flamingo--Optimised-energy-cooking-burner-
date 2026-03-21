const express = require('express');
const { SerialPort } = require('serialport');

const app = express();

// serve HTML file
app.use(express.static('public'));

const port = new SerialPort({
  path: 'COM3',
  baudRate: 9600
});

app.get('/clockwise', (req, res) => {
  port.write('C');
  res.send("Clockwise");
});

app.get('/anticlockwise', (req, res) => {
  port.write('A');
  res.send("Anti-clockwise");
});

app.listen(5000, () => {
  console.log("Server running at http://localhost:5000");
});

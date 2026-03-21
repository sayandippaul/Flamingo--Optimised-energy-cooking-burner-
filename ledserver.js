const express = require('express');
const { SerialPort } = require('serialport');

const app = express();
app.use(express.static('public')); // serve HTML

// 🔁 Change COM port if needed
const port = new SerialPort({
  path: 'COM3',
  baudRate: 9600
});

// Routes
app.get('/lpg-on', (req, res) => {
  port.write('1');
  res.send('LPG ON');
});

app.get('/lpg-off', (req, res) => {
  port.write('2');
  res.send('LPG OFF');
});

app.get('/induction-on', (req, res) => {
  port.write('3');
  res.send('Induction ON');
});

app.get('/induction-off', (req, res) => {
  port.write('4');
  res.send('Induction OFF');
});

app.get('/none', (req, res) => {
  port.write('0');
  res.send('ALL OFF');
});

app.listen(3000, () => {
  console.log('Server running at http://localhost:3000');
});

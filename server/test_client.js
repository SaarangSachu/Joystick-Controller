const io = require('socket.io-client');
const socket = io('http://localhost:3000');

socket.on('connect', () => {
    console.log('Test Client Connected');
    // Simulate button press
    socket.emit('controller-input', { type: 'BUTTON_PRESS', button: 'A' });

    // Give it a moment to send then exit
    setTimeout(() => {
        console.log('Exiting test client');
        process.exit(0);
    }, 1000);
});

socket.on('disconnect', () => {
    console.log('Disconnected');
});

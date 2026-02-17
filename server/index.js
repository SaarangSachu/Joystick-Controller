const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const ip = require('ip');

const app = express();
app.use(cors());
app.use(express.static('public'));

const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

const players = {}; // Map socket.id -> player_id

io.on('connection', (socket) => {
    // console.log('User connected:', socket.id); // Validated by specific event

    socket.on('join-room', (roomId) => {
        socket.join(roomId);
        console.log(`Socket ${socket.id} joined room ${roomId}`);
    });

    socket.on('register-player', (playerId) => {
        players[socket.id] = playerId;
        console.log(`PLAYER_CONNECTED: ${playerId}`);
    });

    socket.on('controller-input', (data) => {
        if (!players[socket.id] && data.player) {
            // Fallback registration if they start sending input without registering
            players[socket.id] = data.player;
            console.log(`PLAYER_CONNECTED: ${data.player}`);
        }
        // console.log('Received input:', data); // Reduce noise for launcher
        io.emit('controller-input', data);
    });

    socket.on('pong', (data) => {
        if (players[socket.id]) {
            const latency = Date.now() - data.t;
            console.log(`PLAYER_PING: ${players[socket.id]} ${latency}ms`);
        }
    });

    socket.on('disconnect', () => {
        if (players[socket.id]) {
            console.log(`PLAYER_DISCONNECTED: ${players[socket.id]}`);
            delete players[socket.id];
        }
    });
});

// Ping Loop
setInterval(() => {
    io.emit('ping', { t: Date.now() });
}, 2000);

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`Server running on http://${ip.address()}:${PORT}`);
});

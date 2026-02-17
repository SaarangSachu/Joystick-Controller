const socket = io();

// Configuration
const REFRESH_RATE = 50;
// Get Player ID from URL (default to 1)
const urlParams = new URLSearchParams(window.location.search);
const PLAYER_ID = parseInt(urlParams.get('player')) || 1;

console.log(`Initialized as Player ${PLAYER_ID}`);

// Apply Player Theme
const playerColors = {
    1: 'cyan',   // Blue
    2: 'red',    // Red
    3: 'lime',   // Green
    4: 'yellow'  // Yellow
};
const themeColor = playerColors[PLAYER_ID] || 'cyan';
document.documentElement.style.setProperty('--theme-color', themeColor);

// Update title
document.title = `Player ${PLAYER_ID} - PocketPad`;

// --- Socket Connection ---
socket.on('connect', () => {
    console.log('Connected to server:', socket.id);
    socket.emit('register-player', PLAYER_ID);
});

socket.on('ping', (data) => {
    socket.emit('pong', data);
});

// --- Button Handling ---
// Helper to bind touch events
function bindButton(elementId, buttonName) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const press = (e) => {
        e.preventDefault(); // Prevent mouse emulation / scrolling
        el.classList.add('active');
        if (navigator.vibrate) navigator.vibrate(10);
        socket.emit('controller-input', { player: PLAYER_ID, type: 'BUTTON', button: buttonName, value: 1 });
    };

    const release = (e) => {
        e.preventDefault();
        el.classList.remove('active');
        socket.emit('controller-input', { player: PLAYER_ID, type: 'BUTTON', button: buttonName, value: 0 });
    };

    // Touch events for mobile
    el.addEventListener('touchstart', press);
    el.addEventListener('touchend', release);

    // Mouse events for desktop testing
    el.addEventListener('mousedown', press);
    el.addEventListener('mouseup', release);
    el.addEventListener('mouseleave', release);
}

// Bind all buttons
const buttonMap = {
    'btn-a': 'A',
    'btn-b': 'B',
    'btn-x': 'X',
    'btn-y': 'Y',
    'dpad-up': 'DPAD_UP',
    'dpad-down': 'DPAD_DOWN',
    'dpad-left': 'DPAD_LEFT',
    'dpad-right': 'DPAD_RIGHT',
    'btn-start': 'START',
    'btn-select': 'BACK',
    'btn-l1': 'LB',
    'btn-r1': 'RB',
    // Triggers as buttons for simplicity in Phase 3 (can make analog later if UI supports sliding)
    'btn-l2': 'XUSB_GAMEPAD_LEFT_TRIGGER', // Special handling might be needed in receiver if it expects float
    'btn-r2': 'XUSB_GAMEPAD_RIGHT_TRIGGER'
};

/* 
 * NOTE: For Triggers (L2/R2), standard buttons emit 0 or 1.
 * If we want analog, we need a slider or pressure sensitivity.
 * For now, we'll map them as digital "full press" (value 255/1.0) in the receiver.
 */

Object.keys(buttonMap).forEach(id => {
    bindButton(id, buttonMap[id]);
});


// --- Joystick Handling (Nipple.js) ---
const joyLeft = nipplejs.create({
    zone: document.getElementById('joystick-left'),
    mode: 'static',
    position: { left: '50%', top: '50%' },
    position: { left: '50%', top: '50%' },
    color: themeColor,
    size: 120
});

const joyRight = nipplejs.create({
    zone: document.getElementById('joystick-right'),
    mode: 'static',
    position: { left: '50%', top: '50%' },
    position: { left: '50%', top: '50%' },
    color: themeColor,
    size: 120
});

// Helper to throttle joystick data if needed, but nipple.js is usually okay
function handleJoystick(evt, data, side) {
    if (!data || !data.vector) return;

    // vector is { x: -1 to 1, y: -1 to 1 }
    // Invert Y because screen Y is down-positive, but controller Y is up-positive
    const x = data.vector.x;
    const y = data.vector.y; // nipplejs y is usually up-positive? Let's verify. 
    // joy.cpl expects up as positive usually, but let's test.
    // Actually HTML canvas Y is down-positive. NippleJS 'vector' usually normalizes this.

    // Send individual axis updates
    if (side === 'LEFT') {
        socket.emit('controller-input', { player: PLAYER_ID, type: 'AXIS', axis: 'LX', value: x });
        socket.emit('controller-input', { player: PLAYER_ID, type: 'AXIS', axis: 'LY', value: y });
    } else {
        socket.emit('controller-input', { player: PLAYER_ID, type: 'AXIS', axis: 'RX', value: x });
        socket.emit('controller-input', { player: PLAYER_ID, type: 'AXIS', axis: 'RY', value: y });
    }
}

// Zero out on release
function resetJoystick(side) {
    if (side === 'LEFT') {
        socket.emit('controller-input', { player: PLAYER_ID, type: 'AXIS', axis: 'LX', value: 0 });
        socket.emit('controller-input', { player: PLAYER_ID, type: 'AXIS', axis: 'LY', value: 0 });
    } else {
        socket.emit('controller-input', { player: PLAYER_ID, type: 'AXIS', axis: 'RX', value: 0 });
        socket.emit('controller-input', { player: PLAYER_ID, type: 'AXIS', axis: 'RY', value: 0 });
    }
}

joyLeft.on('move', (evt, data) => handleJoystick(evt, data, 'LEFT'));
joyLeft.on('end', () => resetJoystick('LEFT'));

joyRight.on('move', (evt, data) => handleJoystick(evt, data, 'RIGHT'));
joyRight.on('end', () => resetJoystick('RIGHT'));

// --- Fullscreen Toggle ---
const fullscreenBtn = document.getElementById('fullscreen-btn');
if (fullscreenBtn) {
    fullscreenBtn.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.log(`Error attempting to enable fullscreen: ${err.message}`);
            });
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    });
}

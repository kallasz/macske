const canvas = document.querySelector('#video_stream');
const ctx = canvas.getContext('2d');

const startBtn = document.querySelector('#stream-start');
const stopBtn = document.querySelector('#stream-stop');
const status_box = document.querySelector('#status');

let ws = null;
let isRecording = false;
const WS_URL = `ws${location.protocol == "https:" ? "s" : ""}://${location.hostname}/stream/arpi/ws/`;

ws = new WebSocket(WS_URL);
ws.binaryType = 'arraybuffer';

ws.onopen = () => {
  // if (isRecording) {
  //   status_div.textContent = 'Recording (Connected)';
  //   status_div.className = 'status recording';
  // } else {
  //   status_div.textContent = 'Connected';
  //   status_div.className = 'status connected';
  // }

  startBtn.disabled = isRecording;
  startBtn.hidden = isRecording;
  stopBtn.disabled = !isRecording;
  stopBtn.hidden = !isRecording;
};

ws.onmessage = (event) => {
  if (event.data instanceof ArrayBuffer) {
    displayFrame(event.data);
  }
};

function displayFrame(arrayBuffer) {
  const blob = new Blob([arrayBuffer], { type: 'image/jpeg' });
  const url = URL.createObjectURL(blob);

  const img = new Image();
  img.onload = () => {
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    URL.revokeObjectURL(url); // Clean up
  };
  img.src = url;
}

ws.onclose = () => {
  console.log('WebSocket disconnected');

  if (isRecording) {
    startBtn.disabled = true;
    startBtn.hidden = true;
    stopBtn.disabled = false;
    stopBtn.hidden = false;
  } else {
    startBtn.disabled = true;
    startBtn.hidden = false;
    stopBtn.disabled = true;
    stopBtn.hidden = true;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

startBtn.addEventListener('click', () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ _meta_action: 'START' }));
    isRecording = true;
    startBtn.disabled = true;
    startBtn.hidden = true;
    stopBtn.disabled = false;
    stopBtn.hidden = false;
  } else {
    alert('Not connected to server. Please wait...');
  }
});

stopBtn.addEventListener('click', () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ _meta_action: 'STOP' }));
    isRecording = false;
    stopBtn.disabled = true;
    stopBtn.hidden = true;
    startBtn.disabled = false;
    startBtn.hidden = false;
  }
});
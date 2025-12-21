(function() {
  const canvas = document.getElementById('raceCanvas');
  const ctx = canvas.getContext('2d');

  // Same-origin API (served by Flask)
  const YEAR = 2025;
  let raceNum = 1;
  const NUM_LAPS = 58; // server returns actual max laps
  let seasonMaxRound = 1;
  let currentRound = 1;

  let drivers = [];
  let maxLaps = NUM_LAPS;
  let eventInfo = null;
  let currentLap = 1;
  let progress = 0;
  let speed = 0.003;
  let paused = false;
  let trackRenderer = null;
  let isLoading = true;

  function resizeCanvas() {
    const container = canvas.parentElement;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
  }
  resizeCanvas();

  function drawLoading() {
    ctx.fillStyle = '#141922';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#fff';
    ctx.font = '20px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Loading race data...', canvas.width / 2, canvas.height / 2);
  }

  async function fetchSeasonInfo() {
    try {
      const res = await fetch(`/api/season/${YEAR}`);
      if (!res.ok) throw new Error(`Season API ${res.status}`);
      const s = await res.json();
      seasonMaxRound = s.max_round || 1;
      currentRound = s.current_round || seasonMaxRound;
    } catch (e) {
      console.warn('Season info failed, defaulting to 1 round', e);
      seasonMaxRound = 1;
      currentRound = 1;
    }
  }

  async function loadRaceData() {
    try {
      drawLoading();
      const response = await fetch(`/api/race/${YEAR}/${raceNum}/${NUM_LAPS}`);
      if (!response.ok) throw new Error(`API returned ${response.status}`);
      const data = await response.json();
      drivers = data.drivers;
      maxLaps = data.max_laps;
      eventInfo = data.event_info;

      if (eventInfo) {
        document.querySelector('.viz-race-title').textContent = (eventInfo.name || 'F1 Race').toUpperCase();
        document.querySelector('.viz-race-date').textContent = eventInfo.date || '';
      }

      trackRenderer = new TrackRenderer(drivers);
      isLoading = false;
      animate();
    } catch (error) {
      console.error('Error loading race data:', error);
      ctx.fillStyle = '#141922';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#ff4444';
      ctx.font = '16px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Error loading data. Ensure Flask API is running.', canvas.width / 2, canvas.height / 2);
    }
  }

  class TrackRenderer {
    constructor(driversData) {
      this.track = [];
      this.track_cx = 0;
      this.track_cy = 0;
      this.track_scale = 1;
      this.track_offset_x = 0;
      this.track_offset_y = 0;
      if (driversData.length > 0 && driversData[0].laps['1']) {
        this.initializeTrack(driversData[0].laps['1']);
      }
    }
    initializeTrack(telemetry) {
      const xs = telemetry.map(p => p.X);
      const ys = telemetry.map(p => p.Y);
      const x_min = Math.min(...xs), x_max = Math.max(...xs);
      const y_min = Math.min(...ys), y_max = Math.max(...ys);
      const x_range = x_max - x_min;
      const y_range = y_max - y_min;
      const maxWidth = canvas.width * 0.5;
      const maxHeight = canvas.height * 0.7;
      const scale = Math.min(
        x_range > 0 ? maxWidth / x_range : 1,
        y_range > 0 ? maxHeight / y_range : 1
      );
      this.track_cx = xs.reduce((a, b) => a + b) / xs.length;
      this.track_cy = ys.reduce((a, b) => a + b) / ys.length;
      this.track_scale = scale;
      this.track_offset_x = canvas.width * 0.25;
      this.track_offset_y = canvas.height * 0.5;
      this.track = telemetry.map(point => ({
        x: scale * (point.X - this.track_cx) + this.track_offset_x,
        y: scale * (point.Y - this.track_cy) + this.track_offset_y
      }));
    }
    drawTrack() {
      if (this.track.length < 2) return;
      ctx.strokeStyle = 'rgb(80, 80, 100)';
      ctx.lineWidth = 8;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.beginPath();
      ctx.moveTo(this.track[0].x, this.track[0].y);
      for (let i = 1; i < this.track.length; i++) ctx.lineTo(this.track[i].x, this.track[i].y);
      ctx.closePath();
      ctx.stroke();
      const start = this.track[0];
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(start.x - 20, start.y);
      ctx.lineTo(start.x + 20, start.y);
      ctx.stroke();
    }
    transformPosition(x, y) {
      return {
        x: this.track_scale * (x - this.track_cx) + this.track_offset_x,
        y: this.track_scale * (y - this.track_cy) + this.track_offset_y
      };
    }
  }

  class PositionCalculator {
    static calculateRacePositions(drivers, currentLap, progress) {
      const positions = [];
      const lapKey = String(currentLap);
      for (const driver of drivers) {
        if (!(lapKey in driver.laps)) {
          positions.push({ code: driver.code, time: 999999, x: 0, y: 0 });
          continue;
        }
        const tel = driver.laps[lapKey];
        const idx = Math.min(Math.floor(progress * (tel.length - 1)), tel.length - 1);
        let cumulativeTime = 0;
        for (let i = 1; i < currentLap; i++) {
          if (driver.lap_times[String(i)]) cumulativeTime += driver.lap_times[String(i)];
        }
        if (driver.lap_times[lapKey]) cumulativeTime += driver.lap_times[lapKey] * progress;
        const point = tel[idx];
        positions.push({ code: driver.code, time: cumulativeTime, x: point.X, y: point.Y });
      }
      positions.sort((a, b) => a.time - b.time);
      return positions;
    }
  }

  function updateDashboard(positions) {
    const list = document.getElementById('vizPositionList');
    list.innerHTML = '';
    positions.forEach((pos, i) => {
      const driver = drivers.find(d => d.code === pos.code);
      if (!driver) return;
      const lapTime = driver.lap_times[String(currentLap)] || 0;
      const mins = Math.floor(lapTime / 60);
      const secs = (lapTime % 60).toFixed(2);
      const timeStr = `${mins}:${secs.padStart(5, '0')}`;
      const row = document.createElement('div');
      row.className = 'viz-position-row';
      const posNum = document.createElement('div');
      posNum.className = 'viz-position-num';
      posNum.textContent = i + 1;
      if (i < 3) posNum.style.background = driver.color;
      const bar = document.createElement('div');
      bar.className = 'viz-driver-bar';
      bar.style.background = driver.color;
      const info = document.createElement('div');
      info.className = 'viz-driver-info';
      info.innerHTML = `${driver.abbr}<span class="viz-team-name">${driver.team}</span>`;
      const lapTimeEl = document.createElement('div');
      lapTimeEl.className = 'viz-lap-time';
      lapTimeEl.textContent = timeStr;
      row.appendChild(posNum);
      row.appendChild(bar);
      row.appendChild(info);
      row.appendChild(lapTimeEl);
      list.appendChild(row);
    });
  }

  function drawDriver(x, y, position, abbr, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 14, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = '#000';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(position, x, y);
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 11px sans-serif';
    ctx.fillText(abbr, x, y + 20);
  }

  function animate() {
    if (isLoading) return;
    if (!paused) {
      progress += speed;
      if (progress >= 1) {
        progress = 0; 
        currentLap++; 
        if (currentLap > maxLaps) {
          // Finished this race; advance to next
          currentLap = 1;
          raceNum++;
          if (raceNum > (currentRound || seasonMaxRound)) {
            raceNum = 1; // wrap to start of season
          }
          isLoading = true;
          // Load next race data
          loadRaceData();
          return; // Wait for data to load
        }
      }
      document.getElementById('vizLapText').textContent = `LAP ${currentLap}/${maxLaps}`;
      document.getElementById('vizProgressFill').style.width = (progress * 100) + '%';
    }
    ctx.fillStyle = '#141922';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    if (trackRenderer) trackRenderer.drawTrack();
    const positions = PositionCalculator.calculateRacePositions(drivers, currentLap, progress);
    updateDashboard(positions);
    for (let i = positions.length - 1; i >= 0; i--) {
      const pos = positions[i];
      const driver = drivers.find(d => d.code === pos.code);
      if (driver && pos.time < 999999 && trackRenderer) {
        const screenPos = trackRenderer.transformPosition(pos.x, pos.y);
        drawDriver(screenPos.x, screenPos.y, i + 1, driver.abbr, driver.color);
      }
    }
    requestAnimationFrame(animate);
  }

  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    switch (e.key) {
      case ' ': e.preventDefault(); paused = !paused; break;
      case 'ArrowUp': e.preventDefault(); speed = Math.min(0.02, speed * 1.5); break;
      case 'ArrowDown': e.preventDefault(); speed = Math.max(0.0005, speed / 1.5); break;
    }
  });

  window.addEventListener('resize', () => {
    resizeCanvas();
    if (trackRenderer && drivers.length > 0) {
      trackRenderer.initializeTrack(drivers[0].laps['1']);
    }
  });

  (async () => {
    await fetchSeasonInfo();
    await loadRaceData();
  })();
})();

// Shared functionality for all game pages
let currentGame = '';

// Initialize the game page
function initGamePage(gameName) {
    currentGame = gameName;
    
    // Set up home button
    const homeButton = document.getElementById('homeButton');
    if (homeButton) {
        const { team } = getContext();
        homeButton.href = team ? `/t/${team}` : '/';
    }
    
    // Show leaderboard by default
    showLeaderboard();
    
    // Set up event listeners
    setupEventListeners();
}

// Get context (local vs production, team vs main)
function getContext() {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const parts = window.location.pathname.split('/').filter(Boolean);
    let team = null;
    
    if (parts.length >= 2 && parts[0] === 't') {
        team = parts[1];
    }
    
    return { isLocal, team, game: currentGame };
}

// Show leaderboard
function showLeaderboard() {
    const { isLocal, team } = getContext();
    const baseSrc = team ? `/api/${team}/charts/${currentGame}/leaderboard.png` : `${currentGame}_leaderboard.png`;
    
    document.getElementById('displayImage').src = baseSrc;
    document.getElementById('displayImage').alt = `${currentGame} Leaderboard`;
    
    // Update button states
    document.querySelectorAll('.button').forEach(btn => btn.classList.remove('active'));
    document.querySelector('[onclick="showLeaderboard()"]').classList.add('active');
}

// Show ratings progress
function showRatingsProgress() {
    const { isLocal, team } = getContext();
    const baseSrc = team ? `/api/${team}/charts/${currentGame}/ratings_progress.png` : `${currentGame}_ratings_progress.png`;
    
    document.getElementById('displayImage').src = baseSrc;
    document.getElementById('displayImage').alt = `${currentGame} Ratings Progress`;
    
    // Update button states
    document.querySelectorAll('.button').forEach(btn => btn.classList.remove('active'));
    document.querySelector('[onclick="showRatingsProgress()"]').classList.add('active');
}

// Modal functions
function openAddPlayerModal() {
    document.getElementById('addPlayerModal').style.display = 'block';
    document.getElementById('playerNameInput').focus();
}

function closeAddPlayerModal() {
    document.getElementById('addPlayerModal').style.display = 'none';
    document.getElementById('playerNameInput').value = '';
}

function openAddResultModal() {
    document.getElementById('addResultModal').style.display = 'block';
    // Reset result selection
    const resultRadios = document.querySelectorAll('input[name="result"]');
    resultRadios.forEach(radio => radio.checked = false);
    loadPlayers();
}

function closeAddResultModal() {
    document.getElementById('addResultModal').style.display = 'none';
}

// Load players for result modal
async function loadPlayers() {
    try {
        const { isLocal, team } = getContext();
        const base = isLocal ? 'http://localhost:8080' : '';
        const apiUrl = team ? `${base}/api/${team}/players/${currentGame}` : `${base}/api/players/${currentGame}`;
        
        const response = await fetch(apiUrl, { credentials: 'include' });
        const data = await response.json();
        const players = Array.isArray(data.players) ? data.players : [];

        const player1Select = document.getElementById('player1Select');
        const player2Select = document.getElementById('player2Select');

        if (!player1Select || !player2Select) return;

        // Clear existing options
        player1Select.innerHTML = '<option value="">Select Player 1</option>';
        player2Select.innerHTML = '<option value="">Select Player 2</option>';

        // Add player options
        players.forEach(player => {
            // Format player name: replace underscores with spaces, title case, and handle Q suffix
            const display = player.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()).replace(' Q', ' -♛');
            const option1 = document.createElement('option');
            option1.value = player;
            option1.textContent = display;
            player1Select.appendChild(option1);

            const option2 = document.createElement('option');
            option2.value = player;
            option2.textContent = display;
            player2Select.appendChild(option2);
        });
    } catch (error) {
        console.error('Error loading players:', error);
        showStatusMessage('Failed to load players', 'error');
    }
}

// Add player
async function addPlayer() {
    const playerName = document.getElementById('playerNameInput').value.trim().toLowerCase();
    
    if (!playerName) {
        showStatusMessage('Please enter a player name', 'error');
        return;
    }
    
    if (!playerName.match(/^[a-zA-Z0-9_]+$/)) {
        showStatusMessage('Player name can only contain letters, numbers, and underscores', 'error');
        return;
    }

    // Show loading state
    const addBtn = document.querySelector('#addPlayerModal .modal-btn.confirm');
    const originalText = addBtn.textContent;
    addBtn.textContent = 'Adding Player...';
    addBtn.disabled = true;
    
    try {
        const { isLocal, team } = getContext();
        const base = isLocal ? 'http://localhost:8080' : '';
        const apiUrl = team ? `${base}/api/${team}/players/${currentGame}` : `${base}/api/players/${currentGame}`;
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                player_name: playerName
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatusMessage(`Player "${data.player_name}" added successfully!`, 'success');
            setTimeout(() => {
                closeAddPlayerModal();
                // Refresh the charts
                location.reload();
            }, 1500);
        } else {
            showStatusMessage(data.error || 'Failed to add player', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showStatusMessage('Network error. Make sure the server is running.', 'error');
    } finally {
        // Restore button state
        addBtn.textContent = originalText;
        addBtn.disabled = false;
    }
}

// Submit result
async function submitResult() {
    const player1 = document.getElementById('player1Select').value;
    const player2 = document.getElementById('player2Select').value;
    const result = document.querySelector('input[name="result"]:checked')?.value;
    
    if (!player1 || !player2) {
        showStatusMessage('Please select both players', 'error');
        return;
    }
    
    if (player1 === player2) {
        showStatusMessage('Players must be different', 'error');
        return;
    }
    
    if (!result) {
        showStatusMessage('Please select a result', 'error');
        return;
    }

    // Show loading state
    const submitBtn = document.querySelector('#addResultModal .modal-btn.confirm');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Submitting...';
    submitBtn.disabled = true;

    try {
        const { isLocal, team } = getContext();
        const base = isLocal ? 'http://localhost:8080' : '';
        const apiUrl = team ? `${base}/api/${team}/results/${currentGame}` : `${base}/api/results/${currentGame}`;
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                player1: player1,
                player2: player2,
                result: result
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatusMessage(`Result submitted: ${player1} vs ${player2} (${result})`, 'success');
            setTimeout(() => {
                closeAddResultModal();
                // Refresh the charts
                location.reload();
            }, 1500);
        } else {
            showStatusMessage(data.error || 'Failed to submit result', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showStatusMessage('Network error. Make sure the server is running.', 'error');
    } finally {
        // Restore button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

// Status message functions
function showStatusMessage(message, type) {
    // Remove existing status messages
    const existingMessages = document.querySelectorAll('.status-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new status message
    const statusDiv = document.createElement('div');
    statusDiv.className = `status-message ${type}`;
    statusDiv.textContent = message;
    document.body.appendChild(statusDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (statusDiv.parentNode) {
            statusDiv.remove();
        }
    }, 5000);
}

// Setup event listeners
function setupEventListeners() {
    // Close modals when clicking outside
    window.onclick = function(event) {
        const addPlayerModal = document.getElementById('addPlayerModal');
        const addResultModal = document.getElementById('addResultModal');
        
        if (event.target === addPlayerModal) {
            closeAddPlayerModal();
        }
        if (event.target === addResultModal) {
            closeAddResultModal();
        }
    }

    // Handle Enter key in input
    const playerNameInput = document.getElementById('playerNameInput');
    if (playerNameInput) {
        playerNameInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                addPlayer();
            }
        });
    }
}

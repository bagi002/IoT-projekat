// Global variables
const API_BASE_URL = 'http://localhost:5000/api';
let temperatureChart, humidityChart;
let lastNotificationCount = 0;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    initializeCharts();
    initializeEventListeners();
    updateCurrentTime();
    startDataRefresh();
    
    // Set initial tab
    showTab('dashboard');
});

// Tab management
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            showTab(tabName);
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
        });
    });
}

function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
        
        // Load data for specific tabs
        if (tabName === 'history') {
            loadHistoryData();
        } else if (tabName === 'notifications') {
            loadNotifications();
        }
    }
}

// Initialize event listeners
function initializeEventListeners() {
    // Pump controls
    document.getElementById('start-pump').addEventListener('click', startPump);
    document.getElementById('stop-pump').addEventListener('click', stopPump);
    
    // Heater controls
    document.getElementById('start-heater').addEventListener('click', startHeater);
    document.getElementById('stop-heater').addEventListener('click', stopHeater);
    
    // History controls
    document.getElementById('refresh-charts').addEventListener('click', loadHistoryData);
    document.getElementById('time-range').addEventListener('change', loadHistoryData);
    
    // Notification controls
    document.getElementById('clear-all-notifications').addEventListener('click', clearAllNotifications);
}

// Time management
function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('sr-RS', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('current-time').textContent = timeString;
}

// Data refresh
function startDataRefresh() {
    // Update time every second
    setInterval(updateCurrentTime, 1000);
    
    // Update dashboard data every 5 seconds
    setInterval(loadDashboardData, 5000);
    
    // Check for new notifications every 10 seconds
    setInterval(checkNewNotifications, 10000);
    
    // Initial load
    loadDashboardData();
}

// Dashboard data loading
async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard`);
        const data = await response.json();
        
        updateDashboard(data);
        
        // Update connection status
        document.getElementById('connection-status').textContent = '● Online';
        document.getElementById('connection-status').className = 'status-online';
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        
        // Update connection status
        document.getElementById('connection-status').textContent = '● Offline';
        document.getElementById('connection-status').className = 'status-offline';
    }
}

function updateDashboard(data) {
    // Update Beton Sensor
    updateSensorCard('beton', data.beton_sensor);
    
    // Update Vazduh Sensor
    updateSensorCard('vazduh', data.vazduh_sensor);
    
    // Update Pumpa
    updateActuatorCard('pumpa', data.pumpa);
    
    // Update Grijač
    updateActuatorCard('grijac', data.grijac);
}

function updateSensorCard(sensorType, sensorData) {
    const prefix = sensorType;
    
    // Temperature
    document.getElementById(`${prefix}-temp`).textContent = `${sensorData.temperature.toFixed(1)}°C`;
    
    // Humidity
    document.getElementById(`${prefix}-humidity`).textContent = `${sensorData.humidity.toFixed(1)}%`;
    
    // Battery
    const batteryLevel = sensorData.battery;
    document.getElementById(`${prefix}-battery`).textContent = `${batteryLevel}%`;
    updateBatteryLevel(`${prefix}-battery-level`, batteryLevel);
    
    // Status
    const statusElement = document.getElementById(`${prefix}-status`);
    if (sensorData.status === 'online') {
        statusElement.className = 'status-indicator online';
    } else {
        statusElement.className = 'status-indicator offline';
    }
}

function updateActuatorCard(actuatorType, actuatorData) {
    const prefix = actuatorType;
    
    // Status
    const activeElement = document.getElementById(`${prefix}-active`);
    if (actuatorData.active) {
        activeElement.textContent = 'Aktivna';
        activeElement.className = 'status-text active';
    } else {
        activeElement.textContent = 'Neaktivna';
        activeElement.className = 'status-text inactive';
    }
    
    // Battery
    const batteryLevel = actuatorData.battery;
    document.getElementById(`${prefix}-battery`).textContent = `${batteryLevel}%`;
    updateBatteryLevel(`${prefix}-battery-level`, batteryLevel);
    
    // Status indicator
    const statusElement = document.getElementById(`${prefix}-status`);
    if (actuatorData.status === 'online') {
        statusElement.className = 'status-indicator online';
    } else {
        statusElement.className = 'status-indicator offline';
    }
    
    // Specific data
    if (actuatorType === 'pumpa' && actuatorData.remaining_time) {
        document.getElementById('pumpa-time').textContent = `${actuatorData.remaining_time}s`;
    } else if (actuatorType === 'pumpa') {
        document.getElementById('pumpa-time').textContent = '0s';
    }
    
    if (actuatorType === 'grijac' && actuatorData.temperature) {
        document.getElementById('grijac-temp').textContent = `${actuatorData.temperature.toFixed(1)}°C`;
    }
}

function updateBatteryLevel(elementId, batteryLevel) {
    const batteryElement = document.getElementById(elementId);
    if (batteryElement) {
        batteryElement.style.setProperty('--battery-level', `${batteryLevel}%`);
        batteryElement.style.width = `${batteryLevel}%`;
    }
}

// Control functions
async function startPump() {
    const duration = parseInt(document.getElementById('pump-duration').value) || 300;
    
    try {
        const response = await fetch(`${API_BASE_URL}/pumpa/upravljanje`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                akcija: 'pokreni',
                trajanje: duration
            })
        });
        
        const result = await response.json();
        
        if (result.uspjeh) {
            showNotificationToast('info', result.poruka);
        } else {
            showNotificationToast('warning', result.poruka);
        }
        
    } catch (error) {
        console.error('Error starting pump:', error);
        showNotificationToast('critical', 'Greška pri pokretanju pumpe');
    }
}

async function stopPump() {
    try {
        const response = await fetch(`${API_BASE_URL}/pumpa/upravljanje`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                akcija: 'zaustavi'
            })
        });
        
        const result = await response.json();
        
        if (result.uspjeh) {
            showNotificationToast('info', result.poruka);
        } else {
            showNotificationToast('warning', result.poruka);
        }
        
    } catch (error) {
        console.error('Error stopping pump:', error);
        showNotificationToast('critical', 'Greška pri zaustavljanju pumpe');
    }
}

async function startHeater() {
    const targetTemp = parseInt(document.getElementById('heater-temp').value) || 50;
    
    try {
        const response = await fetch(`${API_BASE_URL}/grijac/upravljanje`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                akcija: 'pokreni',
                ciljna_temperatura: targetTemp
            })
        });
        
        const result = await response.json();
        
        if (result.uspjeh) {
            showNotificationToast('info', result.poruka);
        } else {
            showNotificationToast('warning', result.poruka);
        }
        
    } catch (error) {
        console.error('Error starting heater:', error);
        showNotificationToast('critical', 'Greška pri pokretanju grijača');
    }
}

async function stopHeater() {
    try {
        const response = await fetch(`${API_BASE_URL}/grijac/upravljanje`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                akcija: 'zaustavi'
            })
        });
        
        const result = await response.json();
        
        if (result.uspjeh) {
            showNotificationToast('info', result.poruka);
        } else {
            showNotificationToast('warning', result.poruka);
        }
        
    } catch (error) {
        console.error('Error stopping heater:', error);
        showNotificationToast('critical', 'Greška pri zaustavljanju grijača');
    }
}

// Charts
function initializeCharts() {
    // Temperature Chart
    const tempCtx = document.getElementById('temperatureChart').getContext('2d');
    temperatureChart = new Chart(tempCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperatura betona',
                    data: [],
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Temperatura vazduha',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Temperatura (°C)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Vreme'
                    }
                }
            }
        }
    });
    
    // Humidity Chart
    const humCtx = document.getElementById('humidityChart').getContext('2d');
    humidityChart = new Chart(humCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Vlažnost betona',
                    data: [],
                    borderColor: '#27ae60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Vlažnost vazduha',
                    data: [],
                    borderColor: '#f39c12',
                    backgroundColor: 'rgba(243, 156, 18, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Vlažnost (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Vreme'
                    }
                }
            }
        }
    });
}

async function loadHistoryData() {
    const timeRange = document.getElementById('time-range').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/istorija?hours=${timeRange}`);
        const data = await response.json();
        
        updateCharts(data);
        
    } catch (error) {
        console.error('Error loading history data:', error);
        showNotificationToast('critical', 'Greška pri učitavanju istorijskih podataka');
    }
}

function updateCharts(data) {
    // Prepare data for charts
    const labels = [];
    const betonTemp = [];
    const vazduhTemp = [];
    const betonHumidity = [];
    const vazduhHumidity = [];
    
    // Process data (assuming we have data for both sensors at same times)
    const maxDataPoints = Math.min(data.beton.length, data.vazduh.length);
    
    for (let i = 0; i < maxDataPoints; i++) {
        const betonData = data.beton[i];
        const vazduhData = data.vazduh[i];
        
        if (betonData && vazduhData) {
            const time = new Date(betonData.timestamp).toLocaleTimeString('sr-RS', {
                hour: '2-digit',
                minute: '2-digit'
            });
            
            labels.push(time);
            betonTemp.push(betonData.temperature);
            vazduhTemp.push(vazduhData.temperature);
            betonHumidity.push(betonData.humidity);
            vazduhHumidity.push(vazduhData.humidity);
        }
    }
    
    // Update temperature chart
    temperatureChart.data.labels = labels;
    temperatureChart.data.datasets[0].data = betonTemp;
    temperatureChart.data.datasets[1].data = vazduhTemp;
    temperatureChart.update();
    
    // Update humidity chart
    humidityChart.data.labels = labels;
    humidityChart.data.datasets[0].data = betonHumidity;
    humidityChart.data.datasets[1].data = vazduhHumidity;
    humidityChart.update();
}

// Notifications
async function loadNotifications() {
    try {
        const response = await fetch(`${API_BASE_URL}/notifikacije`);
        const notifications = await response.json();
        
        displayNotifications(notifications);
        updateNotificationBadge(notifications.filter(n => !n.acknowledged).length);
        
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

function displayNotifications(notifications) {
    const notificationsList = document.getElementById('notifications-list');
    notificationsList.innerHTML = '';
    
    if (notifications.length === 0) {
        notificationsList.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 20px;">Nema notifikacija</p>';
        return;
    }
    
    notifications.forEach(notification => {
        const notificationElement = createNotificationElement(notification);
        notificationsList.appendChild(notificationElement);
    });
}

function createNotificationElement(notification) {
    const div = document.createElement('div');
    div.className = `notification-item ${notification.severity}`;
    
    if (notification.acknowledged) {
        div.style.opacity = '0.6';
    }
    
    div.innerHTML = `
        <div class="notification-content">
            <div class="notification-type ${notification.severity}">${notification.type}</div>
            <div class="notification-message">${notification.message}</div>
            <div class="notification-time">${new Date(notification.timestamp).toLocaleString('sr-RS')}</div>
        </div>
        <div class="notification-actions">
            ${!notification.acknowledged ? `<button class="btn btn-secondary" onclick="acknowledgeNotification(${notification.id})">
                <i class="fas fa-check"></i> Potvrdi
            </button>` : '<span style="color: #27ae60;"><i class="fas fa-check"></i> Potvrđeno</span>'}
        </div>
    `;
    
    return div;
}

async function acknowledgeNotification(notificationId) {
    try {
        const response = await fetch(`${API_BASE_URL}/notifikacije/${notificationId}/acknowledge`, {
            method: 'POST'
        });
        
        if (response.ok) {
            loadNotifications(); // Reload notifications
        }
        
    } catch (error) {
        console.error('Error acknowledging notification:', error);
    }
}

async function clearAllNotifications() {
    // This would require a backend endpoint to clear all notifications
    // For now, just reload
    loadNotifications();
}

async function checkNewNotifications() {
    try {
        const response = await fetch(`${API_BASE_URL}/notifikacije`);
        const notifications = await response.json();
        
        const unacknowledgedCount = notifications.filter(n => !n.acknowledged).length;
        
        // Check if there are new notifications
        if (unacknowledgedCount > lastNotificationCount) {
            const newNotifications = notifications.filter(n => !n.acknowledged).slice(0, unacknowledgedCount - lastNotificationCount);
            
            // Show toast for newest notification
            if (newNotifications.length > 0) {
                const newest = newNotifications[0];
                showNotificationToast(newest.severity, newest.message);
            }
        }
        
        lastNotificationCount = unacknowledgedCount;
        updateNotificationBadge(unacknowledgedCount);
        
    } catch (error) {
        console.error('Error checking new notifications:', error);
    }
}

function updateNotificationBadge(count) {
    const badge = document.getElementById('notification-badge');
    badge.textContent = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
}

function showNotificationToast(severity, message) {
    const toast = document.getElementById('notification-toast');
    const icon = toast.querySelector('.toast-icon');
    const messageElement = toast.querySelector('.toast-message');
    const closeButton = toast.querySelector('.toast-close');
    
    // Set content
    messageElement.textContent = message;
    
    // Set severity class and icon
    toast.className = `notification-toast ${severity}`;
    icon.className = `toast-icon ${severity}`;
    
    // Set icon based on severity
    switch (severity) {
        case 'critical':
            icon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            break;
        case 'warning':
            icon.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
            break;
        case 'info':
            icon.innerHTML = '<i class="fas fa-info-circle"></i>';
            break;
    }
    
    // Show toast
    toast.classList.add('show');
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 5000);
    
    // Close button
    closeButton.onclick = () => {
        toast.classList.remove('show');
    };
}

// CSS for battery levels (injected dynamically)
const style = document.createElement('style');
style.textContent = `
    .battery-level::before {
        width: var(--battery-level, 0%);
    }
`;
document.head.appendChild(style);

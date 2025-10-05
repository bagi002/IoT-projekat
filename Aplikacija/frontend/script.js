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
        // Load data from individual endpoints
        const [betonResponse, povrsinaResponse, pumpaResponse, grijacResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/senzori/beton`),
            fetch(`${API_BASE_URL}/senzori/povrsina`),
            fetch(`${API_BASE_URL}/pumpa/stanje`),
            fetch(`${API_BASE_URL}/grijac/stanje`)
        ]);

        // Check for timeouts (simulate 1min timeout with 5 second timeout for demo)
        const timeout = 5000; // 5 seconds for demo, should be 60000 for 1 minute
        
        const betonData = betonResponse.ok ? await betonResponse.json() : null;
        const povrsinaData = povrsinaResponse.ok ? await povrsinaResponse.json() : null;
        const pumpaData = pumpaResponse.ok ? await pumpaResponse.json() : null;
        const grijacData = grijacResponse.ok ? await grijacResponse.json() : null;

        updateDashboard({
            beton_sensor: betonData,
            povrsina_sensor: povrsinaData,
            pumpa: pumpaData,
            grijac: grijacData
        });
        
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
    if (data.beton_sensor) {
        updateSensorCard('beton', data.beton_sensor);
    } else {
        setSensorOffline('beton');
    }
    
    // Update Povrsina/Vazduh Sensor  
    if (data.povrsina_sensor) {
        updateSensorCard('vazduh', data.povrsina_sensor);
    } else {
        setSensorOffline('vazduh');
    }
    
    // Update Pumpa
    if (data.pumpa) {
        updateActuatorCard('pumpa', data.pumpa);
    } else {
        setActuatorOffline('pumpa');
    }
    
    // Update Grijač
    if (data.grijac) {
        updateActuatorCard('grijac', data.grijac);
    } else {
        setActuatorOffline('grijac');
    }
}

function updateSensorCard(sensorType, sensorData) {
    const prefix = sensorType;
    
    // Temperature
    document.getElementById(`${prefix}-temp`).textContent = `${sensorData.temperatura.toFixed(1)}°C`;
    
    // Humidity
    document.getElementById(`${prefix}-humidity`).textContent = `${sensorData.vlaznost.toFixed(1)}%`;
    
    // Battery
    const batteryLevel = sensorData.baterija;
    document.getElementById(`${prefix}-battery`).textContent = `${batteryLevel}%`;
    updateBatteryLevel(`${prefix}-battery-level`, batteryLevel);
    
    // Status
    const statusElement = document.getElementById(`${prefix}-status`);
    if (sensorData.greska === null) {
        statusElement.className = 'status-indicator online';
    } else {
        statusElement.className = 'status-indicator offline';
    }
}

function setSensorOffline(sensorType) {
    const prefix = sensorType;
    
    document.getElementById(`${prefix}-temp`).textContent = '--°C';
    document.getElementById(`${prefix}-humidity`).textContent = '--%';
    document.getElementById(`${prefix}-battery`).textContent = '--%';
    document.getElementById(`${prefix}-status`).className = 'status-indicator offline';
    updateBatteryLevel(`${prefix}-battery-level`, 0);
}

function updateActuatorCard(actuatorType, actuatorData) {
    const prefix = actuatorType;
    
    // Status
    const activeElement = document.getElementById(`${prefix}-active`);
    let isActive = false;
    
    if (actuatorType === 'pumpa') {
        isActive = actuatorData.aktivna;
    } else if (actuatorType === 'grijac') {
        isActive = actuatorData.aktivan;
    }
    
    if (isActive) {
        activeElement.textContent = actuatorType === 'pumpa' ? 'Aktivna' : 'Aktivan';
        activeElement.className = 'status-text active';
    } else {
        activeElement.textContent = actuatorType === 'pumpa' ? 'Neaktivna' : 'Neaktivan';
        activeElement.className = 'status-text inactive';
    }
    
    // Battery
    const batteryLevel = actuatorData.baterija;
    document.getElementById(`${prefix}-battery`).textContent = `${batteryLevel}%`;
    updateBatteryLevel(`${prefix}-battery-level`, batteryLevel);
    
    // Status indicator
    const statusElement = document.getElementById(`${prefix}-status`);
    if (actuatorData.greska === null) {
        statusElement.className = 'status-indicator online';
    } else {
        statusElement.className = 'status-indicator offline';
    }
    
    // Specific data
    if (actuatorType === 'pumpa') {
        // For pump, we'll show remaining time if available (not in new API, but keep for compatibility)
        document.getElementById('pumpa-time').textContent = '0s';
    }
    
    if (actuatorType === 'grijac' && actuatorData.temperatura) {
        document.getElementById('grijac-temp').textContent = `${actuatorData.temperatura.toFixed(1)}°C`;
    }
}

function setActuatorOffline(actuatorType) {
    const prefix = actuatorType;
    
    const activeElement = document.getElementById(`${prefix}-active`);
    activeElement.textContent = actuatorType === 'pumpa' ? 'Neaktivna' : 'Neaktivan';
    activeElement.className = 'status-text offline';
    
    document.getElementById(`${prefix}-battery`).textContent = '--%';
    document.getElementById(`${prefix}-status`).className = 'status-indicator offline';
    updateBatteryLevel(`${prefix}-battery-level`, 0);
    
    if (actuatorType === 'pumpa') {
        document.getElementById('pumpa-time').textContent = '0s';
    } else if (actuatorType === 'grijac') {
        document.getElementById('grijac-temp').textContent = '--°C';
    }
}

function updateControlCardStatus(actuatorType, actuatorData) {
    // This function is no longer needed since we removed manual control cards
    // Keeping it for compatibility but it doesn't do anything
}

function updateBatteryLevel(elementId, batteryLevel) {
    const batteryElement = document.getElementById(elementId);
    if (batteryElement) {
        batteryElement.style.setProperty('--battery-level', `${batteryLevel}%`);
        batteryElement.style.width = `${batteryLevel}%`;
    }
    
    // Update battery text and icon colors based on level
    const prefix = elementId.replace('-battery-level', '');
    const batteryText = document.getElementById(`${prefix}-battery`);
    const batteryIcon = document.getElementById(`${prefix}-battery-icon`);
    
    if (batteryText && batteryIcon) {
        // Remove existing classes
        batteryText.classList.remove('critical', 'warning', 'good', 'excellent');
        batteryIcon.classList.remove('critical', 'warning', 'good', 'excellent');
        
        // Determine battery level class and icon
        let levelClass, iconClass;
        
        if (batteryLevel <= 15) {
            levelClass = 'critical';
            iconClass = 'fas fa-battery-empty';
        } else if (batteryLevel <= 35) {
            levelClass = 'warning';
            iconClass = 'fas fa-battery-quarter';
        } else if (batteryLevel <= 65) {
            levelClass = 'good';
            iconClass = 'fas fa-battery-half';
        } else if (batteryLevel <= 85) {
            levelClass = 'good';
            iconClass = 'fas fa-battery-three-quarters';
        } else {
            levelClass = 'excellent';
            iconClass = 'fas fa-battery-full';
        }
        
        // Apply new classes
        batteryText.classList.add(levelClass);
        batteryIcon.classList.add(levelClass);
        batteryIcon.className = `battery-icon ${iconClass} ${levelClass}`;
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
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff',
                        font: {
                            size: 14,
                            weight: '600'
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Temperatura (°C)',
                        color: '#ffffff',
                        font: {
                            size: 14,
                            weight: '600'
                        }
                    },
                    ticks: {
                        color: '#e0e6ed',
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Vreme',
                        color: '#ffffff',
                        font: {
                            size: 14,
                            weight: '600'
                        }
                    },
                    ticks: {
                        color: '#e0e6ed',
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
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
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff',
                        font: {
                            size: 14,
                            weight: '600'
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Vlažnost (%)',
                        color: '#ffffff',
                        font: {
                            size: 14,
                            weight: '600'
                        }
                    },
                    ticks: {
                        color: '#e0e6ed',
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Vreme',
                        color: '#ffffff',
                        font: {
                            size: 14,
                            weight: '600'
                        }
                    },
                    ticks: {
                        color: '#e0e6ed',
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
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
            <button class="btn btn-danger" onclick="deleteNotification(${notification.id})" title="Obriši notifikaciju">
                <i class="fas fa-trash"></i>
            </button>
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

async function deleteNotification(notificationId) {
    try {
        const response = await fetch(`${API_BASE_URL}/notifikacije/${notificationId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadNotifications(); // Reload notifications
        }
        
    } catch (error) {
        console.error('Error deleting notification:', error);
    }
}

async function clearAllNotifications() {
    try {
        const response = await fetch(`${API_BASE_URL}/notifikacije/clear`, {
            method: 'POST'
        });
        
        if (response.ok) {
            loadNotifications(); // Reload notifications
        }
        
    } catch (error) {
        console.error('Error clearing all notifications:', error);
    }
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

// Global variables
const API_BASE_URL = 'http://localhost:5000/api';
let temperatureChart, humidityChart;
let lastNotificationCount = 0;
let currentSimTime = null;

// Simulated time functions
async function loadSimTime() {
    try {
        const response = await fetch(`${API_BASE_URL}/sim-time`);
        if (response.ok) {
            currentSimTime = await response.json();
            console.log('📅 Loaded sim time:', currentSimTime);
        } else {
            console.error('❌ Failed to load sim time:', response.status);
            currentSimTime = null;
        }
    } catch (error) {
        console.error('❌ Error loading sim time:', error);
        currentSimTime = null;
    }
}

function getCurrentSimTime() {
    if (currentSimTime) {
        return new Date(currentSimTime.iso_time);
    } else {
        console.warn('⚠️ Sim time not loaded, using system time');
        return new Date();
    }
}

function formatSimTime(format = 'iso') {
    const simTime = getCurrentSimTime();
    
    if (format === 'iso') {
        return simTime.toISOString();
    } else if (format === 'local') {
        return simTime.toLocaleString();
    } else if (format === 'time') {
        return simTime.toLocaleTimeString();
    } else if (format === 'date') {
        return simTime.toLocaleDateString();
    }
    
    return simTime.toString();
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 IoT Frontend loaded');
    
    // Load sim time first
    loadSimTime().then(() => {
        console.log('📅 Sim time loaded:', currentSimTime);
        
        // Check if all required elements exist
        checkRequiredElements();
        
        initializeTabs();
        initializeCharts();
        initializeEventListeners();
        updateCurrentTime();
        startDataRefresh();
        
        // Set initial tab
        showTab('dashboard');
        
        // Initial notification load with debug info
        console.log('📡 Starting initial notification load...');
        loadNotifications();
    });
});

// Check if all required DOM elements exist
function checkRequiredElements() {
    console.log('🔍 Checking required DOM elements...');
    
    const requiredElements = [
        'beton-temp', 'beton-humidity', 'beton-battery', 'beton-status',
        'vazduh-temp', 'vazduh-humidity', 'vazduh-battery', 'vazduh-status', 
        'pumpa-active', 'pumpa-battery', 'pumpa-status',
        'grijac-active', 'grijac-battery', 'grijac-status', 'grijac-temp',
        'connection-status'
    ];
    
    let allElementsFound = true;
    
    requiredElements.forEach(elementId => {
        const element = document.getElementById(elementId);
        if (element) {
            console.log(`✅ Element found: ${elementId}`);
        } else {
            console.error(`❌ Missing element: ${elementId}`);
            allElementsFound = false;
        }
    });
    
    if (allElementsFound) {
        console.log('🎉 All required elements found!');
    } else {
        console.error('⚠️  Some elements are missing!');
    }
    
    return allElementsFound;
}

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
    const refreshBtn = document.getElementById('refresh-charts');
    const timeRange = document.getElementById('time-range');
    
    if (refreshBtn) refreshBtn.addEventListener('click', loadHistoryData);
    if (timeRange) timeRange.addEventListener('change', loadHistoryData);
    
    // Notification controls
    const markAllReadBtn = document.getElementById('mark-all-read');
    const clearReadBtn = document.getElementById('clear-read-notifications');
    const clearAllBtn = document.getElementById('clear-all-notifications');
    
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', markAllNotificationsAsRead);
    }
    
    if (clearReadBtn) {
        clearReadBtn.addEventListener('click', clearReadNotifications);
    }
    
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', clearAllNotifications);
    }
    
    // Event delegation for notification actions
    const notificationsList = document.getElementById('notifications-list');
    if (notificationsList) {
        notificationsList.addEventListener('click', function(e) {
            const button = e.target.closest('button[data-action]');
            if (button) {
                e.preventDefault();
                e.stopPropagation();
                
                const action = button.getAttribute('data-action');
                const id = parseInt(button.getAttribute('data-id'));
                
                if (!isNaN(id)) {
                    if (action === 'acknowledge') {
                        acknowledgeNotification(id);
                    } else if (action === 'delete') {
                        deleteNotification(id);
                    }
                }
            }
        });
    }
}

// Time management
function updateCurrentTime() {
    const now = getCurrentSimTime();
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
    console.log('🔄 Starting automatic data refresh...');
    
    // Update sim time every 30 seconds
    setInterval(loadSimTime, 30000);
    
    // Update time display every second
    setInterval(updateCurrentTime, 1000);
    
    // Update dashboard data every 5 seconds
    setInterval(loadDashboardData, 5000);
    
    // Check for new notifications every 2 seconds for real-time updates
    setInterval(loadNotifications, 2000);
    
    // Initial load with delay to ensure DOM is ready
    setTimeout(() => {
        console.log('🎯 Performing initial data load...');
        loadDashboardData();
    }, 1000);
}

// Dashboard data loading
async function loadDashboardData() {
    try {
        console.log('📡 Loading dashboard data from /api/dashboard...');
        
        // Load data from new dashboard endpoint
        const response = await fetch(`${API_BASE_URL}/dashboard`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const dashboardData = await response.json();
        console.log('✅ Dashboard data received:', dashboardData);
        
        // Map backend data to frontend structure
        const mappedData = {
            beton_sensor: dashboardData.beton_senzor,
            povrsina_sensor: dashboardData.povrsina_senzor,
            pumpa: dashboardData.pumpa,
            grijac: dashboardData.grijac
        };
        
        console.log('🔄 Mapped data for frontend:', mappedData);
        updateDashboard(mappedData);
        
        // Update connection status
        document.getElementById('connection-status').textContent = '● Online';
        document.getElementById('connection-status').className = 'status-online';
        
    } catch (error) {
        console.error('❌ Error loading dashboard data:', error);
        
        // Update connection status
        const connectionStatus = document.getElementById('connection-status');
        if (connectionStatus) {
            connectionStatus.textContent = '● Offline';
            connectionStatus.className = 'status-offline';
        }
        
        // Set all devices offline
        updateDashboard({
            beton_sensor: null,
            povrsina_sensor: null,
            pumpa: null,
            grijac: null
        });
    }
}

function updateDashboard(data) {
    console.log('🎯 UpdateDashboard called with:', data);
    
    // Update Beton Sensor
    console.log('🔍 Processing beton sensor...');
    if (data.beton_sensor && data.beton_sensor.active && data.beton_sensor.data) {
        console.log('✅ Beton sensor is active, updating with:', data.beton_sensor.data);
        updateSensorCard('beton', data.beton_sensor.data);
    } else {
        console.log('❌ Beton sensor is offline or no data');
        setSensorOffline('beton');
    }
    
    // Update Povrsina/Vazduh Sensor  
    console.log('🔍 Processing povrsina sensor...');
    if (data.povrsina_sensor && data.povrsina_sensor.active && data.povrsina_sensor.data) {
        console.log('✅ Povrsina sensor is active, updating with:', data.povrsina_sensor.data);
        updateSensorCard('vazduh', data.povrsina_sensor.data);
    } else {
        console.log('❌ Povrsina sensor is offline or no data');
        setSensorOffline('vazduh');
    }
    
    // Update Pumpa
    console.log('🔍 Processing pumpa...');
    if (data.pumpa && data.pumpa.active && data.pumpa.data) {
        console.log('✅ Pumpa is active, updating with:', data.pumpa.data);
        updateActuatorCard('pumpa', data.pumpa.data);
    } else {
        console.log('❌ Pumpa is offline or no data');
        setActuatorOffline('pumpa');
    }
    
    // Update Grijač
    console.log('🔍 Processing grijac...');
    if (data.grijac && data.grijac.active && data.grijac.data) {
        console.log('✅ Grijac is active, updating with:', data.grijac.data);
        updateActuatorCard('grijac', data.grijac.data);
    } else {
        console.log('❌ Grijac is offline or no data');
        setActuatorOffline('grijac');
    }
    
    console.log('🏁 Dashboard update completed');
}

function updateSensorCard(sensorType, sensorData) {
    const prefix = sensorType;
    console.log(`🎯 updateSensorCard called for ${sensorType} with data:`, sensorData);
    
    // Verify all elements exist before updating
    const tempElement = document.getElementById(`${prefix}-temp`);
    const humidityElement = document.getElementById(`${prefix}-humidity`);
    const batteryElement = document.getElementById(`${prefix}-battery`);
    const statusElement = document.getElementById(`${prefix}-status`);
    
    if (!tempElement) {
        console.error(`❌ Element ${prefix}-temp not found!`);
        return;
    }
    if (!humidityElement) {
        console.error(`❌ Element ${prefix}-humidity not found!`);
        return;
    }
    if (!batteryElement) {
        console.error(`❌ Element ${prefix}-battery not found!`);
        return;
    }
    if (!statusElement) {
        console.error(`❌ Element ${prefix}-status not found!`);
        return;
    }
    
    console.log(`✅ All elements found for ${prefix}`);
    
    // Temperature
    const temp = sensorData.temperatura !== null && sensorData.temperatura !== undefined 
        ? `${sensorData.temperatura.toFixed(1)}°C` 
        : '--°C';
    console.log(`🌡️  Setting ${prefix}-temp to: ${temp}`);
    tempElement.textContent = temp;
    
    // Humidity
    const humidity = sensorData.vlaznost !== null && sensorData.vlaznost !== undefined 
        ? `${sensorData.vlaznost.toFixed(1)}%` 
        : '--%';
    console.log(`💧 Setting ${prefix}-humidity to: ${humidity}`);
    humidityElement.textContent = humidity;
    
    // Battery
    const batteryLevel = sensorData.baterija || 0;
    console.log(`🔋 Setting ${prefix}-battery to: ${batteryLevel}%`);
    batteryElement.textContent = `${batteryLevel}%`;
    
    // Update battery level indicator if it exists
    const batteryLevelElement = document.getElementById(`${prefix}-battery-level`);
    if (batteryLevelElement) {
        updateBatteryLevel(`${prefix}-battery-level`, batteryLevel);
    }
    
    // Status
    if (sensorData.greska === null || sensorData.greska === undefined) {
        statusElement.className = 'status-indicator online';
        console.log(`🟢 Set ${prefix} status to online`);
    } else {
        statusElement.className = 'status-indicator offline';
        console.log(`🔴 Set ${prefix} status to offline due to error:`, sensorData.greska);
    }
    
    console.log(`✅ Successfully updated ${prefix} sensor card`);
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
    console.log(`🎯 updateActuatorCard called for ${actuatorType} with data:`, actuatorData);
    
    // Verify essential elements exist
    const activeElement = document.getElementById(`${prefix}-active`);
    const batteryElement = document.getElementById(`${prefix}-battery`);
    const statusElement = document.getElementById(`${prefix}-status`);
    
    if (!activeElement) {
        console.error(`❌ Element ${prefix}-active not found!`);
        return;
    }
    if (!batteryElement) {
        console.error(`❌ Element ${prefix}-battery not found!`);
        return;
    }
    if (!statusElement) {
        console.error(`❌ Element ${prefix}-status not found!`);
        return;
    }
    
    console.log(`✅ All elements found for ${prefix}`);
    
    // Status (Active/Inactive)
    let isActive = false;
    if (actuatorType === 'pumpa') {
        isActive = actuatorData.aktivna || false;
    } else if (actuatorType === 'grijac') {
        isActive = actuatorData.aktivan || false;
    }
    
    const statusText = actuatorType === 'pumpa' 
        ? (isActive ? 'Aktivna' : 'Neaktivna')
        : (isActive ? 'Aktivan' : 'Neaktivan');
    
    console.log(`⚡ Setting ${prefix} status to: ${statusText}`);
    activeElement.textContent = statusText;
    activeElement.className = isActive ? 'status-text active' : 'status-text inactive';
    
    // Battery
    const batteryLevel = actuatorData.baterija || 0;
    console.log(`🔋 Setting ${prefix}-battery to: ${batteryLevel}%`);
    batteryElement.textContent = `${batteryLevel}%`;
    
    // Update battery level indicator if it exists
    const batteryLevelElement = document.getElementById(`${prefix}-battery-level`);
    if (batteryLevelElement) {
        updateBatteryLevel(`${prefix}-battery-level`, batteryLevel);
    }
    
    // Status indicator
    if (actuatorData.greska === null || actuatorData.greska === undefined) {
        statusElement.className = 'status-indicator online';
        console.log(`🟢 Set ${prefix} status indicator to online`);
    } else {
        statusElement.className = 'status-indicator offline';
        console.log(`🔴 Set ${prefix} status indicator to offline due to error:`, actuatorData.greska);
    }
    
    // Specific temperature for grijac
    if (actuatorType === 'grijac' && actuatorData.temperatura !== null && actuatorData.temperatura !== undefined) {
        const grijacTempElement = document.getElementById('grijac-temp');
        if (grijacTempElement) {
            const tempValue = `${actuatorData.temperatura.toFixed(1)}°C`;
            console.log(`🌡️  Setting grijac-temp to: ${tempValue}`);
            grijacTempElement.textContent = tempValue;
        }
    }
    
    console.log(`✅ Successfully updated ${prefix} actuator card`);
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
        console.log('📊 Loading sensor history data...');
        
        // Učitaj podatke za oba senzora
        const betonResponse = await fetch(`${API_BASE_URL}/sensor-history?device_type=beton_senzor&limit=100`);
        const vazduhResponse = await fetch(`${API_BASE_URL}/sensor-history?device_type=povrsina_senzor&limit=100`);
        
        if (!betonResponse.ok || !vazduhResponse.ok) {
            throw new Error('Failed to fetch sensor history');
        }
        
        const betonData = await betonResponse.json();
        const vazduhData = await vazduhResponse.json();
        
        console.log('📊 Beton history:', betonData);
        console.log('📊 Vazduh history:', vazduhData);
        
        updateChartsWithSensorHistory(betonData.data || [], vazduhData.data || []);
        
    } catch (error) {
        console.error('❌ Error loading history data:', error);
        showNotificationToast('critical', 'Greška pri učitavanju istorijskih podataka');
    }
}

function updateChartsWithSensorHistory(betonData, vazduhData) {
    console.log('📊 Updating charts with sensor history...');
    
    // Pripremi podatke za chartove
    const labels = [];
    const betonTemp = [];
    const vazduhTemp = [];
    const betonHumidity = [];
    const vazduhHumidity = [];
    
    // Kombiniraj i sortiraj podatke po vremenu
    const allData = [];
    
    betonData.forEach(record => {
        allData.push({
            time: new Date(record.sim_time),
            device: 'beton',
            temperatura: record.temperatura,
            vlaznost: record.vlaznost
        });
    });
    
    vazduhData.forEach(record => {
        allData.push({
            time: new Date(record.sim_time),
            device: 'vazduh',
            temperatura: record.temperatura,
            vlaznost: record.vlaznost
        });
    });
    
    // Sortiraj po vremenu
    allData.sort((a, b) => a.time - b.time);
    
    // Uzmi poslednih 20 časova podataka
    const maxPoints = 20;
    const limitedData = allData.slice(-maxPoints);
    
    // Grupiši po vremenskim intervalima
    const timeGroups = {};
    limitedData.forEach(item => {
        const timeKey = item.time.toISOString().slice(0, 13); // Grupiši po satu
        if (!timeGroups[timeKey]) {
            timeGroups[timeKey] = { beton: null, vazduh: null };
        }
        timeGroups[timeKey][item.device] = item;
    });
    
    // Kreiraj labels i podatke
    Object.keys(timeGroups).sort().forEach(timeKey => {
        const date = new Date(timeKey + ':00:00.000Z');
        labels.push(date.toLocaleTimeString('sr-RS', { 
            hour: '2-digit', 
            minute: '2-digit',
            day: '2-digit',
            month: '2-digit'
        }));
        
        const group = timeGroups[timeKey];
        betonTemp.push(group.beton ? group.beton.temperatura : null);
        vazduhTemp.push(group.vazduh ? group.vazduh.temperatura : null);
        betonHumidity.push(group.beton ? group.beton.vlaznost : null);
        vazduhHumidity.push(group.vazduh ? group.vazduh.vlaznost : null);
    });
    
    console.log('📊 Chart data prepared:', { labels: labels.length, betonTemp: betonTemp.length });
    
    // Ažuriraj temperature chart
    if (temperatureChart) {
        temperatureChart.data.labels = labels;
        temperatureChart.data.datasets[0].data = betonTemp;
        temperatureChart.data.datasets[1].data = vazduhTemp;
        temperatureChart.update();
    }
    
    // Ažuriraj humidity chart
    if (humidityChart) {
        humidityChart.data.labels = labels;
        humidityChart.data.datasets[0].data = betonHumidity;
        humidityChart.data.datasets[1].data = vazduhHumidity;
        humidityChart.update();
    }
    
    console.log('📊 Charts updated successfully');
}

function updateChartsWithSensorHistory(betonHistory, vazduhHistory) {
    console.log('📊 Updating charts with sensor history...');
    
    // Pripremi podatke za chartove
    const labels = [];
    const betonTemp = [];
    const vazduhTemp = [];
    const betonHumidity = [];
    const vazduhHumidity = [];
    
    // Kombinuj i sortiraj sve podatke po vremenu (najstariji prvi za chart)
    const allData = [
        ...betonHistory.map(item => ({...item, source: 'beton'})),
        ...vazduhHistory.map(item => ({...item, source: 'vazduh'}))
    ].sort((a, b) => new Date(a.sim_time) - new Date(b.sim_time));
    
    // Grupiši po vremenu (round na 10 minuta)
    const dataByTime = {};
    
    allData.forEach(item => {
        const timeKey = item.timestamp; // Koristi timestamp kao ključ
        
        if (!dataByTime[timeKey]) {
            dataByTime[timeKey] = {
                time: timeKey,
                sim_time: item.sim_time,
                beton_temp: null,
                beton_humidity: null,
                vazduh_temp: null,
                vazduh_humidity: null
            };
        }
        
        if (item.source === 'beton') {
            dataByTime[timeKey].beton_temp = item.temperatura;
            dataByTime[timeKey].beton_humidity = item.vlaznost;
        } else {
            dataByTime[timeKey].vazduh_temp = item.temperatura;
            dataByTime[timeKey].vazduh_humidity = item.vlaznost;
        }
    });
    
    // Konvertuj u nižove za chartove
    Object.values(dataByTime)
        .sort((a, b) => new Date(a.sim_time) - new Date(b.sim_time))
        .slice(-50) // Uzmi poslednih 50 tačaka
        .forEach(item => {
            // Format vreme za prikaz
            const time = new Date(item.sim_time);
            const timeLabel = time.toLocaleTimeString('sr-RS', { 
                hour: '2-digit', 
                minute: '2-digit',
                day: '2-digit',
                month: '2-digit'
            });
            
            labels.push(timeLabel);
            betonTemp.push(item.beton_temp);
            vazduhTemp.push(item.vazduh_temp);
            betonHumidity.push(item.beton_humidity);
            vazduhHumidity.push(item.vazduh_humidity);
        });
    
    console.log('📊 Chart data prepared:', { labels, betonTemp, vazduhTemp });
    
    // Ažuriraj temperature chart
    temperatureChart.data.labels = labels;
    temperatureChart.data.datasets[0].data = betonTemp;
    temperatureChart.data.datasets[1].data = vazduhTemp;
    temperatureChart.update();
    
    // Ažuriraj humidity chart  
    humidityChart.data.labels = labels;
    humidityChart.data.datasets[0].data = betonHumidity;
    humidityChart.data.datasets[1].data = vazduhHumidity;
    humidityChart.update();
    
    console.log('✅ Charts updated successfully');
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

// Notification management
let notificationsList = [];
let notificationsCache = new Map();

// Load notifications from backend
async function loadNotifications() {
    try {
        console.log('📮 Loading notifications from backend...');
        
        const response = await fetch(`${API_BASE_URL}/notifikacije`);
        console.log('📮 Notifications API response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📮 Notifications data received:', data);
        
        if (data.success) {
            const newNotifications = data.notifikacije || [];
            const newCount = newNotifications.length;
            const previousCount = notificationsList.length;
            
            // Check for new notifications
            if (newCount > previousCount && previousCount > 0) {
                const newNotificationCount = newCount - previousCount;
                console.log(`🆕 ${newNotificationCount} new notification(s) received!`);
                showNotificationToast(`${newNotificationCount} nova notifikacija`, 'info');
            }
            
            notificationsList = newNotifications;
            console.log(`📮 Loaded ${notificationsList.length} notifications`);
            updateNotificationsDisplay();
            updateNotificationsStats();
        } else {
            console.error('❌ Error loading notifications:', data.error);
            showNotificationsError('Greška pri učitavanju notifikacija');
        }
    } catch (error) {
        console.error('❌ Failed to load notifications:', error);
        showNotificationsError('Greška pri učitavanju notifikacija');
    }
}

// Show/hide loading spinner
function showNotificationsLoading(show) {
    const container = document.getElementById('notifications-list');
    if (show) {
        container.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Učitavanje notifikacija...</p>
            </div>
        `;
    }
}

// Show error message
function showNotificationsError(message) {
    const container = document.getElementById('notifications-list');
    container.innerHTML = `
        <div class="notifications-empty">
            <i class="fas fa-exclamation-triangle"></i>
            <p>${message}</p>
            <button onclick="loadNotifications()" class="btn btn-primary">Pokušaj ponovo</button>
        </div>
    `;
}

// Update notifications display
function updateNotificationsDisplay() {
    console.log('🔔 updateNotificationsDisplay called with', notificationsList.length, 'notifications');
    const container = document.getElementById('notifications-list');
    
    if (!container) {
        console.error('❌ notifications-list element not found!');
        return;
    }
    
    if (!notificationsList || notificationsList.length === 0) {
        console.log('📝 No notifications to display');
        container.innerHTML = `
            <div class="notifications-empty">
                <i class="fas fa-bell-slash"></i>
                <h4>Nema notifikacija</h4>
                <p>Trenutno nema novih notifikacija.</p>
            </div>
        `;
        return;
    }
    
    // Sort notifications by time (newest first)
    const sortedNotifications = [...notificationsList].sort((a, b) => 
        new Date(b.vreme) - new Date(a.vreme)
    );
    
    const html = sortedNotifications.map(notification => 
        createNotificationHTML(notification)
    ).join('');
    
    container.innerHTML = html;
}

// Create HTML for single notification
function createNotificationHTML(notification) {
    const readClass = notification.procitana ? 'read' : 'unread';
    const typeClass = getNotificationTypeClass(notification.tip);
    const formattedTime = formatNotificationTime(notification.vreme);
    
    return `
        <div class="notification-item ${readClass} ${typeClass}" data-id="${notification.id}">
            <div class="notification-header">
                <h5 class="notification-title">
                    ${notification.procitana ? '' : '<i class="fas fa-circle" style="font-size: 0.5em; color: #2196f3; margin-right: 8px;"></i>'}
                    ${escapeHtml(notification.tip.toUpperCase())}
                </h5>
                <span class="notification-time">${formattedTime}</span>
            </div>
            <div class="notification-message">
                ${escapeHtml(notification.poruka)}
            </div>
            <div class="notification-actions">
                ${!notification.procitana ? 
                    `<button class="btn btn-mark-read" onclick="markNotificationAsRead(${notification.id})">
                        <i class="fas fa-check"></i> Označiti kao pročitano
                    </button>` :
                    `<span class="read-status"><i class="fas fa-check-circle"></i> Pročitana</span>`
                }
                <button class="btn btn-delete" onclick="deleteNotification(${notification.id})">
                    <i class="fas fa-trash"></i> Obriši
                </button>
            </div>
        </div>
    `;
}

// Get notification type class for styling
function getNotificationTypeClass(tip) {
    const type = tip.toLowerCase();
    if (type.includes('critical') || type.includes('kritična') || type.includes('greška')) {
        return 'critical';
    } else if (type.includes('warning') || type.includes('upozorenje')) {
        return 'warning';
    } else {
        return 'info';
    }
}

// Format notification time
function formatNotificationTime(timeString) {
    try {
        const date = new Date(timeString);
        const now = getCurrentSimTime();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) {
            return 'Upravo';
        } else if (diffMins < 60) {
            return `Pre ${diffMins} min`;
        } else if (diffHours < 24) {
            return `Pre ${diffHours} h`;
        } else if (diffDays < 7) {
            return `Pre ${diffDays} dana`;
        } else {
            return date.toLocaleDateString('sr-RS', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    } catch (error) {
        return timeString;
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Update notifications statistics
function updateNotificationsStats() {
    const total = notificationsList.length;
    const unread = notificationsList.filter(n => !n.procitana).length;
    const read = total - unread;
    
    const totalElement = document.getElementById('total-notifications');
    const unreadElement = document.getElementById('unread-notifications');
    const readElement = document.getElementById('read-notifications');
    
    if (totalElement) totalElement.textContent = `Ukupno: ${total}`;
    if (unreadElement) unreadElement.textContent = `Nepročitane: ${unread}`;
    if (readElement) readElement.textContent = `Pročitane: ${read}`;
    
    // Update tab badge
    updateNotificationBadge(unread);
}

// Mark notification as read
async function markNotificationAsRead(notificationId) {
    try {
        console.log('📝 Marking notification as read:', notificationId);
        
        const response = await fetch(`${API_BASE_URL}/notifikacije/procitaj`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: notificationId })
        });
        
        console.log('📝 Mark as read response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📝 Mark as read response data:', data);
        
        if (data.success) {
            console.log('✅ Notification marked as read successfully');
            // Reload notifications to reflect changes
            loadNotifications();
            showNotificationToast('Notifikacija označena kao pročitana', 'success');
        } else {
            console.error('❌ Failed to mark notification as read:', data.error);
            showNotificationToast('Greška pri ažuriranju notifikacije', 'error');
        }
    } catch (error) {
        console.error('❌ Error marking notification as read:', error);
        showNotificationToast('Greška pri ažuriranju notifikacije', 'error');
    }
}

// Delete single notification
async function deleteNotification(notificationId) {
    if (!confirm('Da li ste sigurni da želite da obrišete ovu notifikaciju?')) {
        return;
    }
    
    try {
        console.log('🗑️ Deleting notification:', notificationId);
        
        const response = await fetch(`${API_BASE_URL}/notifikacije/${notificationId}`, {
            method: 'DELETE'
        });
        
        console.log('🗑️ Delete notification response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('🗑️ Delete notification response data:', data);
        
        if (data.success) {
            console.log('✅ Notification deleted successfully');
            // Reload notifications to reflect changes
            loadNotifications();
            showNotificationToast('Notifikacija obrisana', 'success');
        } else {
            console.error('❌ Failed to delete notification:', data.error);
            showNotificationToast('Greška pri brisanju notifikacije', 'error');
        }
    } catch (error) {
        console.error('❌ Error deleting notification:', error);
        showNotificationToast('Greška pri brisanju notifikacije', 'error');
    }
}

// Mark all notifications as read
async function markAllNotificationsAsRead() {
    try {
        console.log('✅ Marking all notifications as read...');
        
        const response = await fetch(`${API_BASE_URL}/notifikacije/procitaj-sve`, {
            method: 'POST'
        });
        
        console.log('✅ Mark all as read response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Mark all as read response data:', data);
        
        if (data.success) {
            console.log('✅ All notifications marked as read successfully');
            // Reload notifications to reflect changes
            loadNotifications();
            showNotificationToast('Sve notifikacije označene kao pročitane', 'success');
        } else {
            console.error('❌ Failed to mark all notifications as read:', data.error);
            showNotificationToast('Greška pri ažuriranju notifikacija', 'error');
        }
    } catch (error) {
        console.error('❌ Error marking all notifications as read:', error);
        showNotificationToast('Greška pri ažuriranju notifikacija', 'error');
    }
}

// Clear read notifications
async function clearReadNotifications() {
    const readCount = notificationsList.filter(n => n.procitana).length;
    
    if (readCount === 0) {
        showNotificationToast('Nema pročitanih notifikacija za brisanje', 'info');
        return;
    }
    
    if (!confirm(`Da li ste sigurni da želite da obrišete ${readCount} pročitanih notifikacija?`)) {
        return;
    }
    
    try {
        console.log('🗑️ Deleting read notifications...');
        
        const response = await fetch(`${API_BASE_URL}/notifikacije/obrisi-procitane`, {
            method: 'DELETE'
        });
        
        console.log('🗑️ Delete read notifications response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('🗑️ Delete read notifications response data:', data);
        
        if (data.success) {
            console.log('✅ Read notifications deleted successfully');
            // Reload notifications to reflect changes
            loadNotifications();
            showNotificationToast(`Obrisano ${readCount} pročitanih notifikacija`, 'success');
        } else {
            console.error('❌ Failed to delete read notifications:', data.error);
            showNotificationToast('Greška pri brisanju notifikacija', 'error');
        }
    } catch (error) {
        console.error('❌ Error deleting read notifications:', error);
        showNotificationToast('Greška pri brisanju notifikacija', 'error');
    }
}

// Clear all notifications
async function clearAllNotifications() {
    if (notificationsList.length === 0) {
        showNotificationToast('Nema notifikacija za brisanje', 'info');
        return;
    }
    
    if (!confirm(`Da li ste sigurni da želite da obrišete sve (${notificationsList.length}) notifikacije?`)) {
        return;
    }
    
    try {
        console.log('🗑️ Deleting all notifications...');
        
        const response = await fetch(`${API_BASE_URL}/notifikacije/obrisi-sve`, {
            method: 'DELETE'
        });
        
        console.log('🗑️ Delete all notifications response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('🗑️ Delete all notifications response data:', data);
        
        if (data.success) {
            const deletedCount = notificationsList.length;
            console.log(`✅ All ${deletedCount} notifications deleted successfully`);
            // Reload notifications to reflect changes
            loadNotifications();
            showNotificationToast(`Obrisano ${deletedCount} notifikacija`, 'success');
        } else {
            console.error('❌ Failed to delete all notifications:', data.error);
            showNotificationToast('Greška pri brisanju notifikacija', 'error');
        }
    } catch (error) {
        console.error('❌ Error deleting all notifications:', error);
        showNotificationToast('Greška pri brisanju notifikacija', 'error');
    }
}

// Show notification toast
function showNotificationToast(message, type = 'info') {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.notification-toast');
    existingToasts.forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = `notification-toast ${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'} toast-icon ${type}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Hide toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Update notification badge in tab
function updateNotificationBadge(count) {
    console.log('🔔 Updating notification badge with count:', count);
    
    // Try the direct badge element first
    const badge = document.getElementById('notification-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'inline-flex';
        } else {
            badge.style.display = 'none';
        }
        return;
    }
    
    // Fallback to the old method
    const notificationsTab = document.querySelector('[data-tab="notifications"]');
    if (notificationsTab) {
        let tabBadge = notificationsTab.querySelector('.badge');
        
        if (count > 0) {
            if (!tabBadge) {
                tabBadge = document.createElement('span');
                tabBadge.className = 'badge';
                notificationsTab.appendChild(tabBadge);
            }
            tabBadge.textContent = count > 99 ? '99+' : count;
            tabBadge.style.display = 'inline-flex';
        } else if (tabBadge) {
            tabBadge.style.display = 'none';
        }
    }
}

// CSS for battery levels (injected dynamically)
const style = document.createElement('style');
style.textContent = `
    .battery-level::before {
        width: var(--battery-level, 0%);
    }
`;
document.head.appendChild(style);

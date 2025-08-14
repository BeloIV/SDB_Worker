// API utility functions

// Get the API URL from environment variables or use a default
// When running in the browser, replace 'backend' with 'localhost' in the URL
const apiUrl = process.env.REACT_APP_API_URL || '/api';
// Check if we're running in a browser environment
const isBrowser = typeof window !== 'undefined';
// Replace 'backend' with 'localhost' if we're in a browser
const API_URL = isBrowser && apiUrl.includes('backend') 
  ? apiUrl.replace('backend', 'localhost') 
  : apiUrl;

/**
 * Make a request to the API
 * @param {string} endpoint - The API endpoint (without the /api prefix)
 * @param {Object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<Object>} - The response data
 */
export const apiRequest = async (endpoint, options = {}) => {
  // Ensure endpoint starts with a slash
  const formattedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // Construct the full URL
  const url = `${API_URL}${formattedEndpoint}`;

  // Set default headers if not provided
  const headers = options.headers || {
    'Content-Type': 'application/json',
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Check if response is ok
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Check if response has content
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error('Response is not JSON');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

/**
 * Get team schedule for a specific date
 * @param {string} teamPassword - The team password
 * @param {string} date - The date in YYYY-MM-DD format
 * @returns {Promise<Object>} - The schedule data
 */
export const getTeamScheduleForDate = async (teamPassword, date) => {
  return apiRequest('/get-schedule-for-date/', {
    method: 'POST',
    body: JSON.stringify({
      team_password: teamPassword,
      date,
    }),
  });
};

/**
 * Get task details
 * @param {number} taskId - The task ID
 * @param {string} teamPassword - The team password
 * @returns {Promise<Object>} - The task data
 */
export const getTaskDetails = async (taskId, teamPassword) => {
  return apiRequest('/get-task-details/', {
    method: 'POST',
    body: JSON.stringify({
      task_id: taskId,
      team_password: teamPassword,
    }),
  });
};

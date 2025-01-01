import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000/api';

/**
 * Validate a referral code
 * @param {string} code - The referral code to validate
 * @returns {Promise<Object>} Validation result
 */
export const validateReferralCode = async (code) => {
  try {
    const response = await axios.post(`${API_URL}/referral/validate`, { code });
    return response.data;
  } catch (error) {
    if (error.response) {
      return error.response.data;
    }
    throw error;
  }
};

/**
 * Use a referral code
 * @param {string} code - The referral code to use
 * @param {string} userId - The ID of the user using the code
 * @returns {Promise<Object>} Usage result
 */
export const useReferralCode = async (code, userId) => {
  try {
    const response = await axios.post(`${API_URL}/referral/use`, { code, userId });
    return response.data;
  } catch (error) {
    if (error.response) {
      return error.response.data;
    }
    throw error;
  }
};

/**
 * Generate a new referral code
 * @param {number} maxUses - Maximum number of times the code can be used
 * @returns {Promise<Object>} Generated code details
 */
export const generateReferralCode = async (maxUses) => {
  try {
    const token = await getAuthToken();
    const response = await axios.post(
      `${API_URL}/referral/generate`,
      { maxUses },
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );
    return response.data;
  } catch (error) {
    if (error.response) {
      return error.response.data;
    }
    throw error;
  }
};

/**
 * Get referral statistics
 * @returns {Promise<Object>} Referral statistics
 */
export const getReferralStats = async () => {
  try {
    const token = await getAuthToken();
    const response = await axios.get(
      `${API_URL}/referral/stats`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );
    return response.data;
  } catch (error) {
    if (error.response) {
      return error.response.data;
    }
    throw error;
  }
};

/**
 * Get detailed analytics for a specific code
 * @param {string} code - The referral code to get analytics for
 * @returns {Promise<Object>} Code analytics
 */
export const getCodeAnalytics = async (code) => {
  try {
    const token = await getAuthToken();
    const response = await axios.get(
      `${API_URL}/referral/stats/${code}`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );
    return response.data;
  } catch (error) {
    if (error.response) {
      return error.response.data;
    }
    throw error;
  }
};

// Helper function to get auth token
const getAuthToken = async () => {
  // This should be implemented based on your authentication system
  // For Firebase, you would use firebase.auth().currentUser.getIdToken()
  const user = await firebase.auth().currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }
  return user.getIdToken();
}; 
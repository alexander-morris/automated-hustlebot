const { db } = require('../config/firebase');

/**
 * Validate a referral code
 * @param {string} code - The referral code to validate
 * @returns {Promise<Object>} Validation result
 */
async function validateReferralCode(code) {
  try {
    // Check code format
    if (!code.match(/^[A-Z0-9]{8}$/)) {
      return {
        valid: false,
        message: 'Invalid code format'
      };
    }

    // Check if code exists
    const codeRef = db.collection('referralCodes').where('code', '==', code);
    const codeDoc = await codeRef.get();

    if (codeDoc.empty) {
      return {
        valid: false,
        message: 'Invalid code'
      };
    }

    const codeData = codeDoc.docs[0].data();

    // Check if code is active
    if (!codeData.active) {
      return {
        valid: false,
        message: 'Code is inactive'
      };
    }

    // Check if code has expired
    if (codeData.usedCount >= codeData.maxUses) {
      return {
        valid: false,
        message: 'Code has expired'
      };
    }

    return {
      valid: true,
      maxUses: codeData.maxUses,
      remainingUses: codeData.maxUses - codeData.usedCount
    };
  } catch (error) {
    console.error('Error validating code:', error);
    throw error;
  }
}

module.exports = {
  validateReferralCode
}; 
const ReferralCode = require('../models/ReferralCode');

class ReferralController {
  async validateCode(code) {
    const referralCode = await ReferralCode.findOne({ code });
    
    if (!referralCode) {
      throw new Error('Invalid referral code');
    }

    if (!referralCode.isActive) {
      throw new Error('Referral code is inactive');
    }

    if (referralCode.usedCount >= referralCode.usageLimit) {
      throw new Error('Referral code has reached usage limit');
    }

    if (referralCode.expiresAt < new Date()) {
      throw new Error('Referral code has expired');
    }

    return referralCode;
  }

  async useCode(code) {
    const referralCode = await this.validateCode(code);
    referralCode.usedCount += 1;
    
    if (referralCode.usedCount >= referralCode.usageLimit) {
      referralCode.isActive = false;
    }

    await referralCode.save();
    return referralCode;
  }
}

module.exports = new ReferralController(); 
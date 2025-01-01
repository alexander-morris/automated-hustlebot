const express = require('express');
const router = express.Router();
const { db } = require('../config/firebase');
const { auth } = require('../middleware/auth');
const { validateReferralCode } = require('../utils/validation');

// Generate new referral code
router.post('/generate', auth, async (req, res) => {
  try {
    const maxUses = req.body.maxUses || 1;
    const code = generateCode();
    
    await db.collection('referralCodes').add({
      code,
      maxUses,
      usedCount: 0,
      createdAt: new Date(),
      active: true,
      createdBy: req.user.uid
    });

    res.json({ code, maxUses, usedCount: 0 });
  } catch (error) {
    console.error('Error generating referral code:', error);
    res.status(500).json({ error: 'Failed to generate code' });
  }
});

// Validate referral code
router.post('/validate', async (req, res) => {
  try {
    const { code } = req.body;
    if (!code) {
      return res.status(400).json({ valid: false, message: 'Code is required' });
    }

    const validationResult = await validateReferralCode(code);
    if (!validationResult.valid) {
      return res.status(400).json(validationResult);
    }

    res.json(validationResult);
  } catch (error) {
    console.error('Error validating referral code:', error);
    res.status(500).json({ error: 'Failed to validate code' });
  }
});

// Use referral code
router.post('/use', async (req, res) => {
  try {
    const { code, userId } = req.body;
    if (!code || !userId) {
      return res.status(400).json({ error: 'Code and userId are required' });
    }

    const codeRef = db.collection('referralCodes').where('code', '==', code);
    const codeDoc = await codeRef.get();

    if (codeDoc.empty) {
      return res.status(400).json({ error: 'Invalid code' });
    }

    const codeData = codeDoc.docs[0].data();
    if (codeData.usedCount >= codeData.maxUses) {
      return res.status(400).json({ error: 'Code has expired' });
    }

    // Update usage count
    await codeDoc.docs[0].ref.update({
      usedCount: codeData.usedCount + 1
    });

    // Record usage
    await db.collection('referralUsage').add({
      code,
      userId,
      usedAt: new Date()
    });

    res.json({ success: true });
  } catch (error) {
    console.error('Error using referral code:', error);
    res.status(500).json({ error: 'Failed to use code' });
  }
});

// Get referral statistics
router.get('/stats', auth, async (req, res) => {
  try {
    const codesSnapshot = await db.collection('referralCodes').get();
    const usageSnapshot = await db.collection('referralUsage').get();

    const stats = {
      totalCodes: codesSnapshot.size,
      totalUses: usageSnapshot.size,
      activeReferrals: 0
    };

    codesSnapshot.forEach(doc => {
      const data = doc.data();
      if (data.usedCount < data.maxUses) {
        stats.activeReferrals++;
      }
    });

    res.json(stats);
  } catch (error) {
    console.error('Error getting referral stats:', error);
    res.status(500).json({ error: 'Failed to get statistics' });
  }
});

// Get detailed code analytics
router.get('/stats/:code', auth, async (req, res) => {
  try {
    const { code } = req.params;
    const codeRef = db.collection('referralCodes').where('code', '==', code);
    const codeDoc = await codeRef.get();

    if (codeDoc.empty) {
      return res.status(404).json({ error: 'Code not found' });
    }

    const codeData = codeDoc.docs[0].data();
    const usageHistory = await db.collection('referralUsage')
      .where('code', '==', code)
      .orderBy('usedAt', 'desc')
      .get();

    const analytics = {
      code,
      usageRate: codeData.usedCount / codeData.maxUses,
      totalUses: codeData.usedCount,
      maxUses: codeData.maxUses,
      createdAt: codeData.createdAt,
      usageHistory: usageHistory.docs.map(doc => doc.data())
    };

    res.json(analytics);
  } catch (error) {
    console.error('Error getting code analytics:', error);
    res.status(500).json({ error: 'Failed to get analytics' });
  }
});

// Helper function to generate random code
function generateCode(length = 8) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let code = '';
  for (let i = 0; i < length; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

module.exports = router; 
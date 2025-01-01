const express = require('express');
const router = express.Router();
const referralController = require('../controllers/referralController');

router.post('/validate', async (req, res) => {
  try {
    const { code } = req.body;
    const referralCode = await referralController.validateCode(code);
    res.json({ valid: true, code: referralCode });
  } catch (error) {
    res.status(400).json({ valid: false, error: error.message });
  }
});

router.post('/use', async (req, res) => {
  try {
    const { code } = req.body;
    const result = await referralController.useCode(code);
    res.json({ success: true, code: result });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

module.exports = router; 
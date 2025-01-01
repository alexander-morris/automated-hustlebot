const request = require('supertest');
const { app } = require('../app');
const { db } = require('../config/firebase');

describe('Referral Gating System', () => {
  beforeEach(async () => {
    // Clear test data
    const referralCodes = await db.collection('referralCodes').get();
    const batch = db.batch();
    referralCodes.forEach(doc => batch.delete(doc.ref));
    await batch.commit();
  });

  describe('Code Generation', () => {
    test('should generate valid referral code', async () => {
      const res = await request(app)
        .post('/api/referral/generate')
        .send({ maxUses: 5 });

      expect(res.status).toBe(200);
      expect(res.body.code).toMatch(/^[A-Z0-9]{8}$/);
      expect(res.body.maxUses).toBe(5);
      expect(res.body.usedCount).toBe(0);
    });

    test('should require authentication for code generation', async () => {
      const res = await request(app)
        .post('/api/referral/generate');

      expect(res.status).toBe(401);
    });
  });

  describe('Code Validation', () => {
    let validCode;

    beforeEach(async () => {
      // Create a test code
      const codeDoc = await db.collection('referralCodes').add({
        code: 'TEST1234',
        maxUses: 2,
        usedCount: 0,
        createdAt: new Date(),
        active: true
      });
      validCode = (await codeDoc.get()).data();
    });

    test('should validate existing code', async () => {
      const res = await request(app)
        .post('/api/referral/validate')
        .send({ code: 'TEST1234' });

      expect(res.status).toBe(200);
      expect(res.body.valid).toBe(true);
    });

    test('should reject invalid code', async () => {
      const res = await request(app)
        .post('/api/referral/validate')
        .send({ code: 'INVALID1' });

      expect(res.status).toBe(400);
      expect(res.body.valid).toBe(false);
    });

    test('should reject expired code', async () => {
      await db.collection('referralCodes')
        .doc(validCode.id)
        .update({ usedCount: 2 });

      const res = await request(app)
        .post('/api/referral/validate')
        .send({ code: 'TEST1234' });

      expect(res.status).toBe(400);
      expect(res.body.valid).toBe(false);
      expect(res.body.message).toContain('expired');
    });
  });

  describe('Code Usage Tracking', () => {
    let trackingCode;

    beforeEach(async () => {
      const codeDoc = await db.collection('referralCodes').add({
        code: 'TRACK123',
        maxUses: 3,
        usedCount: 0,
        createdAt: new Date(),
        active: true
      });
      trackingCode = (await codeDoc.get()).data();
    });

    test('should increment usage count', async () => {
      const res = await request(app)
        .post('/api/referral/use')
        .send({ code: 'TRACK123' });

      expect(res.status).toBe(200);
      
      const updatedCode = await db.collection('referralCodes')
        .doc(trackingCode.id)
        .get();
      
      expect(updatedCode.data().usedCount).toBe(1);
    });

    test('should track user who used code', async () => {
      const res = await request(app)
        .post('/api/referral/use')
        .send({
          code: 'TRACK123',
          userId: 'testUser123'
        });

      expect(res.status).toBe(200);
      
      const usage = await db.collection('referralUsage')
        .where('code', '==', 'TRACK123')
        .where('userId', '==', 'testUser123')
        .get();
      
      expect(usage.empty).toBe(false);
      expect(usage.docs[0].data().usedAt).toBeTruthy();
    });
  });

  describe('Analytics', () => {
    beforeEach(async () => {
      // Create test data
      await db.collection('referralCodes').add({
        code: 'STATS123',
        maxUses: 5,
        usedCount: 3,
        createdAt: new Date(Date.now() - 86400000), // 1 day ago
        active: true
      });
    });

    test('should return usage statistics', async () => {
      const res = await request(app)
        .get('/api/referral/stats');

      expect(res.status).toBe(200);
      expect(res.body).toHaveProperty('totalCodes');
      expect(res.body).toHaveProperty('totalUses');
      expect(res.body).toHaveProperty('activeReferrals');
    });

    test('should return detailed code analytics', async () => {
      const res = await request(app)
        .get('/api/referral/stats/STATS123');

      expect(res.status).toBe(200);
      expect(res.body.code).toBe('STATS123');
      expect(res.body.usageRate).toBe(0.6); // 3/5 uses
      expect(res.body).toHaveProperty('usageHistory');
    });
  });
}); 
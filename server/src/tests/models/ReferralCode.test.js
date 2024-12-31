const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const ReferralCode = require('../../models/ReferralCode');

let mongoServer;

beforeAll(async () => {
  mongoServer = await MongoMemoryServer.create();
  await mongoose.connect(mongoServer.getUri());
});

afterAll(async () => {
  await mongoose.disconnect();
  await mongoServer.stop();
});

describe('ReferralCode Model Test', () => {
  it('should create & save referral code successfully', async () => {
    const validCode = new ReferralCode({
      code: 'TEST123',
      usageLimit: 5,
      createdBy: 'system',
      expiresAt: new Date(Date.now() + 86400000) // 24 hours from now
    });
    const savedCode = await validCode.save();
    
    expect(savedCode._id).toBeDefined();
    expect(savedCode.code).toBe('TEST123');
    expect(savedCode.usedCount).toBe(0);
    expect(savedCode.isActive).toBe(true);
  });
}); 
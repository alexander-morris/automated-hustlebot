// Set up environment variables for testing
process.env.NODE_ENV = 'test';
process.env.FIREBASE_DATABASE_URL = 'http://localhost:8080';

// Mock Firebase Admin
jest.mock('firebase-admin', () => ({
  credential: {
    applicationDefault: jest.fn().mockReturnValue({})
  },
  initializeApp: jest.fn(),
  firestore: jest.fn().mockReturnValue({
    collection: jest.fn().mockReturnValue({
      add: jest.fn(),
      get: jest.fn(),
      where: jest.fn(),
      doc: jest.fn()
    })
  }),
  auth: jest.fn().mockReturnValue({
    verifyIdToken: jest.fn().mockResolvedValue({
      uid: 'test-uid',
      email: 'test@example.com',
      email_verified: true
    })
  }),
  apps: []
})); 
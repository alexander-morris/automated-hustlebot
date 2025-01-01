import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { validateReferralCode } from '../api/referral';
import {
  Box,
  Button,
  Container,
  TextField,
  Typography,
  Alert,
  Paper
} from '@mui/material';

const ReferralGate = () => {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await validateReferralCode(code);
      if (result.valid) {
        // Store code in session
        sessionStorage.setItem('referralCode', code);
        // Redirect to registration
        navigate('/register');
      } else {
        setError(result.message || 'Invalid referral code');
      }
    } catch (err) {
      setError('Failed to validate code. Please try again.');
      console.error('Referral validation error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            Welcome to HustleBot
          </Typography>
          
          <Typography variant="body1" sx={{ mb: 4 }} align="center">
            Enter your referral code to get started
          </Typography>

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Referral Code"
              variant="outlined"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="Enter your code"
              sx={{ mb: 3 }}
              inputProps={{
                maxLength: 8,
                style: { textTransform: 'uppercase' }
              }}
            />

            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              size="large"
              disabled={loading || code.length !== 8}
            >
              {loading ? 'Validating...' : 'Continue'}
            </Button>
          </form>
        </Paper>
      </Box>
    </Container>
  );
};

export default ReferralGate; 
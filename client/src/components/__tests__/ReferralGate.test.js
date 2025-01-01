import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ReferralGate from '../ReferralGate';
import { validateReferralCode } from '../../api/referral';

// Mock the referral API
jest.mock('../../api/referral');

// Mock the react-router-dom useNavigate hook
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

describe('ReferralGate', () => {
  beforeEach(() => {
    // Clear mocks before each test
    jest.clearAllMocks();
  });

  it('renders the referral gate form', () => {
    render(
      <MemoryRouter>
        <ReferralGate />
      </MemoryRouter>
    );

    expect(screen.getByText(/Welcome to HustleBot/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Referral Code/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Continue/i })).toBeInTheDocument();
  });

  it('validates input format', () => {
    render(
      <MemoryRouter>
        <ReferralGate />
      </MemoryRouter>
    );

    const input = screen.getByLabelText(/Referral Code/i);
    const submitButton = screen.getByRole('button', { name: /Continue/i });

    // Button should be disabled with empty input
    expect(submitButton).toBeDisabled();

    // Enter invalid length code
    fireEvent.change(input, { target: { value: 'ABC123' } });
    expect(submitButton).toBeDisabled();

    // Enter valid length code
    fireEvent.change(input, { target: { value: 'ABCD1234' } });
    expect(submitButton).not.toBeDisabled();
  });

  it('handles valid referral code submission', async () => {
    validateReferralCode.mockResolvedValueOnce({ valid: true });

    render(
      <MemoryRouter>
        <ReferralGate />
      </MemoryRouter>
    );

    const input = screen.getByLabelText(/Referral Code/i);
    const submitButton = screen.getByRole('button', { name: /Continue/i });

    fireEvent.change(input, { target: { value: 'ABCD1234' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(validateReferralCode).toHaveBeenCalledWith('ABCD1234');
      expect(mockNavigate).toHaveBeenCalledWith('/register');
    });
  });

  it('handles invalid referral code submission', async () => {
    validateReferralCode.mockResolvedValueOnce({
      valid: false,
      message: 'Invalid referral code'
    });

    render(
      <MemoryRouter>
        <ReferralGate />
      </MemoryRouter>
    );

    const input = screen.getByLabelText(/Referral Code/i);
    const submitButton = screen.getByRole('button', { name: /Continue/i });

    fireEvent.change(input, { target: { value: 'ABCD1234' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Invalid referral code/i)).toBeInTheDocument();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  it('handles API errors gracefully', async () => {
    validateReferralCode.mockRejectedValueOnce(new Error('API Error'));

    render(
      <MemoryRouter>
        <ReferralGate />
      </MemoryRouter>
    );

    const input = screen.getByLabelText(/Referral Code/i);
    const submitButton = screen.getByRole('button', { name: /Continue/i });

    fireEvent.change(input, { target: { value: 'ABCD1234' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Failed to validate code/i)).toBeInTheDocument();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  it('converts input to uppercase', () => {
    render(
      <MemoryRouter>
        <ReferralGate />
      </MemoryRouter>
    );

    const input = screen.getByLabelText(/Referral Code/i);
    fireEvent.change(input, { target: { value: 'abcd1234' } });
    expect(input.value).toBe('ABCD1234');
  });

  it('shows loading state during validation', async () => {
    validateReferralCode.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    render(
      <MemoryRouter>
        <ReferralGate />
      </MemoryRouter>
    );

    const input = screen.getByLabelText(/Referral Code/i);
    const submitButton = screen.getByRole('button', { name: /Continue/i });

    fireEvent.change(input, { target: { value: 'ABCD1234' } });
    fireEvent.click(submitButton);

    expect(screen.getByText(/Validating/i)).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });
}); 
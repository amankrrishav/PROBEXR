/**
 * AuthModal component tests — A-37
 *
 * Covers all major view transitions:
 *   login / signup / forgot / reset / unverified banner
 * Plus: form submission, error display, magic link toggle.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import AuthModal from '../AuthModal.jsx';

// ── Service mocks ────────────────────────────────────────────────────────

const mockRequestMagicLink = vi.fn();
const mockForgotPassword = vi.fn();
const mockResetPassword = vi.fn();
const mockResendVerification = vi.fn();

vi.mock('../../../services/auth.js', () => ({
    requestMagicLink: (...args) => mockRequestMagicLink(...args),
    forgotPassword: (...args) => mockForgotPassword(...args),
    resetPassword: (...args) => mockResetPassword(...args),
    resendVerification: (...args) => mockResendVerification(...args),
}));

// ── Default props ────────────────────────────────────────────────────────

const defaultProps = {
    open: true,
    mode: 'login',
    onModeChange: vi.fn(),
    onClose: vi.fn(),
    onLogin: vi.fn(),
    onRegister: vi.fn(),
    submitting: false,
    error: null,
    onSuccess: vi.fn(),
    user: null,
};

function renderModal(overrides = {}) {
    return render(<AuthModal {...defaultProps} {...overrides} />);
}

beforeEach(() => {
    vi.clearAllMocks();
});

// ── Visibility ───────────────────────────────────────────────────────────

describe('AuthModal visibility', () => {
    it('renders nothing when open=false', () => {
        renderModal({ open: false });
        expect(screen.queryByText('Welcome back')).toBeNull();
    });

    it('renders login view when open=true and mode=login', () => {
        renderModal({ open: true, mode: 'login' });
        expect(screen.getByText('Welcome back')).toBeTruthy();
    });

    it('renders signup view when mode=signup', () => {
        renderModal({ open: true, mode: 'signup' });
        expect(screen.getByText('Create your PROBEXR account')).toBeTruthy();
    });
});

// ── Tab switching ────────────────────────────────────────────────────────

describe('AuthModal tab switching', () => {
    it('switches to signup view when Sign up tab is clicked', () => {
        renderModal({ mode: 'login' });
        fireEvent.click(screen.getByText('Sign up'));
        expect(screen.getByText('Create your PROBEXR account')).toBeTruthy();
    });

    it('switches back to login view when Log in tab is clicked', () => {
        renderModal({ mode: 'signup' });
        fireEvent.click(screen.getByText('Log in'));
        expect(screen.getByText('Welcome back')).toBeTruthy();
    });
});

// ── Login form ───────────────────────────────────────────────────────────

describe('AuthModal login form', () => {
    it('calls onLogin with email and password on submit', async () => {
        defaultProps.onLogin.mockResolvedValue(undefined);
        renderModal({ mode: 'login' });

        fireEvent.change(screen.getByPlaceholderText('you@company.com'), {
            target: { value: 'user@example.com' },
        });
        fireEvent.change(screen.getByPlaceholderText('Your password'), {
            target: { value: 'Password123!' },
        });

        await act(async () => {
            // Two "Log in" elements exist (tab + submit button) — target the submit
            const submitBtn = screen.getAllByText('Log in').find(
                el => el.getAttribute('type') === 'submit'
            );
            fireEvent.click(submitBtn);
        });

        expect(defaultProps.onLogin).toHaveBeenCalledWith({
            email: 'user@example.com',
            password: 'Password123!',
        });
    });

    it('shows external error prop', () => {
        renderModal({ mode: 'login', error: 'Invalid credentials' });
        expect(screen.getByText('Invalid credentials')).toBeTruthy();
    });

    it('shows submitting state on button when submitting=true', () => {
        renderModal({ mode: 'login', submitting: true });
        expect(screen.getByText('Signing in…')).toBeTruthy();
    });
});

// ── Signup form ──────────────────────────────────────────────────────────

describe('AuthModal signup form', () => {
    it('calls onRegister with email and password on submit', async () => {
        defaultProps.onRegister.mockResolvedValue(undefined);
        renderModal({ mode: 'signup' });

        fireEvent.change(screen.getByPlaceholderText('you@company.com'), {
            target: { value: 'new@example.com' },
        });
        fireEvent.change(screen.getByPlaceholderText('12+ chars, upper, lower, digit, symbol'), {
            target: { value: 'StrongPass1!' },
        });

        await act(async () => {
            // Two "Sign up" elements exist (tab + submit button) — target the submit
            const submitBtn = screen.getAllByText('Sign up').find(
                el => el.getAttribute('type') === 'submit'
            );
            fireEvent.click(submitBtn);
        });

        expect(defaultProps.onRegister).toHaveBeenCalledWith({
            email: 'new@example.com',
            password: 'StrongPass1!',
        });
    });

    it('shows password strength meter when typing in signup mode', () => {
        renderModal({ mode: 'signup' });
        fireEvent.change(screen.getByPlaceholderText('12+ chars, upper, lower, digit, symbol'), {
            target: { value: 'abc' },
        });
        // Strength hint labels appear
        expect(screen.getByText(/12\+ characters/)).toBeTruthy();
    });

    it('shows Creating account… when submitting in signup mode', () => {
        renderModal({ mode: 'signup', submitting: true });
        expect(screen.getByText('Creating account…')).toBeTruthy();
    });
});

// ── Forgot password view ─────────────────────────────────────────────────

describe('AuthModal forgot password view', () => {
    it('navigates to forgot view when Forgot password? is clicked', () => {
        renderModal({ mode: 'login' });
        fireEvent.click(screen.getByText('Forgot password?'));
        expect(screen.getByText('Reset your password')).toBeTruthy();
    });

    it('calls forgotPassword service on submit', async () => {
        mockForgotPassword.mockResolvedValue(undefined);
        renderModal({ mode: 'login' });

        fireEvent.click(screen.getByText('Forgot password?'));
        fireEvent.change(screen.getByPlaceholderText('you@company.com'), {
            target: { value: 'user@example.com' },
        });

        await act(async () => {
            fireEvent.click(screen.getByText('Send reset link'));
        });

        expect(mockForgotPassword).toHaveBeenCalledWith('user@example.com');
    });

    it('shows error if forgotPassword service throws', async () => {
        mockForgotPassword.mockRejectedValue(new Error('Network error'));
        renderModal({ mode: 'login' });

        fireEvent.click(screen.getByText('Forgot password?'));
        fireEvent.change(screen.getByPlaceholderText('you@company.com'), {
            target: { value: 'user@example.com' },
        });

        await act(async () => {
            fireEvent.click(screen.getByText('Send reset link'));
        });

        await waitFor(() => {
            expect(screen.getByText('Something went wrong. Please try again.')).toBeTruthy();
        });
    });

    it('navigates back to login when Back to log in is clicked', () => {
        renderModal({ mode: 'login' });
        fireEvent.click(screen.getByText('Forgot password?'));
        fireEvent.click(screen.getByText('Back to log in'));
        expect(screen.getByText('Welcome back')).toBeTruthy();
    });
});

// ── Magic link toggle ────────────────────────────────────────────────────

describe('AuthModal magic link toggle', () => {
    it('hides password field when magic link mode is toggled on', () => {
        renderModal({ mode: 'login' });
        fireEvent.click(screen.getByText('Email me a login link instead'));
        expect(screen.queryByPlaceholderText('Your password')).toBeNull();
    });

    it('calls requestMagicLink service when magic link form is submitted', async () => {
        mockRequestMagicLink.mockResolvedValue(undefined);
        renderModal({ mode: 'login' });

        fireEvent.click(screen.getByText('Email me a login link instead'));
        fireEvent.change(screen.getByPlaceholderText('you@company.com'), {
            target: { value: 'user@example.com' },
        });

        await act(async () => {
            fireEvent.click(screen.getByText('Send login link'));
        });

        expect(mockRequestMagicLink).toHaveBeenCalledWith('user@example.com');
    });

    it('shows error if requestMagicLink throws', async () => {
        mockRequestMagicLink.mockRejectedValue(new Error('Failed'));
        renderModal({ mode: 'login' });

        fireEvent.click(screen.getByText('Email me a login link instead'));
        fireEvent.change(screen.getByPlaceholderText('you@company.com'), {
            target: { value: 'user@example.com' },
        });

        await act(async () => {
            fireEvent.click(screen.getByText('Send login link'));
        });

        await waitFor(() => {
            expect(screen.getByText('Failed to send magic link. Please try again.')).toBeTruthy();
        });
    });
});

// ── Unverified user banner ───────────────────────────────────────────────

describe('AuthModal unverified user banner', () => {
    const unverifiedUser = { email: 'user@example.com', is_verified: false };

    it('shows verify email banner when user is logged in but not verified', () => {
        renderModal({ open: true, user: unverifiedUser });
        expect(screen.getByText('Verify your email')).toBeTruthy();
        expect(screen.getByText(/user@example\.com/)).toBeTruthy();
    });

    it('shows resend button in banner', () => {
        renderModal({ open: true, user: unverifiedUser });
        expect(screen.getByText('Resend verification email')).toBeTruthy();
    });

    it('calls resendVerification on resend button click', async () => {
        mockResendVerification.mockResolvedValue(undefined);
        renderModal({ open: true, user: unverifiedUser });

        await act(async () => {
            fireEvent.click(screen.getByText('Resend verification email'));
        });

        expect(mockResendVerification).toHaveBeenCalledWith('user@example.com');
    });

    it('shows error if resend fails', async () => {
        mockResendVerification.mockRejectedValue(new Error('Failed'));
        renderModal({ open: true, user: unverifiedUser });

        await act(async () => {
            fireEvent.click(screen.getByText('Resend verification email'));
        });

        await waitFor(() => {
            expect(screen.getByText('Failed to resend. Please try again.')).toBeTruthy();
        });
    });
});
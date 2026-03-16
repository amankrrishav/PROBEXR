/**
 * AccountSettings component tests.
 *
 * Tests: success path saves locally + shows "Changes saved",
 *        failure path shows error + does NOT save locally + does NOT close,
 *        submitting state is always cleared (finally block),
 *        validation blocks submission before calling backend.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import AccountSettings from '../AccountSettings.jsx';

// ── Mocks ─────────────────────────────────────────────────────────────────

const mockUpdateProfile = vi.fn();
const mockOnClose = vi.fn();

const mockUser = {
    id: 1,
    email: 'test@example.com',
    full_name: 'Jane Doe',
    avatar_url: '',
};

// Mock AppContext
vi.mock('../../../contexts/AppContext', () => ({
    useAppContext: () => ({
        auth: {
            user: mockUser,
            updateProfile: mockUpdateProfile,
        },
    }),
}));

// Mock useFeatureFlags
vi.mock('../../../hooks/useFeatureFlags', () => ({
    useFeatureFlags: () => ({}),
}));

// ── Helpers ───────────────────────────────────────────────────────────────

function renderOpen() {
    return render(<AccountSettings open={true} onClose={mockOnClose} />);
}

beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
});

// ── Tests ─────────────────────────────────────────────────────────────────

describe('AccountSettings', () => {

    it('renders when open=true', () => {
        renderOpen();
        expect(screen.getByText('Account Settings')).toBeTruthy();
        expect(screen.getByLabelText('Full Name')).toBeTruthy();
    });

    it('does not render when open=false', () => {
        render(<AccountSettings open={false} onClose={mockOnClose} />);
        expect(screen.queryByText('Account Settings')).toBeNull();
    });

    it('pre-fills full name from user prop', () => {
        renderOpen();
        const input = screen.getByLabelText('Full Name');
        expect(input.value).toBe('Jane Doe');
    });

    // ── Success path ──────────────────────────────────────────────────────

    it('saves to localStorage and shows success on backend success', async () => {
        mockUpdateProfile.mockResolvedValue({ ...mockUser, full_name: 'Jane Doe' });
        renderOpen();

        const nameInput = screen.getByLabelText('Full Name');
        fireEvent.change(nameInput, { target: { value: 'Jane Doe' } });

        await act(async () => {
            fireEvent.click(screen.getByText('Save Changes'));
        });

        await waitFor(() => {
            expect(screen.getByText('Changes saved')).toBeTruthy();
        });

        // localStorage was written
        const stored = JSON.parse(localStorage.getItem('probexr_user'));
        expect(stored).not.toBeNull();
        expect(stored.full_name).toBe('Jane Doe');
    });

    it('calls updateProfile with correct payload on success', async () => {
        mockUpdateProfile.mockResolvedValue({ ...mockUser });
        renderOpen();

        const nameInput = screen.getByLabelText('Full Name');
        fireEvent.change(nameInput, { target: { value: 'Updated Name' } });

        await act(async () => {
            fireEvent.click(screen.getByText('Save Changes'));
        });

        await waitFor(() => {
            expect(mockUpdateProfile).toHaveBeenCalledWith({
                full_name: 'Updated Name',
                avatar_url: null,
            });
        });
    });

    // ── Failure path ──────────────────────────────────────────────────────

    it('shows error message when backend call fails', async () => {
        mockUpdateProfile.mockRejectedValue(new Error('Network error'));
        renderOpen();

        await act(async () => {
            fireEvent.click(screen.getByText('Save Changes'));
        });

        await waitFor(() => {
            expect(screen.getByText('Network error')).toBeTruthy();
        });
    });

    it('does NOT save to localStorage when backend fails', async () => {
        mockUpdateProfile.mockRejectedValue(new Error('Server error'));
        renderOpen();

        await act(async () => {
            fireEvent.click(screen.getByText('Save Changes'));
        });

        await waitFor(() => {
            expect(screen.queryByText('Changes saved')).toBeNull();
        });

        expect(localStorage.getItem('probexr_user')).toBeNull();
    });

    it('does NOT close modal when backend fails', async () => {
        mockUpdateProfile.mockRejectedValue(new Error('Server error'));
        renderOpen();

        await act(async () => {
            fireEvent.click(screen.getByText('Save Changes'));
        });

        await waitFor(() => {
            expect(screen.queryByText('Changes saved')).toBeNull();
        });

        // onClose was not called
        expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('re-enables submit button after backend failure', async () => {
        mockUpdateProfile.mockRejectedValue(new Error('Server error'));
        renderOpen();

        const btn = screen.getByText('Save Changes');

        await act(async () => {
            fireEvent.click(btn);
        });

        await waitFor(() => {
            // Button text reverts from "Saving..." back to "Save Changes"
            expect(screen.getByText('Save Changes')).toBeTruthy();
        });
    });

    // ── Validation ────────────────────────────────────────────────────────

    it('shows name error and does not call backend when name is empty', async () => {
        renderOpen();

        const nameInput = screen.getByLabelText('Full Name');
        fireEvent.change(nameInput, { target: { value: '' } });

        await act(async () => {
            fireEvent.click(screen.getByText('Save Changes'));
        });

        expect(screen.getByText('Full name is required.')).toBeTruthy();
        expect(mockUpdateProfile).not.toHaveBeenCalled();
    });

    // ── Generic error fallback ────────────────────────────────────────────

    it('shows fallback error message when backend error has no message', async () => {
        mockUpdateProfile.mockRejectedValue({});
        renderOpen();

        await act(async () => {
            fireEvent.click(screen.getByText('Save Changes'));
        });

        await waitFor(() => {
            expect(
                screen.getByText('Failed to save. Please check your connection and try again.')
            ).toBeTruthy();
        });
    });

});
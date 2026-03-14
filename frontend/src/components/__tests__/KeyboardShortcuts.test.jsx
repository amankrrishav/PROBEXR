/**
 * KeyboardShortcuts component tests.
 *
 * Tests: not rendered when closed, renders when open,
 * displays all shortcuts, calls onClose.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import KeyboardShortcuts from '../KeyboardShortcuts.jsx';

describe('KeyboardShortcuts', () => {
  it('renders nothing when open=false', () => {
    const { container } = render(
      <KeyboardShortcuts open={false} onClose={() => {}} />
    );
    expect(container.innerHTML).toBe('');
  });

  it('renders the modal when open=true', () => {
    render(<KeyboardShortcuts open={true} onClose={() => {}} />);
    expect(screen.getByText('Keyboard Shortcuts')).toBeTruthy();
  });

  it('displays all 6 shortcut actions', () => {
    render(<KeyboardShortcuts open={true} onClose={() => {}} />);
    const expectedActions = [
      'Summarize',
      'Focus mode',
      'New summary',
      'Keyboard shortcuts',
      'Clear input',
      'Exit modal / Focus mode',
    ];
    for (const action of expectedActions) {
      expect(screen.getByText(action)).toBeTruthy();
    }
  });

  it('calls onClose when the overlay is clicked', () => {
    const onClose = vi.fn();
    render(<KeyboardShortcuts open={true} onClose={onClose} />);
    const overlay = document.querySelector('.shortcuts-overlay');
    fireEvent.click(overlay);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('calls onClose when the × button is clicked', () => {
    const onClose = vi.fn();
    render(<KeyboardShortcuts open={true} onClose={onClose} />);
    const closeBtn = screen.getByText('×');
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('does NOT close when clicking inside the modal', () => {
    const onClose = vi.fn();
    render(<KeyboardShortcuts open={true} onClose={onClose} />);
    const modal = document.querySelector('.shortcuts-modal');
    fireEvent.click(modal);
    expect(onClose).not.toHaveBeenCalled();
  });
});

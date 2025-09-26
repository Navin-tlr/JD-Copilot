import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import Index from './Index';

describe('Index page', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the input with the placeholder', () => {
    const { getByPlaceholderText } = render(<Index />);
    expect(getByPlaceholderText(/Alright genius, spit out/i)).toBeTruthy();
  });

  it('sends message when clicking send icon', async () => {
    const mockFetch = vi.spyOn(global, 'fetch' as any).mockResolvedValue({
      json: async () => ({ message: 'ok' }),
    } as Response);

    const { getByPlaceholderText, getByRole } = render(<Index />);
    const input = getByPlaceholderText(/Alright genius, spit out/i) as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Hello' } });
    const sendBtn = getByRole('button', { name: /send message/i });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toMatch(/question=Hello/);
    });
  });
});

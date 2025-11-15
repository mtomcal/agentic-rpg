import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Home from '../page';
import { apiClient } from '@/lib/api/client';

// Mock the API client
vi.mock('@/lib/api/client', () => ({
  apiClient: {
    healthCheck: vi.fn(),
  },
}));

describe('Home', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should render the page title', () => {
    vi.mocked(apiClient.healthCheck).mockResolvedValue({
      status: 'healthy',
      timestamp: '2025-01-01T00:00:00Z',
    });

    render(<Home />);

    expect(screen.getByRole('heading', { name: 'Agentic RPG' })).toBeInTheDocument();
  });

  it('should show initial checking status', () => {
    vi.mocked(apiClient.healthCheck).mockImplementation(
      () => new Promise(() => {}) // Never resolves to keep loading state
    );

    render(<Home />);

    expect(screen.getByText(/Backend Status: checking\.\.\./)).toBeInTheDocument();
  });

  it('should display healthy status when health check succeeds', async () => {
    vi.mocked(apiClient.healthCheck).mockResolvedValue({
      status: 'healthy',
      timestamp: '2025-01-01T00:00:00Z',
    });

    render(<Home />);

    await waitFor(() => {
      expect(screen.getByText(/Backend Status: healthy/)).toBeInTheDocument();
    });
  });

  it('should display error status when health check fails', async () => {
    vi.mocked(apiClient.healthCheck).mockRejectedValue(new Error('Network error'));

    render(<Home />);

    await waitFor(() => {
      expect(screen.getByText(/Backend Status: error/)).toBeInTheDocument();
    });
  });

  it('should call health check on mount', () => {
    vi.mocked(apiClient.healthCheck).mockResolvedValue({
      status: 'healthy',
      timestamp: '2025-01-01T00:00:00Z',
    });

    render(<Home />);

    expect(apiClient.healthCheck).toHaveBeenCalledTimes(1);
  });

  it('should render foundation setup message', () => {
    vi.mocked(apiClient.healthCheck).mockResolvedValue({
      status: 'healthy',
      timestamp: '2025-01-01T00:00:00Z',
    });

    render(<Home />);

    expect(screen.getByText('Foundation setup complete')).toBeInTheDocument();
  });

  it('should have proper semantic HTML structure', () => {
    vi.mocked(apiClient.healthCheck).mockResolvedValue({
      status: 'healthy',
      timestamp: '2025-01-01T00:00:00Z',
    });

    const { container } = render(<Home />);

    const main = container.querySelector('main');
    expect(main).toBeInTheDocument();
    expect(main?.tagName).toBe('MAIN');
  });

  it('should handle empty status response gracefully', async () => {
    vi.mocked(apiClient.healthCheck).mockResolvedValue({
      status: '',
      timestamp: '2025-01-01T00:00:00Z',
    });

    render(<Home />);

    await waitFor(() => {
      expect(screen.getByText(/Backend Status:/)).toBeInTheDocument();
    });
  });
});

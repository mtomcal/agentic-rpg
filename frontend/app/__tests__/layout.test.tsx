import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock Next.js font
vi.mock('next/font/google', () => ({
  Inter: () => ({
    className: 'inter-font',
  }),
}));

import RootLayout from '../layout';

describe('RootLayout', () => {
  it('should render children', () => {
    render(
      <RootLayout>
        <div data-testid="test-child">Test Content</div>
      </RootLayout>
    );

    expect(screen.getByTestId('test-child')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should render multiple children correctly', () => {
    render(
      <RootLayout>
        <div data-testid="child-1">Child 1</div>
        <div data-testid="child-2">Child 2</div>
      </RootLayout>
    );

    expect(screen.getByTestId('child-1')).toBeInTheDocument();
    expect(screen.getByTestId('child-2')).toBeInTheDocument();
  });

  it('should render complex nested children', () => {
    render(
      <RootLayout>
        <main>
          <h1>Main Heading</h1>
          <p>Main content paragraph</p>
        </main>
      </RootLayout>
    );

    expect(screen.getByRole('heading', { name: 'Main Heading' })).toBeInTheDocument();
    expect(screen.getByText('Main content paragraph')).toBeInTheDocument();
  });

  it('should handle empty children', () => {
    render(
      <RootLayout>
        <div data-testid="empty-container"></div>
      </RootLayout>
    );

    expect(screen.getByTestId('empty-container')).toBeInTheDocument();
  });
});

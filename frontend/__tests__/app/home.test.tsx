import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import HomePage from "@/app/page";
import * as api from "@/lib/api";

// Mock next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock API
jest.mock("@/lib/api");
const mockListSessions = api.listSessions as jest.MockedFunction<typeof api.listSessions>;
const mockDeleteSession = api.deleteSession as jest.MockedFunction<typeof api.deleteSession>;

beforeEach(() => {
  mockPush.mockReset();
  mockListSessions.mockReset();
  mockDeleteSession.mockReset();
});

describe("HomePage", () => {
  it("shows loading state initially", () => {
    mockListSessions.mockReturnValue(new Promise(() => {})); // never resolves
    render(<HomePage />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows session list after loading", async () => {
    mockListSessions.mockResolvedValue({
      sessions: [
        {
          session_id: "sess-001",
          status: "active",
          character_name: "Aldric",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-15T12:00:00Z",
        },
      ],
    });

    render(<HomePage />);
    await waitFor(() => {
      expect(screen.getByText("Aldric")).toBeInTheDocument();
    });
  });

  it("shows empty state when no sessions", async () => {
    mockListSessions.mockResolvedValue({ sessions: [] });

    render(<HomePage />);
    await waitFor(() => {
      expect(screen.getByText("No sessions yet. Start a new game!")).toBeInTheDocument();
    });
  });

  it("shows error state on API failure", async () => {
    mockListSessions.mockRejectedValue(new Error("Network error"));

    render(<HomePage />);
    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it("has New Game button that navigates to /new", async () => {
    mockListSessions.mockResolvedValue({ sessions: [] });

    render(<HomePage />);
    await waitFor(() => {
      expect(screen.getByText("New Game")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("New Game"));
    expect(mockPush).toHaveBeenCalledWith("/new");
  });

  it("navigates to play page when session card clicked", async () => {
    mockListSessions.mockResolvedValue({
      sessions: [
        {
          session_id: "sess-001",
          status: "active",
          character_name: "Aldric",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-15T12:00:00Z",
        },
      ],
    });

    render(<HomePage />);
    await waitFor(() => {
      expect(screen.getByText("Aldric")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Aldric"));
    expect(mockPush).toHaveBeenCalledWith("/play/sess-001");
  });

  it("deletes session with confirmation", async () => {
    mockListSessions.mockResolvedValue({
      sessions: [
        {
          session_id: "sess-001",
          status: "active",
          character_name: "Aldric",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-15T12:00:00Z",
        },
      ],
    });
    mockDeleteSession.mockResolvedValue({ success: true });
    window.confirm = jest.fn(() => true);

    render(<HomePage />);
    await waitFor(() => {
      expect(screen.getByText("Aldric")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText("Delete session"));
    expect(window.confirm).toHaveBeenCalled();
    expect(mockDeleteSession).toHaveBeenCalledWith("sess-001");
  });
});

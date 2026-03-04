import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import NewGamePage from "@/app/new/page";
import * as api from "@/lib/api";

const mockPush = jest.fn();
const mockBack = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
}));

jest.mock("@/lib/api");
const mockCreateSession = api.createSession as jest.MockedFunction<typeof api.createSession>;

beforeEach(() => {
  mockPush.mockReset();
  mockBack.mockReset();
  mockCreateSession.mockReset();
});

describe("NewGamePage", () => {
  it("renders form fields", () => {
    render(<NewGamePage />);
    expect(screen.getByLabelText("Genre / Setting")).toBeInTheDocument();
    expect(screen.getByLabelText("Character Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Profession")).toBeInTheDocument();
    expect(screen.getByLabelText("Background")).toBeInTheDocument();
  });

  it("has a Start Adventure button", () => {
    render(<NewGamePage />);
    expect(screen.getByText("Start Adventure")).toBeInTheDocument();
  });

  it("has a back button", () => {
    render(<NewGamePage />);
    fireEvent.click(screen.getByText("Back"));
    expect(mockBack).toHaveBeenCalled();
  });

  it("requires all fields", () => {
    render(<NewGamePage />);
    fireEvent.click(screen.getByText("Start Adventure"));
    // Should not call API without filling fields
    expect(mockCreateSession).not.toHaveBeenCalled();
  });

  it("does not submit when only genre is filled", () => {
    render(<NewGamePage />);
    fireEvent.change(screen.getByLabelText("Genre / Setting"), {
      target: { value: "Fantasy" },
    });
    fireEvent.click(screen.getByText("Start Adventure"));
    expect(mockCreateSession).not.toHaveBeenCalled();
  });

  it("does not submit when genre is whitespace only", () => {
    render(<NewGamePage />);
    fireEvent.change(screen.getByLabelText("Genre / Setting"), {
      target: { value: "   " },
    });
    fireEvent.change(screen.getByLabelText("Character Name"), {
      target: { value: "Aldric" },
    });
    fireEvent.change(screen.getByLabelText("Profession"), {
      target: { value: "Knight" },
    });
    fireEvent.change(screen.getByLabelText("Background"), {
      target: { value: "A soldier" },
    });
    fireEvent.click(screen.getByText("Start Adventure"));
    expect(mockCreateSession).not.toHaveBeenCalled();
  });

  it("submits form and redirects on success", async () => {
    mockCreateSession.mockResolvedValue({
      session_id: "sess-001",
      game_state: {} as any,
    });

    render(<NewGamePage />);

    fireEvent.change(screen.getByLabelText("Genre / Setting"), {
      target: { value: "Medieval Fantasy" },
    });
    fireEvent.change(screen.getByLabelText("Character Name"), {
      target: { value: "Aldric" },
    });
    fireEvent.change(screen.getByLabelText("Profession"), {
      target: { value: "Knight" },
    });
    fireEvent.change(screen.getByLabelText("Background"), {
      target: { value: "A former soldier" },
    });

    fireEvent.click(screen.getByText("Start Adventure"));

    await waitFor(() => {
      expect(mockCreateSession).toHaveBeenCalledWith("Medieval Fantasy", {
        name: "Aldric",
        profession: "Knight",
        background: "A former soldier",
      });
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/play/sess-001");
    });
  });

  it("shows fallback error message when error has no message", async () => {
    mockCreateSession.mockRejectedValue({});

    render(<NewGamePage />);

    fireEvent.change(screen.getByLabelText("Genre / Setting"), {
      target: { value: "Fantasy" },
    });
    fireEvent.change(screen.getByLabelText("Character Name"), {
      target: { value: "A" },
    });
    fireEvent.change(screen.getByLabelText("Profession"), {
      target: { value: "B" },
    });
    fireEvent.change(screen.getByLabelText("Background"), {
      target: { value: "C" },
    });

    fireEvent.click(screen.getByText("Start Adventure"));

    await waitFor(() => {
      expect(screen.getByText("Failed to create session")).toBeInTheDocument();
    });
  });

  it("shows error on failure", async () => {
    mockCreateSession.mockRejectedValue(new Error("Server error"));

    render(<NewGamePage />);

    fireEvent.change(screen.getByLabelText("Genre / Setting"), {
      target: { value: "Fantasy" },
    });
    fireEvent.change(screen.getByLabelText("Character Name"), {
      target: { value: "A" },
    });
    fireEvent.change(screen.getByLabelText("Profession"), {
      target: { value: "B" },
    });
    fireEvent.change(screen.getByLabelText("Background"), {
      target: { value: "C" },
    });

    fireEvent.click(screen.getByText("Start Adventure"));

    await waitFor(() => {
      expect(screen.getByText(/Server error/)).toBeInTheDocument();
    });
  });

  it("shows loading state while creating", async () => {
    mockCreateSession.mockReturnValue(new Promise(() => {})); // never resolves

    render(<NewGamePage />);

    fireEvent.change(screen.getByLabelText("Genre / Setting"), {
      target: { value: "Fantasy" },
    });
    fireEvent.change(screen.getByLabelText("Character Name"), {
      target: { value: "A" },
    });
    fireEvent.change(screen.getByLabelText("Profession"), {
      target: { value: "B" },
    });
    fireEvent.change(screen.getByLabelText("Background"), {
      target: { value: "C" },
    });

    fireEvent.click(screen.getByText("Start Adventure"));

    await waitFor(() => {
      expect(screen.getByText("Creating...")).toBeInTheDocument();
    });
  });
});

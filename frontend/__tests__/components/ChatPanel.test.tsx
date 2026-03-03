import { render, screen, fireEvent } from "@testing-library/react";
import ChatPanel from "@/components/ChatPanel";
import type { ChatMessage } from "@/lib/store";

describe("ChatPanel", () => {
  const mockOnSend = jest.fn();

  beforeEach(() => {
    mockOnSend.mockReset();
  });

  it("renders empty state when no messages", () => {
    render(
      <ChatPanel
        messages={[]}
        isAgentThinking={false}
        isDisabled={false}
        onSendMessage={mockOnSend}
      />
    );
    expect(
      screen.getByText("Start your adventure by typing an action...")
    ).toBeInTheDocument();
  });

  it("renders player messages right-aligned", () => {
    const messages: ChatMessage[] = [
      {
        id: "1",
        role: "player",
        content: "I go north",
        timestamp: "2024-01-01T00:00:00Z",
        isStreaming: false,
      },
    ];
    render(
      <ChatPanel
        messages={messages}
        isAgentThinking={false}
        isDisabled={false}
        onSendMessage={mockOnSend}
      />
    );
    expect(screen.getByText("I go north")).toBeInTheDocument();
  });

  it("renders agent messages", () => {
    const messages: ChatMessage[] = [
      {
        id: "1",
        role: "agent",
        content: "You walk north into the forest.",
        timestamp: "2024-01-01T00:00:00Z",
        isStreaming: false,
      },
    ];
    render(
      <ChatPanel
        messages={messages}
        isAgentThinking={false}
        isDisabled={false}
        onSendMessage={mockOnSend}
      />
    );
    expect(
      screen.getByText("You walk north into the forest.")
    ).toBeInTheDocument();
  });

  it("renders system messages", () => {
    const messages: ChatMessage[] = [
      {
        id: "1",
        role: "system",
        content: "Game started",
        timestamp: "2024-01-01T00:00:00Z",
        isStreaming: false,
      },
    ];
    render(
      <ChatPanel
        messages={messages}
        isAgentThinking={false}
        isDisabled={false}
        onSendMessage={mockOnSend}
      />
    );
    expect(screen.getByText("Game started")).toBeInTheDocument();
  });

  it("shows streaming indicator for streaming messages", () => {
    const messages: ChatMessage[] = [
      {
        id: "1",
        role: "agent",
        content: "You see a",
        timestamp: "2024-01-01T00:00:00Z",
        isStreaming: true,
      },
    ];
    render(
      <ChatPanel
        messages={messages}
        isAgentThinking={false}
        isDisabled={false}
        onSendMessage={mockOnSend}
      />
    );
    expect(screen.getByText("You see a")).toBeInTheDocument();
    expect(screen.getByTestId("streaming-indicator")).toBeInTheDocument();
  });

  it("shows thinking indicator", () => {
    render(
      <ChatPanel
        messages={[]}
        isAgentThinking={true}
        isDisabled={false}
        onSendMessage={mockOnSend}
      />
    );
    expect(screen.getByText("Agent is thinking...")).toBeInTheDocument();
  });

  it("calls onSendMessage when send button clicked", () => {
    render(
      <ChatPanel
        messages={[]}
        isAgentThinking={false}
        isDisabled={false}
        onSendMessage={mockOnSend}
      />
    );
    const input = screen.getByPlaceholderText("Type your action...");
    fireEvent.change(input, { target: { value: "I attack" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));
    expect(mockOnSend).toHaveBeenCalledWith("I attack");
  });

  it("calls onSendMessage on Enter key", () => {
    render(
      <ChatPanel
        messages={[]}
        isAgentThinking={false}
        isDisabled={false}
        onSendMessage={mockOnSend}
      />
    );
    const input = screen.getByPlaceholderText("Type your action...");
    fireEvent.change(input, { target: { value: "I run" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(mockOnSend).toHaveBeenCalledWith("I run");
  });

  it("does not send on Shift+Enter", () => {
    render(
      <ChatPanel
        messages={[]}
        isAgentThinking={false}
        isDisabled={false}
        onSendMessage={mockOnSend}
      />
    );
    const input = screen.getByPlaceholderText("Type your action...");
    fireEvent.change(input, { target: { value: "test" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it("disables input when isDisabled is true", () => {
    render(
      <ChatPanel
        messages={[]}
        isAgentThinking={false}
        isDisabled={true}
        onSendMessage={mockOnSend}
      />
    );
    const input = screen.getByPlaceholderText("Type your action...");
    expect(input).toBeDisabled();
  });

  it("clears input after sending", () => {
    render(
      <ChatPanel
        messages={[]}
        isAgentThinking={false}
        isDisabled={false}
        onSendMessage={mockOnSend}
      />
    );
    const input = screen.getByPlaceholderText("Type your action...");
    fireEvent.change(input, { target: { value: "I go north" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));
    expect((input as HTMLInputElement).value).toBe("");
  });

  it("does not send empty messages", () => {
    render(
      <ChatPanel
        messages={[]}
        isAgentThinking={false}
        isDisabled={false}
        onSendMessage={mockOnSend}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /send/i }));
    expect(mockOnSend).not.toHaveBeenCalled();
  });
});

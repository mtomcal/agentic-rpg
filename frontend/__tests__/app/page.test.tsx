import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

describe("Home page", () => {
  it("renders the heading", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Agentic RPG"
    );
  });

  it("renders the welcome message", () => {
    render(<Home />);
    expect(screen.getByText("Welcome to the Agentic RPG.")).toBeInTheDocument();
  });
});

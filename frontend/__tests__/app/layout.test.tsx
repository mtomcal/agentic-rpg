import { render, screen } from "@testing-library/react";

// We need to test the layout component's rendered output
// Since RootLayout wraps children in html/body tags, we test the metadata
// and the component's rendering behavior
describe("RootLayout", () => {
  // Import dynamically to avoid issues with metadata export
  let RootLayout: any;

  beforeAll(async () => {
    const mod = await import("@/app/layout");
    RootLayout = mod.default;
  });

  it("renders children", () => {
    // RootLayout renders <html><body>{children}</body></html>
    // We can't render full html/body in jsdom, so we test the function returns
    const result = RootLayout({ children: <div data-testid="child">Hello</div> });
    expect(result).toBeDefined();
    expect(result.props.lang).toBe("en");
  });

  it("applies dark theme classes to body", () => {
    const result = RootLayout({ children: <div>Test</div> });
    const bodyProps = result.props.children.props;
    expect(bodyProps.className).toContain("bg-gray-900");
    expect(bodyProps.className).toContain("text-gray-100");
  });

  it("uses monospace font", () => {
    const result = RootLayout({ children: <div>Test</div> });
    const bodyProps = result.props.children.props;
    expect(bodyProps.className).toContain("font-mono");
  });

  it("exports metadata with correct title", async () => {
    const mod = await import("@/app/layout");
    expect(mod.metadata.title).toBe("Agentic RPG");
    expect(mod.metadata.description).toBe(
      "A browser-based RPG powered by AI agents"
    );
  });
});

import { render, screen } from "@testing-library/react";
import { ColorModeContext, useColorMode } from "../ColorModeContext";

function Probe() {
  const mode = useColorMode();
  return <span data-testid="mode">{mode}</span>;
}

test("useColorMode reads context value", () => {
  render(
    <ColorModeContext.Provider value="light">
      <Probe />
    </ColorModeContext.Provider>,
  );
  expect(screen.getByTestId("mode").textContent).toBe("light");
});

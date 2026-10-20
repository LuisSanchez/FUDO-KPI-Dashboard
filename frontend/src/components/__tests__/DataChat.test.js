import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DataChat from "../DataChat";
import { askDataChat } from "../../api/client";

jest.mock("../../api/client", () => ({
  askDataChat: jest.fn(),
}));

beforeEach(() => {
  askDataChat.mockReset();
});

test("a suggested question is sent and the answer is shown", async () => {
  askDataChat.mockResolvedValue({
    reply: "Febrero fue el peor mes.",
    consultas: [{ filas: 9 }],
  });
  const user = userEvent.setup();
  render(<DataChat open onClose={() => {}} />);

  await user.click(
    screen.getByRole("button", { name: "¿Cuál mes dejó peor EBITDA y qué lo explica?" }),
  );

  await waitFor(() => expect(askDataChat).toHaveBeenCalled());
  const sent = askDataChat.mock.calls[0][0];
  expect(sent[sent.length - 1]).toEqual({
    role: "user",
    content: "¿Cuál mes dejó peor EBITDA y qué lo explica?",
  });
  expect(await screen.findByText("Febrero fue el peor mes.")).toBeTruthy();
  expect(screen.getByText("Revisé la base · 1 consulta")).toBeTruthy();
});

test("the server error stays on screen", async () => {
  askDataChat.mockRejectedValue({
    response: { data: { error: "Falta OPENROUTER_API_KEY en el entorno." } },
  });
  const user = userEvent.setup();
  render(<DataChat open onClose={() => {}} />);

  await user.type(screen.getByRole("textbox", { name: "Pregunta sobre los números" }), "hola");
  await user.click(screen.getByRole("button", { name: "Enviar" }));

  expect(await screen.findByText("Falta OPENROUTER_API_KEY en el entorno.")).toBeTruthy();
});

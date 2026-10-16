import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ErrorMessage } from "./ErrorMessage";

describe("ErrorMessage", () => {
  it("renders the message", () => {
    render(<ErrorMessage message="something went wrong" />);
    expect(screen.getByText("something went wrong")).toBeInTheDocument();
  });
});

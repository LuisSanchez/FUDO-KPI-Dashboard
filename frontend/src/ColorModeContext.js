import { createContext, useContext } from "react";

export const ColorModeContext = createContext("dark");
export const useColorMode = () => useContext(ColorModeContext);

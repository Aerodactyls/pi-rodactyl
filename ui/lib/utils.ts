import {
  EDGE_PAIRS,
  NODE_CONFIGS,
  NODE_STYLES,
  NodeConfig,
} from "@/lib/constants";
import { FlowState } from "@/lib/types";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const getNodeConfig = (id: FlowState): NodeConfig | undefined =>
  NODE_CONFIGS.find((config) => config.id === id);

export const getNextStates = (state: FlowState): FlowState[] =>
  EDGE_PAIRS.filter(([source]) => source === state).map(([, target]) => target);

export const createNodeStyle = (
  config: NodeConfig,
  isCurrentState: boolean,
  isTransitioning: boolean = false,
) => ({
  ...NODE_STYLES[config.group],
  borderRadius: 8,
  padding: 8,
  color: "black",
  cursor: isCurrentState ? "default" : "pointer",
  boxShadow: isCurrentState
    ? isTransitioning
      ? "0 0 0 4px #f57c00, 0 2px 8px rgba(0,0,0,0.08)"
      : "0 0 0 4px #1976d2, 0 2px 8px rgba(0,0,0,0.08)"
    : undefined,
  border: isCurrentState
    ? isTransitioning
      ? "3px solid #f57c00"
      : "3px solid #1976d2"
    : NODE_STYLES[config.group].border,
  opacity: isCurrentState ? 1 : 0.7,
  transition: "box-shadow 0.2s, border 0.2s, opacity 0.2s, transform 0.1s",
  animation:
    isCurrentState && isTransitioning ? "pulse 1s infinite" : undefined,
  ":hover": !isCurrentState
    ? {
        opacity: 0.9,
        transform: "scale(1.02)",
      }
    : undefined,
});

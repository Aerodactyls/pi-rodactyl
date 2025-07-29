import { FlowState } from "@/lib/types";

export interface NodePosition {
  x: number;
  y: number;
}

export interface NodePositions {
  [key: string]: NodePosition;
}

const POSITIONS_FILE_PATH = "/api/positions";

function round(num: number): number {
  return Math.round(num / 5) * 5;
}

export class PositionManager {
  private positions: NodePositions = {};
  private isDirty = false;
  private loadPromise: Promise<void> | null = null;

  constructor() {
    this.loadPromise = this.loadPositions();
  }

  private async loadPositions(): Promise<void> {
    try {
      console.log("Loading positions...");
      const response = await fetch(POSITIONS_FILE_PATH);
      if (response.ok) {
        this.positions = await response.json();
        console.log("Loaded positions:", this.positions);
      } else if (response.status === 404) {
        // File doesn't exist
        console.log("No positions file found, using empty positions");
        this.positions = {};
      } else {
        console.error("Failed to load positions:", response.statusText);
        this.positions = {};
      }
    } catch (error) {
      console.error("Failed to load positions:", error);
      this.positions = {};
    }
  }

  private async savePositions(): Promise<void> {
    try {
      console.log("Saving positions:", this.positions);
      const response = await fetch(POSITIONS_FILE_PATH, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(this.positions),
      });

      if (response.ok) {
        console.log("Positions saved successfully");
        this.isDirty = false;
      } else {
        console.error("Failed to save positions:", response.statusText);
      }
    } catch (error) {
      console.error("Failed to save positions:", error);
    }
  }

  getPosition(nodeId: FlowState): NodePosition | null {
    return this.positions[nodeId] || null;
  }

  async ensureLoaded(): Promise<void> {
    if (this.loadPromise) {
      await this.loadPromise;
      this.loadPromise = null;
    }
  }

  setPosition(nodeId: FlowState, position: NodePosition): void {
    const roundedPosition = {
      x: round(position.x),
      y: round(position.y),
    };
    this.positions[nodeId] = roundedPosition;
    this.isDirty = true;
  }

  updatePositions(newPositions: Partial<NodePositions>): void {
    const roundedPositions: Partial<NodePositions> = {};
    for (const [nodeId, position] of Object.entries(newPositions)) {
      if (position) {
        roundedPositions[nodeId] = {
          x: round(position.x),
          y: round(position.y),
        };
      }
    }
    Object.assign(this.positions, roundedPositions);
    this.isDirty = true;
  }

  getAllPositions(): NodePositions {
    return { ...this.positions };
  }

  async save(): Promise<void> {
    if (this.isDirty) {
      await this.savePositions();
    }
  }

  async reload(): Promise<void> {
    if (this.loadPromise) {
      await this.loadPromise;
      this.loadPromise = null;
    } else {
      await this.loadPositions();
    }
  }
}

export const positionManager = new PositionManager();

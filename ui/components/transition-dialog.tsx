import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { FlowState, getPhaseState, PhaseType, StateType } from "@/lib/types";
import { getNodeConfig } from "@/lib/utils";
import React from "react";

export function TransitionDialog({
  showTransitionDialog,
  setShowTransitionDialog,
  selectedNodeForTransition,
  handleConfirmTransition,
  handleCancelTransition,
}: {
  showTransitionDialog: boolean;
  setShowTransitionDialog: (show: boolean) => void;
  selectedNodeForTransition: FlowState | null;
  handleConfirmTransition: () => void;
  handleCancelTransition: () => void;
}) {
  return (
    <Dialog open={showTransitionDialog} onOpenChange={setShowTransitionDialog}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm State Transition</DialogTitle>
          <DialogDescription>
            Are you sure you want to transition to{" "}
            <strong>
              {selectedNodeForTransition
                ? getNodeConfig(selectedNodeForTransition)?.label ||
                  selectedNodeForTransition
                : "Unknown state"}
            </strong>
            ?
          </DialogDescription>
          {selectedNodeForTransition &&
            (() => {
              const targetPhaseState = getPhaseState(selectedNodeForTransition);
              if (targetPhaseState) {
                return (
                  <div className="mt-2 text-sm text-gray-600">
                    Phase: {PhaseType[targetPhaseState.phase]}, State:{" "}
                    {StateType[targetPhaseState.state]}
                  </div>
                );
              }
              return null;
            })()}
        </DialogHeader>
        <DialogFooter>
          <button
            className="rounded bg-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-400"
            onClick={handleCancelTransition}
          >
            Cancel
          </button>
          <button
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            onClick={handleConfirmTransition}
          >
            Confirm Transition
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

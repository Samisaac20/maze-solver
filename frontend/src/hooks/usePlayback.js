import { useEffect } from 'react';

export const usePlayback = (isRunning, historyLength, speedMs, setState) => {
  useEffect(() => {
    if (!isRunning || !historyLength) return;

    let frameId;
    let lastTime = performance.now();
    const stepDur = Math.max(20, Math.min(1000, speedMs));

    const tick = (time) => {
      const delta = time - lastTime;
      lastTime = time;

      setState(s => {
        const nextProgress = s.frameProgress + delta / stepDur;
        if (nextProgress >= 1) {
          const nextStep = s.currentStep + 1;
          if (nextStep >= s.history.length) {
            return { ...s, isRunning: false };
          }
          return { ...s, currentStep: nextStep, frameProgress: nextProgress - 1 };
        }
        return { ...s, frameProgress: nextProgress };
      });

      frameId = requestAnimationFrame(tick);
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [isRunning, historyLength, speedMs, setState]);
};

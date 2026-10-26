/*
 The web app's helper that works in the background (a "Web Worker"), so the
 page never freezes while a puzzle is being solved, graded or generated.
 The page sends it a job; it sends back the answer (and progress, while
 generating). If a job runs too long, the page simply stops this worker.
*/
'use strict';
importScripts('solver.js', 'generator.js');

const MAX_STEPS = 50000;   // far more than any real 10 x 10 puzzle needs

self.onmessage = ({ data: job }) => {
  try {
    if (job.type === 'solve') {
      const solver = new StarBattleSolver(job.rows, job.stars);
      const steps = [];
      for (const step of solver.solveSteps()) {
        steps.push(step);
        if (steps.length > MAX_STEPS) throw new Error('This puzzle needs too many steps to show.');
      }
      self.postMessage({ type: 'solved', steps, guesses: solver.guesses, backtracks: solver.backtracks });
    } else if (job.type === 'grade') {
      self.postMessage({ type: 'graded', grade: gradePuzzle(job.rows, job.stars) });
    } else if (job.type === 'generate') {
      const result = generateWithDifficulty(job.difficulty, {
        stars: job.stars,
        onTry: tries => self.postMessage({ type: 'progress', tries }),
      });
      self.postMessage({ type: 'generated', rows: result.rows, grade: result.grade, tries: result.tries });
    }
  } catch (err) {
    self.postMessage({ type: 'error', message: err.message });
  }
};

// Pause the previous comparison when another sample starts playing.
document.addEventListener('play', (event) => {
  if (!(event.target instanceof HTMLAudioElement)) return;
  document.querySelectorAll('audio').forEach((audio) => {
    if (audio !== event.target) audio.pause();
  });
}, true);

// Closing a baseline comparison should stop any hidden audio.
document.querySelectorAll('.baseline-comparisons').forEach((comparison) => {
  comparison.addEventListener('toggle', () => {
    if (!comparison.open) comparison.querySelectorAll('audio').forEach((audio) => audio.pause());
  });
});

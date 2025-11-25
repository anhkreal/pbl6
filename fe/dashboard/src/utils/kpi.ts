export function computeAttendanceScore(actualHours: number, expectedHours: number){
  const ratio = Math.max(0, Math.min(1, actualHours / expectedHours));
  return +(ratio * 60).toFixed(2);
}
export function computeEmotionScore(positiveFrames: number, totalFrames: number){
  const ratio = totalFrames>0 ? positiveFrames/totalFrames : 0;
  return +(ratio * 40).toFixed(2);
}
export function computeTotal(att: number, emo: number){
  return +(att + emo).toFixed(2);
}

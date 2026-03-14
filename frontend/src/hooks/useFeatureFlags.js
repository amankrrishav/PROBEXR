/**
 * Feature flags — gate coming-soon surfaces without touching JSX.
 * Toggle flags here to enable/disable features globally.
 */

const FEATURES = {
  emailEditing: false,
  tts: false,
};

export function useFeatureFlags() {
  return FEATURES;
}

export { FEATURES };

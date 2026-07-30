import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'ai.stromex.app',
  appName: 'StromeX',
  webDir: 'out',
  server: {
    androidScheme: 'https',
  },
};

export default config;

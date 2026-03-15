export const colors = {
  light: {
    background: '#F8FAFC',
    surface: '#FFFFFF',
    primary: '#0F766E',
    primaryForeground: '#FFFFFF',
    secondary: '#CCFBF1',
    secondaryForeground: '#0F766E',
    accent: '#F43F5E',
    textMain: '#0F172A',
    textMuted: '#64748B',
    border: '#E2E8F0',
    success: '#10B981',
    warning: '#F59E0B',
    aiActive: '#8B5CF6',
    aiPulse: 'rgba(139, 92, 246, 0.5)',
    overlay: 'rgba(15, 23, 42, 0.6)',
  },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
};

export const radius = {
  sm: 6,
  md: 12,
  lg: 16,
  full: 9999,
};

export const fonts = {
  h1: { fontSize: 32, fontWeight: '700' as const, lineHeight: 40 },
  h2: { fontSize: 24, fontWeight: '600' as const, lineHeight: 32 },
  h3: { fontSize: 20, fontWeight: '600' as const, lineHeight: 28 },
  bodyLg: { fontSize: 18, fontWeight: '400' as const, lineHeight: 28 },
  bodyMd: { fontSize: 16, fontWeight: '400' as const, lineHeight: 24 },
  bodySm: { fontSize: 14, fontWeight: '400' as const, lineHeight: 20 },
  caption: { fontSize: 12, fontWeight: '500' as const, lineHeight: 16, textTransform: 'uppercase' as const },
};
